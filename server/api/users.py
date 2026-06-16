from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from server.db import get_db
from server.auth import get_current_user
from server.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


class UserProfile(BaseModel):
    id: str
    phone: str | None
    nickname: str | None
    gender: str | None
    birth_year: int | None
    playing_years: float | None
    self_rated_ntrp: float | None
    target_ntrp: float | None
    handedness: str | None
    injury_history: list[str] | None

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    nickname: str | None = None
    gender: str | None = None
    birth_year: int | None = None
    playing_years: float | None = None
    self_rated_ntrp: float | None = None
    target_ntrp: float | None = None
    handedness: str | None = None
    injury_history: list[str] | None = None


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
