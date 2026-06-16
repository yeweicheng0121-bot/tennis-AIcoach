import asyncio

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from server.auth import get_current_user
from server.models.user import User
from server.worker.analyze import analyze_tennis_session

router = APIRouter(prefix="/analysis", tags=["analysis"])


class StartAnalysisRequest(BaseModel):
    video_id: str
    health_workout_id: str | None = None


@router.post("/start")
async def start_analysis(
    req: StartAnalysisRequest,
    user: User = Depends(get_current_user),
):
    task = analyze_tennis_session.delay(
        video_id=req.video_id,
        health_workout_id=req.health_workout_id,
        user_id=str(user.id),
    )
    return {
        "task_id": task.id,
        "status": "queued",
        "estimated_duration_seconds": 240,
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
            await websocket.send_json(
                {
                    "status": task.state,
                    "info": task.info if task.state == "PROCESSING" else None,
                    "result": task.result if task.state == "SUCCESS" else None,
                }
            )
            if task.state in ("SUCCESS", "FAILURE"):
                break
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
