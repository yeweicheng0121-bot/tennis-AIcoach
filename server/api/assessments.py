from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server.db import get_db
from server.auth import get_current_user
from server.models.user import User
from server.models.assessment import Assessment

router = APIRouter(prefix="/analysis/assessments", tags=["assessments"])


@router.get("")
async def list_assessments(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assessment)
        .where(Assessment.user_id == user.id, Assessment.status == "completed")
        .order_by(Assessment.created_at.desc())
        .limit(20)
    )
    assessments = result.scalars().all()
    return [
        {
            "assessment_id": str(a.id),
            "overall_ntrp": a.overall_ntrp,
            "ntrp_confidence": a.ntrp_confidence,
            "strengths": a.strengths,
            "weaknesses": a.weaknesses,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in assessments
    ]


@router.get("/{assessment_id}")
async def get_assessment(
    assessment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assessment).where(
            Assessment.id == assessment_id,
            Assessment.user_id == user.id,
        )
    )
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="评估报告不存在")
    return {
        "assessment_id": str(a.id),
        "overall_ntrp": a.overall_ntrp,
        "ntrp_confidence": a.ntrp_confidence,
        "technique_breakdown": a.technique_breakdown,
        "fitness_breakdown": a.fitness_breakdown,
        "strengths": a.strengths,
        "weaknesses": a.weaknesses,
        "key_frames": a.key_frames,
        "report_markdown": a.report_markdown,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }
