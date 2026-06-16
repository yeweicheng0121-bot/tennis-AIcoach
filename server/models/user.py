import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, Text, ARRAY, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from server.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    wechat_union_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    nickname: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    birth_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    playing_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    self_rated_ntrp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_ntrp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    handedness: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    injury_history: Mapped[Optional[list]] = mapped_column(ARRAY(Text), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
