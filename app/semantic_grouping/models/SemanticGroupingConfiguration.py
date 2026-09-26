from dataclasses import dataclass
from datetime import timedelta

from app.vectordb.models.ArticleEmbeddingModel import (
    EMBEDDING_DIMENSIONS,
)


@dataclass(frozen=True, slots=True)
class SemanticGroupingConfiguration:
    model_name: str
    threshold: float
    boundary_min: float
    boundary_max: float
    candidate_window: timedelta
    embedding_dimensions: int = EMBEDDING_DIMENSIONS

    def __post_init__(self) -> None:
        if not self.model_name.strip():
            raise ValueError("Model name must not be empty.")
        if self.embedding_dimensions <= 0:
            raise ValueError(
                "Embedding dimensions must be greater than zero."
            )
        if not 0 <= self.threshold <= 1:
            raise ValueError("Threshold must be between zero and one.")
        if not 0 <= self.boundary_min <= self.boundary_max <= 1:
            raise ValueError(
                "Boundary values must satisfy 0 <= min <= max <= 1."
            )
        if self.candidate_window <= timedelta(0):
            raise ValueError(
                "Candidate window must be greater than zero."
            )
