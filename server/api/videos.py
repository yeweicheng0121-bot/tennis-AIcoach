from __future__ import annotations
import uuid
import os

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server.db import get_db
from server.auth import get_current_user
from server.models.user import User
from server.models.video import Video
from server.config import settings

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="仅支持视频文件")

    video_id = uuid.uuid4()
    ext = os.path.splitext(file.filename or "video.mp4")[1]
    storage_dir = os.path.join(settings.video_storage_path, str(user.id))
    os.makedirs(storage_dir, exist_ok=True)
    storage_path = os.path.join(storage_dir, f"{video_id}{ext}")

    file_size = 0
    with open(storage_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)
            file_size += len(chunk)

    video = Video(
        id=video_id,
        user_id=user.id,
        file_size_bytes=file_size,
        storage_path=storage_path,
        upload_status="uploaded",
    )
    db.add(video)
    await db.commit()

    return {"video_id": str(video_id), "status": "uploaded", "file_size_bytes": file_size}


@router.get("/{video_id}")
async def get_video(
    video_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Video).where(Video.id == video_id, Video.user_id == user.id)
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    return {
        "video_id": str(video.id),
        "duration_seconds": video.duration_seconds,
        "file_size_bytes": video.file_size_bytes,
        "upload_status": video.upload_status,
        "created_at": video.created_at.isoformat() if video.created_at else None,
    }
