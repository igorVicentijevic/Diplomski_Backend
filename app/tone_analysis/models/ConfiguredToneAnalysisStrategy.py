from dataclasses import dataclass

from app.tone_analysis.strategies.IToneAnalysisStrategy import (
    IToneAnalysisStrategy,
)


@dataclass(frozen=True, slots=True)
class ConfiguredToneAnalysisStrategy:
    strategy: IToneAnalysisStrategy
    provider: str
    model_name: str
    prompt_version: str
