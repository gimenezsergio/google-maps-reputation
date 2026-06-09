from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
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
    import urllib.parse
    import re

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
    place_id = None

    # Search in URL (e.g. placeid=ChIJ... or /place/ChIJ... or hex coordinates 0x...:0x...)
    match_place_id = re.search(r'ChIJ[a-zA-Z0-9_-]{23}', resolved_url)
    match_hex_id = re.search(r'0x[0-9a-fA-F]+:0x[0-9a-fA-F]+', resolved_url)
    
    if match_place_id:
        place_id = match_place_id.group(0)
    elif match_hex_id:
        place_id = match_hex_id.group(0)
    elif html:
        # Fallback to search in HTML body
        place_ids = re.findall(r'ChIJ[a-zA-Z0-9_-]{23}', html)
        if place_ids:
            place_id = place_ids[0]
        else:
            hex_ids = re.findall(r'0x[0-9a-fA-F]+:0x[0-9a-fA-F]+', html)
            if hex_ids:
                place_id = hex_ids[0]

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

    return {
        "name": name,
        "place_id": place_id
    }


@router.get("/search-places", response_model=List[MapsSearchResponse])
def search_places_on_google(
    q: str,
    current_super_admin: User = Depends(deps.get_current_super_admin)
) -> Any:
    """
    Search for places/businesses on Google Maps without an API key.
    Only accessible by Super Admins.
    """
    import urllib.request
    import urllib.parse
    import json
    import re

    query = q.strip()
    if not query:
        return []

    url = f"https://www.google.com/search?tbm=map&authuser=0&hl=es&gl=ar&q={urllib.parse.quote(query)}"
    req = urllib.request.Request(
        url, 
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Cookie': 'CONSENT=YES+cb.20210328-17-p0.es+FX+999'
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            body = response.read().decode('utf-8', errors='ignore')
        
        if body.startswith(")]}'"):
            json_text = body[4:].strip()
        else:
            json_text = body.strip()

        data = json.loads(json_text)
        results = []
        
        def extract_listings(item):
            if isinstance(item, list):
                if len(item) >= 3 and isinstance(item[0], int) and isinstance(item[1], str) and isinstance(item[2], list):
                    sublist = item[2][0]
                    if isinstance(sublist, list) and len(sublist) >= 3:
                        hex_id = sublist[2]
                        if isinstance(hex_id, str) and re.match(r'0x[0-9a-fA-F]+:0x[0-9a-fA-F]+', hex_id):
                            parts = item[1].split(',')
                            name = parts[0].strip()
                            address = ",".join(parts[1:]).strip() if len(parts) > 1 else "Google Maps"
                            
                            if not any(r['google_place_id'] == hex_id for r in results):
                                results.append({
                                    "name": name,
                                    "address": address,
                                    "google_place_id": hex_id
                                })
                for sub in item:
                    extract_listings(sub)
                    
        extract_listings(data)
        return results
    except Exception as e:
        return []


