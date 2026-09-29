from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FitBuddy"

    database_url: str = "sqlite:///./fitbuddy.db"

    gemini_api_key: str = ""
    gemini_workout_model: str = "gemini-3.8-flash"
    gemini_tip_model: str = "gemini-3.8-flash"
    # Used when the main model stays busy (503/429) after retries.
    # Blank = no fallback.
    gemini_fallback_model: str = "gemini-3.6-flash"

    admin_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
