from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    secret_key: str = "change-me"
    token_expire_minutes: int = 60 * 12
    storage_dir: Path = Path("storage")
    database_url: str = "sqlite:///./app.db"
    allow_user_signup: bool = False


settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
