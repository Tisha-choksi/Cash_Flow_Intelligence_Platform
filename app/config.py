import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = "sqlite:///./cashflow.db"
    
    # API
    API_TITLE: str = "Cash Flow Intelligence Platform"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    
    # Features
    ENABLE_AR_MODULE: bool = True
    ENABLE_VENDOR_MODULE: bool = True
    ENABLE_PROJECT_MODULE: bool = True
    ENABLE_SALES_MODULE: bool = True
    ENABLE_OTHER_INFLOWS_MODULE: bool = True
    ENABLE_OPEX_MODULE: bool = True
    
    # ML Settings
    AR_MODEL_VERSION: str = "1.0"
    VENDOR_MODEL_VERSION: str = "1.0"
    MIN_CONFIDENCE_SCORE: float = 0.4  # 40%
    
    # Forecast Settings
    FORECAST_HORIZON_DAYS: int = 90  # days into future
    FORECAST_LOOKBACK_MONTHS: int = 6  # historical data to use
    
    # Recommendation Settings
    MIN_CASH_IMPACT_FOR_RECOMMENDATION: float = 1000.0
    MIN_FEASIBILITY_SCORE: float = 0.5
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()