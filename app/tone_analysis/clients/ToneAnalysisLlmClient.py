
from typing import Protocol

from app.tone_analysis.models.LlmToneAnalysisResponse import (
    LlmToneAnalysisResponse,
)


class ToneAnalysisLlmClient(Protocol):
    async def analyze_tone(
        self,
        *,
        title: str,
        summary: str,
    ) -> LlmToneAnalysisResponse:
        ...
