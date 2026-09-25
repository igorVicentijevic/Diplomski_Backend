from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    tone_analysis_prompt_version: str = "v2"
    tone_analysis_timeout_seconds: float = Field(default=30, gt=0)
    tone_analysis_max_retries: int = Field(default=2, ge=0)
    semantic_grouping_shadow_enabled: bool = True
    semantic_grouping_model: str = (
        "sentence-transformers/distiluse-base-multilingual-cased-v2"
    )
    semantic_grouping_threshold: float = Field(
        default=0.69,
        ge=0,
        le=1,
    )
    semantic_grouping_boundary_min: float = Field(
        default=0.60,
        ge=0,
        le=1,
    )
    semantic_grouping_boundary_max: float = Field(
        default=0.80,
        ge=0,
        le=1,
    )
    semantic_grouping_candidate_window_hours: int = Field(
        default=72,
        gt=0,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
