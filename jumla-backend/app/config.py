"""
app/config.py
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # =========================
    # Application
    # =========================
    APP_NAME: str = "Jumla-bot Backend"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # =========================
    # Server
    # =========================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # =========================
    # Database
    # =========================
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # =========================
    # Redis / Celery
    # =========================
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # =========================
    # JWT Authentication
    # =========================
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # =========================
    # Organization Settings
    # =========================
    # Default organization for public lead creation (forms, chat widget)
    # This is the organization_id that public/unauthenticated leads will be assigned to
    # Get this from your database after creating your first organization/user
    DEFAULT_ORGANIZATION_ID: Optional[str] = None

    # =========================
    # CORS
    # =========================
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # =========================
    # S3 / MinIO Storage
    # =========================
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str = "jumla-bot"
    S3_REGION: str = "us-east-1"

    # =========================
    # LLM Configuration 
    # =========================
    
    # Provider Priority (comma-separated: openai,anthropic,gemini)
    LLM_PROVIDER_PRIORITY: str = "openai,anthropic,gemini"
    LLM_FALLBACK_PROVIDER: Optional[str] = "gemini"
    LLM_PRIMARY_PROVIDER: str = "gemini"  # openai | anthropic | gemini
    
    # LLM Models (can override defaults)
    LLM_MODEL_OPENAI: str = "gpt-4o-mini"
    LLM_MODEL_ANTHROPIC: str = "claude-3-5-sonnet-20241022"
    LLM_MODEL_GEMINI: str = "gemini-2.5-pro"
    
    # API Keys 
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    # LLM Behavior
    LLM_TIMEOUT_SECONDS: int = 30  
    LLM_MAX_RETRIES: int = 3  
    LLM_RATE_LIMIT_RPM: int = 60
    LLM_CACHE_TTL_SECONDS: int = 300
    LLM_MAX_TOKENS: int = 2000
    LLM_TEMPERATURE: float = 0.1
    
    # Circuit Breaker
    LLM_CIRCUIT_BREAKER_THRESHOLD: int = 5
    LLM_CIRCUIT_BREAKER_TIMEOUT: int = 60
    
    # Feature Flags
    ENABLE_AI_EXTRACTION: bool = True
    ENABLE_AI_RESPONSE: bool = True
    ENABLE_AI_SUMMARIZATION: bool = True
    ENABLE_LLM_CACHING: bool = True
    
    # PII Protection
    REDACT_PII_IN_LOGS: bool = True

    # =========================
    # Twilio
    # =========================
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    TWILIO_WEBHOOK_SECRET: Optional[str] = None

    # =========================
    # SendGrid
    # =========================
    SENDGRID_API_KEY: str
    SENDGRID_FROM_EMAIL: str
    SENDGRID_FROM_NAME: str = "Jumla-bot"

    # =========================
    # External Enrichment APIs
    # =========================
    ATTOM_API_KEY: Optional[str] = None
    PROPSTREAM_API_KEY: Optional[str] = None
    REALTOR_API_KEY: Optional[str] = None

    # =========================
    # Business Rules
    # =========================
    MIN_OFFER_AMOUNT: float = 10000.0
    MAX_OFFER_AMOUNT: float = 5_000_000.0
    OFFER_MARGIN_PERCENT: float = 0.70
    HOT_LEAD_SCORE_THRESHOLD: float = 80.0
    WARM_LEAD_SCORE_THRESHOLD: float = 50.0

    # =========================
    # Rate Limiting
    # =========================
    RATE_LIMIT_PER_MINUTE: int = 60

    # =========================
    # Monitoring / Logging
    # =========================
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"

    # =========================
    # Pydantic Settings Config
    # =========================
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env.backend",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore unused env vars safely
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance (singleton-style)."""
    return Settings()


settings = get_settings()