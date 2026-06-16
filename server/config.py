from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tennis_coach"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"
    video_storage_path: str = "./storage/videos"
    frame_storage_path: str = "./storage/frames"
    max_upload_size_mb: int = 500

    class Config:
        env_file = ".env"


settings = Settings()
