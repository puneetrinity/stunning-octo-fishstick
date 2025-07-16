from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    app_name: str = Field(default="ChatSEO Platform", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="production", env="ENVIRONMENT")
    
    # Database
    database_url: str = Field(env="DATABASE_URL")
    database_test_url: Optional[str] = Field(env="DATABASE_TEST_URL")
    
    # Redis
    redis_url: str = Field(env="REDIS_URL")
    
    # JWT
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # API Keys
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    anthropic_api_key: str = Field(env="ANTHROPIC_API_KEY")
    google_api_key: str = Field(env="GOOGLE_API_KEY")
    
    # Email
    smtp_host: str = Field(env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: str = Field(env="SMTP_USERNAME")
    smtp_password: str = Field(env="SMTP_PASSWORD")
    
    # Stripe
    stripe_secret_key: str = Field(env="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(env="STRIPE_WEBHOOK_SECRET")
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    rate_limit_burst: int = Field(default=100, env="RATE_LIMIT_BURST")
    
    # Celery
    celery_broker_url: str = Field(env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(env="CELERY_RESULT_BACKEND")
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Create global settings instance
settings = Settings()