from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class FeedbackBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    tags: Optional[list[str]] = []



class FeedbackCreate(FeedbackBase):
    commerce_id: int


class FeedbackOut(FeedbackBase):
    id: int
    commerce_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Schema specifically for incoming public feedback submissions
class PublicFeedbackCreate(FeedbackBase):
    pass


# Schema for public AI review requests
class PublicReviewRequest(BaseModel):
    commerce_id: int
    tags: list[str]
