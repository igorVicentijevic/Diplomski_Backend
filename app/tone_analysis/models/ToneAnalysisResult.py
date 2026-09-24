from dataclasses import dataclass
from math import isclose


@dataclass(frozen=True, slots=True)
class ToneAnalysisResult:
    negative_percentage: float
    positive_percentage: float
    neutral_percentage: float

    def __post_init__(self) -> None:
        percentages = (
            self.negative_percentage,
            self.positive_percentage,
            self.neutral_percentage,
        )

        if any(value < 0 or value > 100 for value in percentages):
            raise ValueError(
                "Tone percentages must be between 0 and 100."
            )

        if not isclose(sum(percentages), 100, abs_tol=0.01):
            raise ValueError("Tone percentages must add up to 100.")
