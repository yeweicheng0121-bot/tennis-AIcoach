from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from server.db import get_db
from server.auth import get_current_user
from server.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


class UserProfile(BaseModel):
    id: str
    phone: Optional[str] = None
    nickname: Optional[str] = None
    gender: Optional[str] = None
    birth_year: Optional[int] = None
    playing_years: Optional[float] = None
    self_rated_ntrp: Optional[float] = None
    target_ntrp: Optional[float] = None
    handedness: Optional[str] = None
    injury_history: Optional[list[str]] = None


class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = None
    gender: Optional[str] = None
    birth_year: Optional[int] = None
    playing_years: Optional[float] = None
    self_rated_ntrp: Optional[float] = None
    target_ntrp: Optional[float] = None
    handedness: Optional[str] = None
    injury_history: Optional[list[str]] = None


@router.get("/me", response_model=UserProfile)
async def get_me(user: User = Depends(get_current_user)):
    return UserProfile(
        id=str(user.id),
        phone=user.phone,
        nickname=user.nickname,
        gender=user.gender,
        birth_year=user.birth_year,
        playing_years=user.playing_years,
        self_rated_ntrp=user.self_rated_ntrp,
        target_ntrp=user.target_ntrp,
        handedness=user.handedness,
        injury_history=user.injury_history,
    )


@router.patch("/me", response_model=UserProfile)
async def update_me(
    req: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return UserProfile(
        id=str(user.id),
        phone=user.phone,
        nickname=user.nickname,
        gender=user.gender,
        birth_year=user.birth_year,
        playing_years=user.playing_years,
        self_rated_ntrp=user.self_rated_ntrp,
        target_ntrp=user.target_ntrp,
        handedness=user.handedness,
        injury_history=user.injury_history,
    )
