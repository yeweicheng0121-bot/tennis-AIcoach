import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from server.db import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    video_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=True)
    health_workout_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("health_workouts.id", ondelete="CASCADE"), nullable=True
    )
    overall_ntrp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ntrp_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    technique_breakdown: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    fitness_breakdown: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    strengths: Mapped[Optional[list]] = mapped_column(ARRAY(Text), nullable=True)
    weaknesses: Mapped[Optional[list]] = mapped_column(ARRAY(Text), nullable=True)
    key_frames: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    report_markdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="processing")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assessment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=True
    )
    duration_weeks: Mapped[int] = mapped_column(Integer, default=4)
    sessions_per_week: Mapped[int] = mapped_column(Integer, default=2)
    primary_goals: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    weekly_plans: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    home_exercises: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
