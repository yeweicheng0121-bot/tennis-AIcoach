"""Task 15a: Analysis API — task start, status, WebSocket progress + screenshot."""
import asyncio
import base64
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from server.db import get_db
from server.auth import get_current_user
from server.models.user import User
from server.models.health import HealthWorkout
from server.worker.analyze import analyze_tennis_session
from server.worker.oppo import compute_fitness_breakdown
from server.config import settings

router = APIRouter(prefix="/analysis", tags=["analysis"])


class StartAnalysisRequest(BaseModel):
    video_id: str
    health_workout_id: Optional[str] = None


@router.post("/start")
async def start_analysis(req: StartAnalysisRequest, user: User = Depends(get_current_user)):
    task = analyze_tennis_session.delay(video_id=req.video_id, health_workout_id=req.health_workout_id, user_id=str(user.id))
    return {"task_id": task.id, "status": "queued", "estimated_duration_seconds": 240}


@router.post("/screenshot")
async def upload_screenshot(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload an OPPO Watch tennis mode screenshot. Claude extracts the stats, returns structured data + creates a HealthWorkout."""
    if not file.content_type or not file.content_type.startswith("image/"):
        return {"error": "仅支持图片文件", "extracted_stats": None}

    # Save screenshot temporarily
    os.makedirs(settings.frame_storage_path, exist_ok=True)
    tmp_path = os.path.join(settings.frame_storage_path, f"screenshot_{uuid.uuid4().hex}.jpg")
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    # Extract stats via Claude
    from server.worker.claude import extract_screenshot_stats
    stats = extract_screenshot_stats(tmp_path)

    # Clean up
    os.remove(tmp_path)

    if not stats:
        return {"workout_id": None, "extracted_stats": None, "message": "无法从截图中提取数据"}

    # Create a HealthWorkout record from extracted stats
    fitness = compute_fitness_breakdown(stats, user.birth_year)
    workout = HealthWorkout(
        user_id=user.id, workout_type="tennis",
        total_shots=stats.get("total_shots"), serve_count=stats.get("serve_count"),
        forehand_topspin=stats.get("forehand_topspin"), forehand_slice=stats.get("forehand_slice"),
        backhand_topspin=stats.get("backhand_topspin"), backhand_slice=stats.get("backhand_slice"),
        avg_swing_speed=stats.get("avg_swing_speed"),
        avg_heart_rate=stats.get("avg_heart_rate"), max_heart_rate=stats.get("max_heart_rate"),
        total_distance=stats.get("total_distance"), total_calories=stats.get("total_calories"),
        raw_data={"source": "screenshot", "extracted": stats},
    )
    db.add(workout)
    await db.commit()
    await db.refresh(workout)

    return {
        "workout_id": str(workout.id),
        "extracted_stats": stats,
        "fitness_preview": fitness,
    }


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = analyze_tennis_session.AsyncResult(task_id)
    response = {"task_id": task_id, "status": task.state}
    if task.state == "PROCESSING" and task.info:
        response.update(task.info)
    elif task.state == "SUCCESS":
        response["result"] = task.result
    elif task.state == "FAILURE":
        response["error"] = str(task.info)
    return response


@router.websocket("/tasks/{task_id}/stream")
async def task_progress_stream(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        while True:
            task = analyze_tennis_session.AsyncResult(task_id)
            await websocket.send_json({"status": task.state, "info": task.info if task.state == "PROCESSING" else None, "result": task.result if task.state == "SUCCESS" else None})
            if task.state in ("SUCCESS", "FAILURE"):
                break
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
