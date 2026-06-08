from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, public, admin, commerce

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS middleware configuration (allows local testing easily)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(public.router, prefix=f"{settings.API_V1_STR}/public", tags=["public"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(commerce.router, prefix=f"{settings.API_V1_STR}/commerce", tags=["commerce"])
import os
from fastapi.staticfiles import StaticFiles

# Resolve path to frontend directory dynamically
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
frontend_dir = os.path.join(project_root, "frontend")

# Mount frontend static files at root URL
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

