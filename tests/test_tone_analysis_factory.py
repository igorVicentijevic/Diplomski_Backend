import pytest

from app.config.Settings import Settings
from app.tone_analysis.exceptions.ToneAnalysisConfigurationError import (
    ToneAnalysisConfigurationError,
)
from app.tone_analysis.factories.ToneAnalysisStrategyFactory import (
    ToneAnalysisStrategyFactory,
)
from app.tone_analysis.strategies.LlmToneAnalysisStrategy import (
    LlmToneAnalysisStrategy,
)
from app.tone_analysis.strategies.RandomToneAnalysisStrategy import (
    RandomToneAnalysisStrategy,
)


def test_factory_creates_random_strategy() -> None:
    settings = Settings(
        _env_file=None,
        tone_analysis_provider="random",
        tone_analysis_prompt_version="v1",
    )

    configured = ToneAnalysisStrategyFactory.create(settings)

    assert isinstance(configured.strategy, RandomToneAnalysisStrategy)
    assert configured.provider == "random"
    assert configured.model_name == "random"
    assert configured.prompt_version == "v1"


def test_factory_creates_groq_strategy() -> None:
    settings = Settings(
        _env_file=None,
        groq_api_key="test-key",
        tone_analysis_provider="groq",
        tone_analysis_model="openai/gpt-oss-20b",
        tone_analysis_prompt_version="v2",
        tone_analysis_timeout_seconds=20,
        tone_analysis_max_retries=1,
    )

    configured = ToneAnalysisStrategyFactory.create(settings)

    assert isinstance(configured.strategy, LlmToneAnalysisStrategy)
    assert configured.provider == "groq"
    assert configured.model_name == "openai/gpt-oss-20b"
    assert configured.prompt_version == "v2"


def test_factory_requires_groq_api_key() -> None:
    settings = Settings(
        _env_file=None,
        groq_api_key=None,
        tone_analysis_provider="groq",
    )

    with pytest.raises(
        ToneAnalysisConfigurationError,
        match="GROQ_API_KEY must be configured",
    ):
        ToneAnalysisStrategyFactory.create(settings)
