import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from server.db import Base


class HealthWorkout(Base):
    __tablename__ = "health_workouts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workout_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_shots: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    serve_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    forehand_topspin: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    forehand_slice: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    backhand_topspin: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    backhand_slice: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_swing_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_heart_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_heart_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_distance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_calories: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
