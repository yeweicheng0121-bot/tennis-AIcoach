from __future__ import annotations
"""Task 14b: Main analysis Celery task — full pipeline orchestration."""
import os
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from server.config import settings
from server.worker.celery_app import celery_app
from server.worker.frames import extract_keyframes
from server.worker.claude import analyze_frames_batch, generate_final_report, detect_video_modules
from server.worker.rag import retrieve_relevant_chunks, format_chunks_for_prompt
from server.worker.oppo import compute_fitness_breakdown

engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@celery_app.task(bind=True, name="analyze_tennis_session")
def analyze_tennis_session(self, video_id: str, health_workout_id: str | None, user_id: str):
    import asyncio
    try:
        return asyncio.run(_run_analysis(self, video_id, health_workout_id, user_id))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_run_analysis(self, video_id, health_workout_id, user_id))
        finally:
            loop.close()


async def _run_analysis(task, video_id: str, health_workout_id: str | None, user_id: str):
    try:
        return await _do_analysis(task, video_id, health_workout_id, user_id)
    except Exception as e:
        async with AsyncSessionLocal() as db:
            from server.models.video import Video
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if video:
                video.upload_status = "failed"
                await db.commit()
        task.update_state(state="FAILURE", meta={"error": str(e), "stage": "failed"})
        raise


async def _do_analysis(task, video_id: str, health_workout_id: str | None, user_id: str):
    async with AsyncSessionLocal() as db:
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
        frame_paths = extract_keyframes(video.storage_path, frame_dir, interval_seconds=15)

        task.update_state(state="PROCESSING", meta={"stage": "detecting_content", "progress": 0.15, "message": "Identifying technical modules..."})
        content_info = detect_video_modules(frame_paths)
        covered_modules = content_info.get("covered_modules", [])
        if not covered_modules:
            covered_modules = ["forehand", "backhand", "serve", "volley", "footwork", "return"]

        task.update_state(state="PROCESSING", meta={"stage": "analyzing_frames", "progress": 0.25, "frame_count": len(frame_paths)})

        BATCH_SIZE = 20
        batches = [frame_paths[i:i + BATCH_SIZE] for i in range(0, len(frame_paths), BATCH_SIZE)]
        frame_analyses = []
        for i, batch in enumerate(batches):
            pct = 0.25 + 0.35 * (i / len(batches))
            task.update_state(state="PROCESSING", meta={"stage": "analyzing_frames", "progress": pct, "batch": i + 1, "total_batches": len(batches)})
            frame_analyses.append(analyze_frames_batch(batch, i, len(batches)))

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

        all_text = " ".join([a["raw_response"] for a in frame_analyses])
        rough_weaknesses = []
        for label, kws in {"反手": ["反手", "backhand"], "发球": ["发球", "serve"], "脚步": ["脚步", "footwork"], "截击": ["截击", "volley"], "正手": ["正手", "forehand"], "接发": ["接发", "return"]}.items():
            if any(kw in all_text for kw in kws):
                rough_weaknesses.append(label)
        if not rough_weaknesses:
            rough_weaknesses = ["反手", "发球"]

        chunks = await retrieve_relevant_chunks(db, user_profile.get("self_rated_ntrp") or 3.0, rough_weaknesses, user_profile.get("target_ntrp"))
        rag_context = format_chunks_for_prompt(chunks)

        task.update_state(state="PROCESSING", meta={"stage": "generating_report", "progress": 0.85})

        report_result = generate_final_report(frame_analyses, oppo_stats, fitness_data, rag_context, user_profile, covered_modules)
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
