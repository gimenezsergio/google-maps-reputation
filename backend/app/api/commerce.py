from collections import Counter
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.feedback import Feedback
from app.models.user import User
from app.models.commerce import Commerce
from app.schemas.feedback import FeedbackOut
from app.schemas.commerce import CommerceOut

router = APIRouter()


@router.get("/feedbacks", response_model=List[FeedbackOut])
def read_commerce_feedbacks(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_commerce_admin)
) -> Any:
    """
    Retrieve private feedbacks (1-3 stars) for the logged-in commerce owner.
    Only accessible by Commerce Admins or Super Admins.
    """
    commerce_id = current_user.commerce_id
    if not commerce_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene un comercio asignado"
        )
        
    # Query only private contencion feedbacks (1 to 3 stars) ordered by newest
    feedbacks = db.query(Feedback).filter(
        Feedback.commerce_id == commerce_id,
        Feedback.rating <= 3
    ).order_by(Feedback.created_at.desc()).all()
    
    return feedbacks


@router.get("/stats")
def read_commerce_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_commerce_admin)
) -> Any:
    """
    Retrieve statistics and metrics for the logged-in commerce owner.
    Only accessible by Commerce Admins or Super Admins.
    """
    commerce_id = current_user.commerce_id
    if not commerce_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene un comercio asignado"
        )
        
    feedbacks = db.query(Feedback).filter(Feedback.commerce_id == commerce_id).all()
    
    total_opinions = len(feedbacks)
    
    if total_opinions > 0:
        average_rating = round(sum(f.rating for f in feedbacks) / total_opinions, 1)
    else:
        average_rating = 0.0
        
    # Calculate star distribution
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for f in feedbacks:
        if f.rating in distribution:
            distribution[f.rating] += 1
            
    private_count = sum(distribution[r] for r in [1, 2, 3])
    positive_count = sum(distribution[r] for r in [4, 5])
    
    # Calculate tag frequency
    tag_counter = Counter()
    for f in feedbacks:
        if f.tags:
            # f.tags is loaded as a python list automatically by SQLAlchemy JSON type
            if isinstance(f.tags, list):
                tag_counter.update(f.tags)
            elif isinstance(f.tags, str):
                try:
                    import json
                    parsed_tags = json.loads(f.tags)
                    if isinstance(parsed_tags, list):
                        tag_counter.update(parsed_tags)
                except Exception:
                    pass
                
    tags_frequency = [{"tag": tag, "count": count} for tag, count in tag_counter.most_common()]
    
    return {
        "total_opinions": total_opinions,
        "average_rating": average_rating,
        "distribution": distribution,
        "private_count": private_count,
        "positive_count": positive_count,
        "tags_frequency": tags_frequency
    }


@router.get("/my-commerce", response_model=CommerceOut)
def read_my_commerce(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_commerce_admin)
) -> Any:
    """
    Retrieve commerce profile details for the logged-in commerce owner.
    """
    commerce_id = current_user.commerce_id
    if not commerce_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene un comercio asignado"
        )
    commerce = db.query(Commerce).filter(Commerce.id == commerce_id).first()
    if not commerce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comercio no encontrado"
        )
    return commerce

