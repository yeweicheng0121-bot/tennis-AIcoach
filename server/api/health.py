from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from sqlalchemy import select

from server.db import get_db
from server.auth import get_current_user
from server.models.user import User
from server.models.health import HealthWorkout
from server.worker.oppo import parse_oppo_tennis_workout, compute_fitness_breakdown

router = APIRouter(prefix="/health", tags=["health"])


class OppoWorkoutData(BaseModel):
    raw_data: dict[str, Any]


@router.post("/workouts")
async def submit_oppo_workout(
    data: OppoWorkoutData,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    parsed = parse_oppo_tennis_workout(data.raw_data)

    workout = HealthWorkout(
        user_id=user.id,
        workout_type=parsed["workout_type"],
        start_time=parsed["start_time"],
        end_time=parsed["end_time"],
        duration_seconds=parsed["duration_seconds"],
        total_shots=parsed["total_shots"],
        serve_count=parsed["serve_count"],
        forehand_topspin=parsed["forehand_topspin"],
        forehand_slice=parsed["forehand_slice"],
        backhand_topspin=parsed["backhand_topspin"],
        backhand_slice=parsed["backhand_slice"],
        avg_swing_speed=parsed["avg_swing_speed"],
        avg_heart_rate=parsed["avg_heart_rate"],
        max_heart_rate=parsed["max_heart_rate"],
        total_distance=parsed["total_distance"],
        total_calories=parsed["total_calories"],
        raw_data=data.raw_data,
    )
    db.add(workout)
    await db.commit()
    await db.refresh(workout)

    fitness = compute_fitness_breakdown(parsed, user.birth_year)

    return {
        "workout_id": str(workout.id),
        "parsed_stats": {
            "total_shots": workout.total_shots,
            "serve_count": workout.serve_count,
            "forehand_topspin": workout.forehand_topspin,
            "backhand_topspin": workout.backhand_topspin,
        },
        "fitness_preview": fitness,
    }


@router.get("/workouts")
async def list_workouts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(HealthWorkout)
        .where(HealthWorkout.user_id == user.id)
        .order_by(HealthWorkout.start_time.desc())
        .limit(20)
    )
    workouts = result.scalars().all()
    return [
        {
            "workout_id": str(w.id),
            "start_time": w.start_time.isoformat() if w.start_time else None,
            "duration_seconds": w.duration_seconds,
            "total_shots": w.total_shots,
            "avg_heart_rate": w.avg_heart_rate,
        }
        for w in workouts
    ]


@router.get("/workouts/{workout_id}")
async def get_workout(
    workout_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(HealthWorkout).where(
            HealthWorkout.id == workout_id, HealthWorkout.user_id == user.id
        )
    )
    w = result.scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=404, detail="运动记录不存在")
    fitness = compute_fitness_breakdown(
        {
            "avg_heart_rate": w.avg_heart_rate,
            "max_heart_rate": w.max_heart_rate,
            "total_distance": w.total_distance,
            "duration_seconds": w.duration_seconds,
            "total_calories": w.total_calories,
        },
        user.birth_year,
    )
    return {
        "workout_id": str(w.id),
        "workout_type": w.workout_type,
        "start_time": w.start_time.isoformat() if w.start_time else None,
        "end_time": w.end_time.isoformat() if w.end_time else None,
        "duration_seconds": w.duration_seconds,
        "stats": {
            "total_shots": w.total_shots,
            "serve_count": w.serve_count,
            "forehand_topspin": w.forehand_topspin,
            "forehand_slice": w.forehand_slice,
            "backhand_topspin": w.backhand_topspin,
            "backhand_slice": w.backhand_slice,
            "avg_swing_speed": w.avg_swing_speed,
        },
        "fitness_breakdown": fitness,
    }
