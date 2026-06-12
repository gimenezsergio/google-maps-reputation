import httpx
import re
import time
import urllib.parse
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.commerce import Commerce
from app.models.user import User, UserRole
from app.schemas.commerce import (
    CommerceOut, 
    CommerceAdminCreate, 
    CommerceUpdate,
    MapsUrlParseRequest,
    MapsUrlParseResponse,
    MapsSearchResponse
)

router = APIRouter()

HEX_PLACE_RE = re.compile(r"0x[0-9a-fA-F]+:0x[0-9a-fA-F]+")
TEXT_PLACE_ID_RE = re.compile(r"ChIJ[a-zA-Z0-9_-]{23}")


def _extract_hex_place_ref(*values: str | None) -> str | None:
    for value in values:
        if not value:
            continue
        match = HEX_PLACE_RE.search(value)
        if match:
            return match.group(0)
    return None


def _extract_text_place_id(*values: str | None) -> str | None:
    for value in values:
        if not value:
            continue
        match = TEXT_PLACE_ID_RE.search(value)
        if match:
            return match.group(0)
    return None


def _build_write_review_uri(hex_place_ref: str) -> str:
    return f"https://www.google.com/maps/place//data=!4m3!3m2!1s{hex_place_ref}!12e1"


def _normalize_google_place_ref(value: str | None) -> str | None:
    if not value:
        return value

    normalized = value.strip()
    if not normalized:
        return normalized

    if normalized.startswith("ChIJ"):
        return normalized

    if normalized.startswith("0x") and ":0x" in normalized:
        return _build_write_review_uri(normalized)

    if normalized.startswith(("http://", "https://")):
        hex_place_ref = _extract_hex_place_ref(normalized)
        if hex_place_ref:
            return _build_write_review_uri(hex_place_ref)
        return normalized

    return normalized


def _build_places_search_payloads(query: str) -> List[dict[str, Any]]:
    normalized = " ".join(query.split())
    payloads: List[dict[str, Any]] = [
        {
            "textQuery": normalized,
            "languageCode": "es",
            "regionCode": "AR",
            "maxResultCount": 8,
        }
    ]

    lower_query = normalized.lower()
    has_location_hint = any(
        term in lower_query
        for term in ("buenos aires", "caba", "capital federal", "argentina")
    )
    if not has_location_hint:
        payloads.append(
            {
                "textQuery": f"{normalized} Buenos Aires Argentina",
                "languageCode": "es",
                "regionCode": "AR",
                "maxResultCount": 8,
            }
        )

    return payloads


def _search_google_places(query: str, api_key: str) -> list[dict[str, Any]]:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress",
    }

    last_error: httpx.RequestError | None = None
    with httpx.Client(timeout=10.0, trust_env=False) as client:
        for payload in _build_places_search_payloads(query):
            for attempt in range(3):
                try:
                    response = client.post(
                        "https://places.googleapis.com/v1/places:searchText",
                        headers=headers,
                        json=payload,
                    )
                except httpx.RequestError as exc:
                    last_error = exc
                    if attempt < 2:
                        time.sleep(0.35 * (attempt + 1))
                        continue
                    break

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Google Places API retornó error {response.status_code}: {response.text}",
                    )

                data = response.json()
                places = data.get("places", [])
                if places:
                    return places
                break

    if last_error is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de comunicación con Google Places API: {last_error}",
        )

    return []


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
        google_place_id=_normalize_google_place_ref(commerce_in.google_place_id),
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

    if "google_place_id" in update_data:
        update_data["google_place_id"] = _normalize_google_place_ref(update_data["google_place_id"])
    
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


