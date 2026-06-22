from __future__ import annotations
"""Task 15b: Assessment listing and detail endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from server.db import get_db
from server.auth import get_current_user
from server.models.user import User
from server.models.assessment import Assessment

router = APIRouter(prefix="/analysis/assessments", tags=["assessments"])

TAG_LABELS = {
    "serve": "发球训练",
    "forehand_topspin": "正手训练", "forehand_flat": "正手训练", "forehand_slice": "正手训练",
    "backhand_topspin": "反手训练", "backhand_flat": "反手训练", "backhand_slice": "反手训练",
    "volley": "截击训练",
}


def auto_tag(technique_breakdown: dict | None) -> str:
    """Auto-tag an assessment based on which stroke types were detected."""
    if not technique_breakdown:
        return "综合训练"
    detected = set()
    for shot, info in technique_breakdown.items():
        if isinstance(info, dict) and info.get("score") is not None:
            main_type = shot.split("_")[0]  # forehand, backhand, serve, volley
            detected.add(main_type)
    if len(detected) == 0:
        return "综合训练"
    if len(detected) == 1:
        t = detected.pop()
        return TAG_LABELS.get(t, f"{t}训练")
    if len(detected) >= 3:
        return "综合训练"
    # 2 types → combine
    labels = [TAG_LABELS.get(t, t) for t in sorted(detected)]
    return f"{labels[0]}+{labels[1]}"


@router.get("")
async def list_assessments(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Assessment).where(Assessment.user_id == user.id, Assessment.status == "completed").order_by(Assessment.created_at.desc()).limit(20))
    assessments = result.scalars().all()
    return [{
        "assessment_id": str(a.id), "overall_ntrp": a.overall_ntrp, "ntrp_confidence": a.ntrp_confidence,
        "strengths": a.strengths, "weaknesses": a.weaknesses,
        "tag": auto_tag(a.technique_breakdown),
        "created_at": a.created_at.isoformat() if a.created_at else None
    } for a in assessments]


@router.get("/aggregate")
async def aggregate_scores(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Assessment).where(Assessment.user_id == user.id, Assessment.status == "completed").order_by(Assessment.created_at.desc()).limit(50)
    )
    assessments = result.scalars().all()
    if not assessments:
        return {"overall_ntrp": None, "shot_scores": {}, "total_assessments": 0, "trend": "no_data", "strengths": [], "weaknesses": []}

    shots = ["forehand_topspin","forehand_flat","forehand_slice","backhand_topspin","backhand_flat","backhand_slice","serve","volley"]
    best = {}; latest = {}
    for shot in shots:
        all_s = []; cur = None
        for a in assessments:
            s = ((a.technique_breakdown or {}).get(shot) or {}).get("score")
            if s is not None: all_s.append(s)
            if s is not None and cur is None: cur = s
        best[shot] = max(all_s) if all_s else None
        latest[shot] = cur

    valid = [v for v in latest.values() if v is not None]
    overall = None
    if valid:
        avg = sum(valid) / len(valid)
        overall = round(avg / 5) * 0.5
        overall = max(1.0, min(overall, 7.0))

    trend = "stable"
    if len(assessments) >= 2:
        a0 = assessments[0].overall_ntrp; a1 = assessments[-1].overall_ntrp
        if a0 and a1:
            d = a0 - a1
            trend = "up" if d > 0.1 else ("down" if d < -0.1 else "stable")

    a0 = assessments[0]
    return {
        "overall_ntrp": overall, "ntrp_confidence": a0.ntrp_confidence,
        "shot_scores": {s: {"best": best[s], "latest": latest[s]} for s in shots},
        "total_assessments": len(assessments), "trend": trend,
        "strengths": a0.strengths or [], "weaknesses": a0.weaknesses or [],
        "latest_assessment_id": str(a0.id) if a0.id else None,
        "latest_report_markdown": a0.report_markdown or "",
    }


@router.get("/{assessment_id}")
async def get_assessment(assessment_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id, Assessment.user_id == user.id))
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="评估报告不存在")
    return {"assessment_id": str(a.id), "overall_ntrp": a.overall_ntrp, "ntrp_confidence": a.ntrp_confidence, "technique_breakdown": a.technique_breakdown, "fitness_breakdown": a.fitness_breakdown, "strengths": a.strengths, "weaknesses": a.weaknesses, "key_frames": a.key_frames, "report_markdown": a.report_markdown, "tag": auto_tag(a.technique_breakdown), "created_at": a.created_at.isoformat() if a.created_at else None}


@router.delete("/{assessment_id}")
async def delete_assessment(assessment_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id, Assessment.user_id == user.id))
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="评估报告不存在")
    await db.execute(delete(Assessment).where(Assessment.id == assessment_id))
    await db.commit()
    return {"deleted": assessment_id, "status": "ok"}


@router.get("/{assessment_id}/download", response_class=PlainTextResponse)
async def download_assessment(assessment_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id, Assessment.user_id == user.id))
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="评估报告不存在")
    md = a.report_markdown or "暂无报告内容"
    return PlainTextResponse(content=md, media_type="text/markdown", headers={
        "Content-Disposition": f'attachment; filename="assessment-{assessment_id[:8]}.md"'
    })
