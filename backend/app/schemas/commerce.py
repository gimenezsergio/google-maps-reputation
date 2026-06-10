from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CommerceBase(BaseModel):
    name: str
    slug: str
    logo_url: Optional[str] = None
    google_place_id: str
    tags: List[str] = []
    is_active: bool = True


class CommerceCreate(CommerceBase):
    pass


class CommerceUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    logo_url: Optional[str] = None
    google_place_id: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class CommerceOut(CommerceBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommercePublic(BaseModel):
    name: str
    logo_url: Optional[str] = None
    google_place_id: str
    tags: List[str]

    model_config = ConfigDict(from_attributes=True)


class CommerceAdminCreate(BaseModel):
    name: str
    slug: str
    logo_url: Optional[str] = None
    google_place_id: str
    tags: List[str] = []
    admin_username: str
    admin_password: str


class MapsUrlParseRequest(BaseModel):
    url: str


class MapsUrlParseResponse(BaseModel):
    name: str
    place_id: Optional[str] = None
    google_place_id: Optional[str] = None


class MapsSearchResponse(BaseModel):
    name: str
    address: str
    google_place_id: str


