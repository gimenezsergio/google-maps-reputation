import os
from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Google Maps Reputation Manager"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./reputation.db"

    # JWT Security Configuration
    SECRET_KEY: str = "local-dev-secret-key-1234567890-abcdefghijklmnop"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520  # 8 days

    # DeepSeek Configuration
    DEEPSEEK_API_KEY: str = ""

    # Google Places API Configuration
    GOOGLE_PLACES_API_KEY: str = ""

    # Super Admin Configuration
    SUPER_ADMIN_USERNAME: str = "admin"
    SUPER_ADMIN_PASSWORD: str = "admin123"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
