from dataclasses import dataclass

from app.tone_analysis.strategies.ToneAnalysisStrategy import (
    ToneAnalysisStrategy,
)


@dataclass(frozen=True, slots=True)
class ConfiguredToneAnalysisStrategy:
    strategy: ToneAnalysisStrategy
    provider: str
    model_name: str
    prompt_version: str
