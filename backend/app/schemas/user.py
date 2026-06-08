from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.user import UserRole


# Schemas para Tokens
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None


# Schemas para Usuarios
class UserBase(BaseModel):
    username: str
    role: UserRole
    commerce_id: Optional[int] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[UserRole] = None
    commerce_id: Optional[int] = None


class UserOut(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
