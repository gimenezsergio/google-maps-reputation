from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Commerce(Base):
    __tablename__ = "commerces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    logo_url = Column(String, nullable=True)
    google_place_id = Column(String, nullable=False)
    tags = Column(JSON, default=list, nullable=False)  # Stored as JSON array in DB
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="commerce", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="commerce", cascade="all, delete-orphan")
