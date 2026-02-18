"""
Configuración de la aplicación usando Pydantic Settings.
Lee las variables de entorno desde .env
"""
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración general de la aplicación"""
    
    # Application
    APP_NAME: str = Field(default="MarketingCQ API")
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")
    
    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    API_PREFIX: str = Field(default="/api/v1")
    
    # Database
    DATABASE_URL: str = Field(...)
    DB_ECHO: bool = Field(default=False)
    
    # Security
    SECRET_KEY: str = Field(...)
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # CORS
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"])
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parsear CORS_ORIGINS si viene como string JSON"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v
    
    # Storage
    STORAGE_TYPE: str = Field(default="local")  # local or s3
    STORAGE_LOCAL_PATH: str = Field(default="./storage/uploads")
    MAX_FILE_SIZE_MB: int = Field(default=10)
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[
            "image/jpeg",
            "image/png",
            "image/gif",
            "application/pdf",
            "image/svg+xml"
        ]
    )
    
    @field_validator("ALLOWED_FILE_TYPES", mode="before")
    @classmethod
    def parse_allowed_file_types(cls, v):
        """Parsear ALLOWED_FILE_TYPES si viene como string JSON"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str = Field(default="")
    AWS_SECRET_ACCESS_KEY: str = Field(default="")
    AWS_BUCKET_NAME: str = Field(default="")
    AWS_REGION: str = Field(default="us-east-1")
    
    # Azure AD / Microsoft Graph for Email
    AZURE_TENANT_ID: str = Field(default="")
    AZURE_CLIENT_ID: str = Field(default="")
    AZURE_CLIENT_SECRET: str = Field(default="")
    EMAIL_FROM: str = Field(default="noreply@marketingcq.com")
    FRONTEND_URL: str = Field(default="http://localhost:3000")
    
    # Weekly Summary Email Scheduler
    WEEKLY_SUMMARY_USER_IDS: list[int] = Field(default=[3, 4])
    WEEKLY_CRON_DAY: str = Field(default="mon")
    WEEKLY_CRON_HOUR: int = Field(default=8)
    WEEKLY_CRON_MINUTE: int = Field(default=0)
    WEEKLY_SUMMARY_ENABLED: bool = Field(default=True)
    
    @field_validator("WEEKLY_SUMMARY_USER_IDS", mode="before")
    @classmethod
    def parse_weekly_summary_user_ids(cls, v):
        """Parsear WEEKLY_SUMMARY_USER_IDS si viene como string JSON"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=20)
    MAX_PAGE_SIZE: int = Field(default=100)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convertir MB a bytes"""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


# Instancia global de settings
settings = Settings()
