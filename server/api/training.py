from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server.db import get_db
from server.auth import get_current_user
from server.models.user import User
from server.models.assessment import TrainingPlan

router = APIRouter(prefix="/training", tags=["training"])


@router.get("/plans")
async def list_training_plans(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user.id)
        .order_by(TrainingPlan.created_at.desc())
        .limit(10)
    )
    plans = result.scalars().all()
    return [
        {
            "plan_id": str(p.id),
            "assessment_id": str(p.assessment_id) if p.assessment_id else None,
            "duration_weeks": p.duration_weeks,
            "sessions_per_week": p.sessions_per_week,
            "primary_goals": p.primary_goals,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in plans
    ]


@router.get("/plans/{plan_id}")
async def get_training_plan(
    plan_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrainingPlan).where(
            TrainingPlan.id == plan_id,
            TrainingPlan.user_id == user.id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="训练计划不存在")
    return {
        "plan_id": str(p.id),
        "assessment_id": str(p.assessment_id) if p.assessment_id else None,
        "duration_weeks": p.duration_weeks,
        "sessions_per_week": p.sessions_per_week,
        "primary_goals": p.primary_goals,
        "weekly_plans": p.weekly_plans,
        "home_exercises": p.home_exercises,
        "status": p.status,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }
