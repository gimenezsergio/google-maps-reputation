from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core.security import get_password_hash
from app.models.commerce import Commerce
from app.models.user import User, UserRole
from app.schemas.commerce import CommerceOut, CommerceAdminCreate, CommerceUpdate

router = APIRouter()


@router.post("/commerce", response_model=CommerceOut)
def create_commerce_and_admin(
    *,
    db: Session = Depends(deps.get_db),
    commerce_in: CommerceAdminCreate,
    current_super_admin: User = Depends(deps.get_current_super_admin)
) -> Any:
    """
    Create a new commerce and its associated commerce admin user.
    Only accessible by Super Admins.
    """
    # Check if slug is taken
    existing_commerce = db.query(Commerce).filter(Commerce.slug == commerce_in.slug).first()
    if existing_commerce:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El slug ya está registrado por otro comercio"
        )
    
    # Check if username is taken
    existing_user = db.query(User).filter(User.username == commerce_in.admin_username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario administrador ya está en uso"
        )
    
    # 1. Create Commerce
    db_commerce = Commerce(
        name=commerce_in.name,
        slug=commerce_in.slug,
        logo_url=commerce_in.logo_url,
        google_place_id=commerce_in.google_place_id,
        tags=commerce_in.tags,
        is_active=True
    )
    db.add(db_commerce)
    db.flush()  # Flushes to get the commerce ID
    
    # 2. Create Commerce Admin User
    hashed_password = get_password_hash(commerce_in.admin_password)
    db_user = User(
        username=commerce_in.admin_username,
        password_hash=hashed_password,
        role=UserRole.COMMERCE_ADMIN,
        commerce_id=db_commerce.id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_commerce)
    
    return db_commerce


@router.get("/commerces", response_model=List[CommerceOut])
def read_all_commerces(
    db: Session = Depends(deps.get_db),
    current_super_admin: User = Depends(deps.get_current_super_admin)
) -> Any:
    """
    Retrieve all registered commerces.
    Only accessible by Super Admins.
    """
    return db.query(Commerce).all()


@router.put("/commerce/{id}", response_model=CommerceOut)
def update_commerce(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    commerce_in: CommerceUpdate,
    current_super_admin: User = Depends(deps.get_current_super_admin)
) -> Any:
    """
    Update an existing commerce details.
    Only accessible by Super Admins.
    """
    commerce = db.query(Commerce).filter(Commerce.id == id).first()
    if not commerce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comercio no encontrado"
        )
    
    update_data = commerce_in.model_dump(exclude_unset=True)
    
    if "slug" in update_data and update_data["slug"] != commerce.slug:
        existing_commerce = db.query(Commerce).filter(Commerce.slug == update_data["slug"]).first()
        if existing_commerce:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El slug ya está registrado por otro comercio"
            )
            
    for field in update_data:
        setattr(commerce, field, update_data[field])
        
    db.add(commerce)
    db.commit()
    db.refresh(commerce)
    return commerce


@router.delete("/commerce/{id}")
def delete_commerce(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_super_admin: User = Depends(deps.get_current_super_admin)
) -> Any:
    """
    Deactivate a commerce (soft delete).
    Only accessible by Super Admins.
    """
    commerce = db.query(Commerce).filter(Commerce.id == id).first()
    if not commerce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comercio no encontrado"
        )
    
    commerce.is_active = False
    db.add(commerce)
    db.commit()
    
    return {"status": "success", "message": "Comercio desactivado correctamente"}
