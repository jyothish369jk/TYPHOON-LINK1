import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "TyphoonLink Disaster Response Engine"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database Configuration: SQLite local central server store
    # Note: Clearly segregated from on-device IndexedDB
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./database/typhoon_server.db")

    # Security & JWT Configuration loaded strictly from Environment Variables
    # Notice: Default string provided only for zero-config hackathon demo boots
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET",
        "typhoonlink-insecure-dev-secret-change-in-production-998124"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

    # CORS configuration for static frontend pages
    ALLOWED_ORIGINS: str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000,http://127.0.0.1:5500,null"
    )

    # Rate limiting: Note that in-memory rate limiting is a demonstration-level guard
    RATE_LIMIT_SOS_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_SOS_PER_MINUTE", "10"))

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
