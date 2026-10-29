"""Application configuration settings."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "WindSight"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Elexon BMRS API Configuration
    ELEXON_API_BASE_URL: str = "https://data.elexon.co.uk/bmrs/api/v1"
    ELEXON_API_KEY: str = ""
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.vercel.app"
    ]
    
    # Cutoff Strategy
    DEFAULT_CUTOFF_RULE: str = "day_ahead_1700"
    
    # Temporal Scope Constraints
    START_DATE_LIMIT: str = "2026-01-01"
    END_DATE_LIMIT: str = "2026-01-31"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

