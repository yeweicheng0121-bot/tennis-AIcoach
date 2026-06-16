from typing import Optional

from sqlalchemy import String, Float, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from server.db import Base


class NtrpChunk(Base):
    __tablename__ = "ntrp_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ntrp_level: Mapped[float] = mapped_column(Float, nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
