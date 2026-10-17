import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables and .env file.
    Follows 12-factor app best practices.
    """
    APP_NAME: str = "Automated Water Quality Monitoring System"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # SQLite local database default
    DATABASE_URL: str = "sqlite:///./water_quality.db"

    # Device ingestion authentication token (Optional security)
    # If set, incoming POST /api/readings requires 'X-Device-Token: <token>'
    DEVICE_API_KEY: Optional[str] = "dev-secret-token-123"

    # Water Quality Reference Thresholds (BIS 10500:2012 / WHO Baseline)
    # pH limits: 6.5 - 8.5
    PH_MIN: float = 6.5
    PH_MAX: float = 8.5

    # Turbidity (NTU): Acceptable <= 1.0, Max Permissible <= 5.0
    TURBIDITY_WARN: float = 1.0
    TURBIDITY_MAX: float = 5.0

    # Temperature (°C)
    TEMP_MIN: float = 15.0
    TEMP_MAX: float = 35.0

    # Dissolved Oxygen (mg/L): >= 6.0 healthy, < 4.0 critical hypoxia
    DO_MIN_WARN: float = 6.0
    DO_MIN_CRITICAL: float = 4.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
