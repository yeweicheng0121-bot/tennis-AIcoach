from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_title: str = "Tennis AI Coach"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tennis_coach"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"
    video_storage_path: str = "./storage/videos"
    frame_storage_path: str = "./storage/frames"
    max_upload_size_mb: int = 500

    model_config = {"env_file": "server/.env"}

    @field_validator("claude_api_key")
    @classmethod
    def warn_empty_api_key(cls, v: str) -> str:
        if not v.strip():
            import warnings
            warnings.warn("CLAUDE_API_KEY is empty — AI analysis will fail at runtime. Set it in .env", RuntimeWarning)
        return v


settings = Settings()
