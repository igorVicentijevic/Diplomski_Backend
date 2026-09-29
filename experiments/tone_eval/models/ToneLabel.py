from enum import Enum


class ToneLabel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

    @classmethod
    def from_percentages(
        cls,
        negative: float,
        positive: float,
        neutral: float,
    ) -> "ToneLabel":
        """Dominant tone derived from the continuous model output."""
        ranked = (
            (negative, cls.NEGATIVE),
            (positive, cls.POSITIVE),
            (neutral, cls.NEUTRAL),
        )
        return max(ranked, key=lambda item: item[0])[1]
