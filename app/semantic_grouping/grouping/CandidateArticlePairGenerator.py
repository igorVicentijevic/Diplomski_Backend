from datetime import UTC, datetime, timedelta

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.models.CandidateArticlePair import (
    CandidateArticlePair,
)


class CandidateArticlePairGenerator:
    def __init__(self, candidate_window: timedelta) -> None:
        if candidate_window <= timedelta(0):
            raise ValueError(
                "Candidate window must be greater than zero."
            )
        self._candidate_window = candidate_window

    def generate(
        self,
        articles: list[ArticleModel],
    ) -> list[CandidateArticlePair]:
        pairs: list[CandidateArticlePair] = []
        ordered_articles = sorted(
            articles,
            key=lambda article: self._as_utc(article.published_at),
        )

        for left_index, left in enumerate(ordered_articles):
            for right in ordered_articles[left_index + 1 :]:
                if self._is_outside_candidate_window(left, right):
                    break
                if left.source_id == right.source_id:
                    continue

                ordered_left, ordered_right = sorted(
                    (left, right),
                    key=lambda article: article.id,
                )
                pairs.append(
                    CandidateArticlePair(
                        left=ordered_left,
                        right=ordered_right,
                    )
                )

        return pairs

    def _is_outside_candidate_window(
        self,
        left: ArticleModel,
        right: ArticleModel,
    ) -> bool:
        return (
            self._as_utc(right.published_at)
            - self._as_utc(left.published_at)
            > self._candidate_window
        )

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
