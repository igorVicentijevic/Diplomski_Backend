from dataclasses import dataclass

from .EvaluationArticle import (
    EvaluationArticle,
)


@dataclass(frozen=True, slots=True)
class ArticlePair:
    pair_id: str
    left: EvaluationArticle
    right: EvaluationArticle
    same_event: bool | None
    candidate_type: str | None = None
    event_id: str | None = None
