from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.commerce import Commerce
from app.models.feedback import Feedback
from app.schemas.commerce import CommercePublic
from app.schemas.feedback import PublicFeedbackCreate
from app.services.deepseek import DeepSeekService

router = APIRouter()


@router.get("/commerce/{slug}", response_model=CommercePublic)
def read_commerce_by_slug(
    slug: str,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get active commerce public details by slug.
    """
    commerce = db.query(Commerce).filter(Commerce.slug == slug, Commerce.is_active == True).first()
    if not commerce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comercio no encontrado o inactivo"
        )
    return commerce


@router.post("/commerce/{slug}/feedback")
def create_public_feedback(
    slug: str,
    feedback_in: PublicFeedbackCreate,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Create public feedback for a specific commerce by its slug.
    """
    commerce = db.query(Commerce).filter(Commerce.slug == slug, Commerce.is_active == True).first()
    if not commerce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comercio no encontrado"
        )
    
    # Clean commentary and email for ratings >= 4 (comments and email are only meant for contencion 1-3)
    comment = feedback_in.comment
    customer_email = feedback_in.customer_email
    if feedback_in.rating >= 4:
        comment = None
        customer_email = None

    db_feedback = Feedback(
        commerce_id=commerce.id,
        rating=feedback_in.rating,
        comment=comment,
        customer_email=customer_email,
        tags=feedback_in.tags
    )
    db.add(db_feedback)
    db.commit()

    
    return {"status": "success", "message": "Feedback registrado correctamente"}


@router.post("/commerce/{slug}/generate-review")
async def generate_public_review(
    slug: str,
    tags: List[str],
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Generate reviews using DeepSeek for the business based on selected tags.
    """
    commerce = db.query(Commerce).filter(Commerce.slug == slug, Commerce.is_active == True).first()
    if not commerce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comercio no encontrado"
        )
    
    # Generate reviews asynchronously via DeepSeekService
    reviews = await DeepSeekService.generate_reviews(
        commerce_name=commerce.name,
        tags=tags
    )
    
    return {"opciones": reviews}
