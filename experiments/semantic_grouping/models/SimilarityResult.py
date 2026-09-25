from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimilarityResult:
    pair_id: str
    similarity: float
    same_event: bool
    candidate_type: str | None = None
