from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToneAnalysisAvailability:
    """Tells whether the provider can serve analyses right now."""

    is_available: bool
    reason: str | None = None

    @classmethod
    def available(cls) -> "ToneAnalysisAvailability":
        return cls(is_available=True)

    @classmethod
    def unavailable(cls, reason: str) -> "ToneAnalysisAvailability":
        return cls(is_available=False, reason=reason)
