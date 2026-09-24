from dataclasses import dataclass
from datetime import datetime

from app.articles.models.ArticleToneAnalysisModel import (
    ArticleToneAnalysisModel,
)


@dataclass(frozen=True, slots=True)
class StoredToneAnalysis:
    tone: ArticleToneAnalysisModel
    processed_at: datetime
