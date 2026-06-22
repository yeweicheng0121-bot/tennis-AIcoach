from __future__ import annotations
"""Task 14b: Main analysis Celery task — full pipeline orchestration."""
import os
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from server.config import settings
from server.worker.celery_app import celery_app
from server.worker.frames import extract_all_frames
from server.worker.llm import generate_final_report
from server.worker.rag import retrieve_relevant_chunks, format_chunks_for_prompt
from server.worker.oppo import compute_fitness_breakdown

@celery_app.task(bind=True, name="analyze_tennis_session")
def analyze_tennis_session(self, video_id: str, health_workout_id: str | None, user_id: str, focus_module: str | None = None):
    """Run the analysis in a dedicated event loop. Create fresh DB engine per task to avoid asyncpg loop conflicts."""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Create engine + session INSIDE the loop so asyncpg pool is on the correct loop
        _engine = create_async_engine(settings.database_url)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
        return loop.run_until_complete(_run_analysis(self, video_id, health_workout_id, user_id, _session_factory, focus_module))
    finally:
        loop.run_until_complete(_engine.dispose())
        loop.close()


async def _run_analysis(task, video_id: str, health_workout_id: str | None, user_id: str, session_factory=None, focus_module: str | None = None):
    try:
        return await _do_analysis(task, video_id, health_workout_id, user_id, session_factory, focus_module)
    except Exception as e:
        # Mark video as failed — use a fresh sync connection to avoid loop issues
        try:
            import psycopg2
            sync_url = __import__("server.config", fromlist=["settings"]).settings.database_url
            sync_url = sync_url.replace("+asyncpg", "+psycopg2")
            conn = psycopg2.connect(sync_url)
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute("UPDATE videos SET upload_status = 'failed' WHERE id = %s", (video_id,))
            cur.close()
            conn.close()
        except Exception:
            pass
        task.update_state(state="FAILURE", meta={"error": str(e), "stage": "failed"})
        raise


async def _do_analysis(task, video_id: str, health_workout_id: str | None, user_id: str, session_factory=None, focus_module: str | None = None):
    async with session_factory() as db:
        from server.models.video import Video
        from server.models.user import User
        from server.models.health import HealthWorkout
        from server.models.assessment import Assessment, TrainingPlan

        result = await db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()
        if not video or not video.storage_path:
            return {"error": "Video not found"}

        task.update_state(state="PROCESSING", meta={"stage": "extracting_frames", "progress": 0.05})

        frame_dir = os.path.join(settings.frame_storage_path, video_id)
        import shutil
        if os.path.exists(frame_dir):
            shutil.rmtree(frame_dir)

        # ── v2.0: OpenCV + MediaPipe pipeline ──
        from server.worker.frames import extract_all_frames
        from server.worker.pose import extract_landmarks_batch
        from server.worker.biomechanics import find_key_frames, compute_angle_stats, classify_shot_types
        from server.worker.structured_report import build_structured_data

        all_frames, fps = extract_all_frames(video.storage_path, frame_dir)
        video_duration = video.duration_seconds or (len(all_frames) / fps if fps > 0 else 120)

        task.update_state(state="PROCESSING", meta={"stage": "pose_estimation", "progress": 0.15, "frame_count": len(all_frames)})
        landmarks_by_frame = extract_landmarks_batch(all_frames)

        task.update_state(state="PROCESSING", meta={"stage": "biomechanics", "progress": 0.35})
        structured_data = build_structured_data(landmarks_by_frame, all_frames, fps, video_duration, focus_module)
        covered_modules = structured_data.get("covered_modules", ["forehand", "backhand", "serve", "volley", "footwork", "return"])

        # Key frame paths for Claude (3 images only)
        key_frame_paths = [kf["frame_path"] for kf in structured_data.get("key_frames", []) if kf.get("frame_path")]
        if not key_frame_paths and all_frames:
            # Fallback: first, middle, last
            n = len(all_frames)
            key_frame_paths = [all_frames[i] for i in [0, n // 2, n - 1] if i < n]

        oppo_stats = {}
        fitness_data = {}
        if health_workout_id:
            r = await db.execute(select(HealthWorkout).where(HealthWorkout.id == health_workout_id))
            workout = r.scalar_one_or_none()
            if workout:
                oppo_stats = {
                    "total_shots": workout.total_shots, "serve_count": workout.serve_count,
                    "forehand_topspin": workout.forehand_topspin, "forehand_slice": workout.forehand_slice,
                    "backhand_topspin": workout.backhand_topspin, "backhand_slice": workout.backhand_slice,
                    "avg_swing_speed": workout.avg_swing_speed,
                }
                fitness_data = compute_fitness_breakdown({
                    "avg_heart_rate": workout.avg_heart_rate, "max_heart_rate": workout.max_heart_rate,
                    "total_distance": workout.total_distance, "duration_seconds": workout.duration_seconds,
                    "total_calories": workout.total_calories,
                })

        r = await db.execute(select(User).where(User.id == user_id))
        user = r.scalar_one_or_none()
        user_profile = {
            "birth_year": user.birth_year if user else None,
            "playing_years": user.playing_years if user else None,
            "self_rated_ntrp": user.self_rated_ntrp if user else None,
            "target_ntrp": user.target_ntrp if user else None,
            "injury_history": user.injury_history if user else None,
        }

        task.update_state(state="PROCESSING", meta={"stage": "retrieving_knowledge", "progress": 0.70})

        # Extract weaknesses from biomechanics stats
        angle_stats = structured_data.get("angle_statistics", {})
        rough_weaknesses = []
        if angle_stats.get("torso_twist", {}).get("avg", 45) < 30:
            rough_weaknesses.append("正手")
        if angle_stats.get("shoulder", {}).get("avg", 90) < 70:
            rough_weaknesses.append("发球")
        if not rough_weaknesses:
            rough_weaknesses = ["反手", "发球"]

        chunks = await retrieve_relevant_chunks(db, user_profile.get("self_rated_ntrp") or 3.0, rough_weaknesses, user_profile.get("target_ntrp"))
        rag_context = format_chunks_for_prompt(chunks)

        task.update_state(state="PROCESSING", meta={"stage": "generating_report", "progress": 0.85})

        report_result = generate_final_report(structured_data, key_frame_paths, oppo_stats, fitness_data, rag_context, user_profile, covered_modules, focus_module)
        report_md = report_result["report_markdown"]
        structured = report_result["structured"]

        assessment = Assessment(
            id=uuid.uuid4(), user_id=user_id, video_id=video_id, health_workout_id=health_workout_id,
            overall_ntrp=structured.get("overall_ntrp", user_profile.get("self_rated_ntrp") or 3.0),
            ntrp_confidence=structured.get("ntrp_confidence", 0.7),
            technique_breakdown=structured.get("technique_breakdown", {}),
            fitness_breakdown=fitness_data,
            strengths=structured.get("strengths", []),
            weaknesses=structured.get("weaknesses", []),
            key_frames=structured.get("key_frames", []),
            report_markdown=report_md,
            status="completed",
        )
        db.add(assessment)

        plan = TrainingPlan(
            id=uuid.uuid4(), user_id=user_id, assessment_id=assessment.id,
            primary_goals={"weaknesses": structured.get("weaknesses", []), "target_ntrp": user_profile.get("target_ntrp")},
        )
        db.add(plan)
        video.upload_status = "analyzed"
        await db.commit()

        return {"assessment_id": str(assessment.id), "status": "completed", "frame_count": len(frame_paths)}
