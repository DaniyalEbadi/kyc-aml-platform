from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    app_name: str = "پارس‌هویت"
    app_env: str = "development"
    demo_mode: bool = True
    secret_key: str = "change-me-in-production-use-a-long-random-string"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"

    database_url: str = "sqlite:///./storage/kyc.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    inline_jobs: bool = True

    storage_backend: str = "local"
    storage_local_path: str = "./storage/files"
    s3_endpoint: str = ""
    s3_bucket: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = "us-east-1"

    llm_provider: str = "mock"
    ocr_provider: str = "mock"
    vision_provider: str = "mock"
    embedding_provider: str = "mock"
    screening_provider: str = "mock"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"

    max_upload_mb: int = 12
    allowed_upload_types: str = "image/jpeg,image/png,application/pdf"
    rate_limit_per_minute: int = 120

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_types(self) -> set[str]:
        return {t.strip() for t in self.allowed_upload_types.split(",") if t.strip()}

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


settings = Settings()