@router.post("/parse-maps-url", response_model=MapsUrlParseResponse)
def parse_google_maps_url(
    *,
    payload: MapsUrlParseRequest,
    current_super_admin: User = Depends(deps.get_current_super_admin)
) -> Any:
    """
    Parse a Google Maps URL (or short link) to extract business name and Place ID.
    Only accessible by Super Admins.
    """
    import urllib.request

    url = payload.url.strip()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La URL no puede estar vacía"
        )

    # 1. Resolve redirect if it's a short URL (maps.app.goo.gl or goo.gl/maps)
    resolved_url = url
    html = ""
    try:
        req = urllib.request.Request(
            url, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
            }
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            resolved_url = response.geturl()
            html = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        # If fetching fails, we continue with the original URL
        pass

    # 2. Try to extract Place ID or Hex FID
    hex_place_ref = _extract_hex_place_ref(resolved_url, html, url)
    place_id = _extract_text_place_id(resolved_url, html, url)

    # 3. Extract business name
    name = "Comercio"
    
    # Try parsing from URL path /maps/place/NAME/
    match_url = re.search(r'/maps/place/([^/]+)', resolved_url)
    if match_url:
        name = urllib.parse.unquote(match_url.group(1)).replace('+', ' ')
    else:
        # Fallback: parse from HTML title
        match_title = re.search(r'<title>(.*?)</title>', html)
        if match_title:
            title_text = match_title.group(1)
            if " - Google Maps" in title_text:
                name = title_text.split(" - Google Maps")[0]
            else:
                name = title_text

    # Clean up coordinates, zoom level or extra search parameters from name
    if "@" in name:
        name = name.split("@")[0].strip()
    if "/" in name:
        name = name.split("/")[0].strip()
    
    # Clean up double spaces or trailing dashes
    name = re.sub(r'\s+', ' ', name).strip()

    # VALIDATION CHECKS (Fase 13)
    is_coords = False
    cleaned_name = name.replace(" ", "").replace("+", "").replace("-", "").replace(",", "")
    # If name consists purely of numbers/coordinates or maps internal data structure
    if not name or cleaned_name.isdigit() or re.match(r'^-?\d+(?:\.\d+)?,?-?\d+(?:\.\d+)?$', name.replace(" ", "").replace("+", "")) or name.startswith("data=") or "data=!" in name:
        is_coords = True

    # Check for generic maps titles
    is_generic_title = False
    match_title_tag = re.search(r'<title>(.*?)</title>', html)
    if match_title_tag:
        title_val = match_title_tag.group(1).strip()
        if title_val.lower() in ["google maps", "google maps - find local businesses, view maps and get driving directions in google maps."]:
            is_generic_title = True

    # If the URL resuelto points directly to coordinate data (no real business listing name)
    if "data=!4m2!3m1!1s" in resolved_url and (name == "Comercio" or is_generic_title):
        is_coords = True

    # If coordinate or name is Comercio/Google Maps, reject it
    if is_coords or name.lower() in ["", "comercio", "google maps", "googlemaps"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace ingresado corresponde a un punto en el mapa o a coordenadas geográficas, no a la ficha de un comercio. Por favor, busca el comercio en Google Maps, haz clic en Compartir y copia ese enlace."
        )

    # Prefer the canonical write-review URL when we can derive the Maps hex place ref.
    google_place_id = _normalize_google_place_ref(
        hex_place_ref or (url if url.lower().startswith(("http://", "https://")) else place_id)
    )

    return {
        "name": name,
        "place_id": hex_place_ref or place_id,
        "google_place_id": google_place_id
    }


@router.get("/search-places", response_model=List[MapsSearchResponse])
def search_places_on_google(
    q: str,
    current_super_admin: User = Depends(deps.get_current_super_admin)
) -> Any:
    """
    Search for places/businesses using Google Places API (New).
    Only accessible by Super Admins.
    """
    if not settings.GOOGLE_PLACES_API_KEY or settings.GOOGLE_PLACES_API_KEY.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La API Key de Google Places no está configurada en el servidor."
        )

    query = q.strip()
    if not query:
        return []

    try:
        places = _search_google_places(query, settings.GOOGLE_PLACES_API_KEY)

        results = []
        for place in places:
            place_id = place.get("id")
            display_name = place.get("displayName", {})
            name = display_name.get("text", "")
            address = place.get("formattedAddress", "")
            if place_id:
                results.append({
                    "name": name,
                    "address": address or "Google Maps",
                    "google_place_id": place_id
                })
        return results
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de comunicación con Google Places API: {exc}"
        )
