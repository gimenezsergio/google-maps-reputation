from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    commerce_id = Column(Integer, ForeignKey("commerces.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 to 5 stars
    comment = Column(String, nullable=True)   # Private feedback commentary
    tags = Column(JSON, default=list, nullable=True)  # Chosen tags (optional, mainly for ratings >= 4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    commerce = relationship("Commerce", back_populates="feedbacks")

