from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
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

    @field_validator("birth_year")
    @classmethod
    def check_birth_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1920 or v > 2020):
            raise ValueError("birth_year must be between 1920 and 2020")
        return v

    @field_validator("playing_years")
    @classmethod
    def check_playing_years(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("playing_years must be >= 0")
        return v

    @field_validator("self_rated_ntrp", "target_ntrp")
    @classmethod
    def check_ntrp(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 1.0 or v > 7.0):
            raise ValueError("NTRP must be between 1.0 and 7.0")
        return v

    @field_validator("gender")
    @classmethod
    def check_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("male", "female", "other"):
            raise ValueError("gender must be 'male', 'female', or 'other'")
        return v

    @field_validator("handedness")
    @classmethod
    def check_handedness(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("left", "right", "ambidextrous"):
            raise ValueError("handedness must be 'left', 'right', or 'ambidextrous'")
        return v


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
