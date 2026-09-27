from dataclasses import dataclass


@dataclass(slots=True)
class SemanticGroupingDecision:
    left_article_id: str
    right_article_id: str
    similarity: float
    predicted_same_event: bool
    is_boundary_candidate: bool
    proposed_group_id: str | None = None
