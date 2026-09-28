from abc import ABC, abstractmethod

from app.tone_analysis.models.LlmToneAnalysisResponse import (
    LlmToneAnalysisResponse,
)
from app.tone_analysis.models.ToneAnalysisAvailability import (
    ToneAnalysisAvailability,
)


class IToneAnalysisLlmClient(ABC):
    @abstractmethod
    async def check_availability(self) -> ToneAnalysisAvailability:
        """Probes the provider before a batch of analyses is started."""
        ...

    @abstractmethod
    async def analyze_tone(
        self,
        *,
        title: str,
        summary: str,
    ) -> LlmToneAnalysisResponse:
        ...
