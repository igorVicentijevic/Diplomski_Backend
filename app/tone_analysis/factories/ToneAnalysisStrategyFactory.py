from app.config.Settings import Settings
from app.tone_analysis.clients.GroqToneAnalysisLlmClient import (
    GroqToneAnalysisLlmClient,
)
from app.tone_analysis.exceptions.ToneAnalysisConfigurationError import (
    ToneAnalysisConfigurationError,
)
from app.tone_analysis.models.ConfiguredToneAnalysisStrategy import (
    ConfiguredToneAnalysisStrategy,
)
from app.tone_analysis.strategies.LlmToneAnalysisStrategy import (
    LlmToneAnalysisStrategy,
)
from app.tone_analysis.strategies.RandomToneAnalysisStrategy import (
    RandomToneAnalysisStrategy,
)


class ToneAnalysisStrategyFactory:
    @staticmethod
    def create(
        settings: Settings,
    ) -> ConfiguredToneAnalysisStrategy:
        if settings.tone_analysis_provider == "random":
            return ConfiguredToneAnalysisStrategy(
                strategy=RandomToneAnalysisStrategy(),
                provider="random",
                model_name="random",
                prompt_version=settings.tone_analysis_prompt_version,
            )

        api_key = settings.groq_api_key
        if api_key is None or not api_key.get_secret_value().strip():
            raise ToneAnalysisConfigurationError(
                "GROQ_API_KEY must be configured when "
                "TONE_ANALYSIS_PROVIDER is 'groq'."
            )

        model_name = settings.tone_analysis_model.strip()
        if not model_name:
            raise ToneAnalysisConfigurationError(
                "TONE_ANALYSIS_MODEL must not be empty."
            )

        prompt_version = settings.tone_analysis_prompt_version.strip()
        if not prompt_version:
            raise ToneAnalysisConfigurationError(
                "TONE_ANALYSIS_PROMPT_VERSION must not be empty."
            )

        client = GroqToneAnalysisLlmClient(
            api_key=api_key.get_secret_value(),
            model=model_name,
            timeout_seconds=settings.tone_analysis_timeout_seconds,
            max_retries=settings.tone_analysis_max_retries,
        )

        return ConfiguredToneAnalysisStrategy(
            strategy=LlmToneAnalysisStrategy(client),
            provider="groq",
            model_name=model_name,
            prompt_version=prompt_version,
        )
