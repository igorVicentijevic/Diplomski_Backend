from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from typing import Literal

from pydantic import SecretStr


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+asyncpg://news:news@localhost:5432/news_aggregator"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


    groq_api_key: SecretStr | None = None
    tone_analysis_provider: Literal["random", "groq"] = "random"
    tone_analysis_model: str = "openai/gpt-oss-20b"
    tone_analysis_prompt_version: str = "v1"
    tone_analysis_timeout_seconds: float = 30
    tone_analysis_max_retries: int = 2

@lru_cache
def get_settings() -> Settings:
    return Settings()



