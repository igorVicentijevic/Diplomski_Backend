from datetime import datetime
from typing import Any

from .models.ArticlePair import ArticlePair
from .models.EvaluationArticle import (
    EvaluationArticle,
)


class ArticlePairJsonCodec:
    def decode(self, payload: object) -> ArticlePair:
        if not isinstance(payload, dict):
            raise TypeError("Article pair must be a JSON object.")

        same_event = payload["sameEvent"]
        if same_event is not None and not isinstance(same_event, bool):
            raise TypeError("sameEvent must be a boolean or null.")

        return ArticlePair(
            pair_id=str(payload["id"]),
            left=self._decode_article(payload["left"]),
            right=self._decode_article(payload["right"]),
            same_event=same_event,
        )

    def encode(
        self,
        pair: ArticlePair,
        candidate_type: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": pair.pair_id,
            "left": self._encode_article(pair.left),
            "right": self._encode_article(pair.right),
            "sameEvent": pair.same_event,
        }
        if candidate_type is not None:
            payload["candidateType"] = candidate_type
        return payload

    @staticmethod
    def _decode_article(payload: object) -> EvaluationArticle:
        if not isinstance(payload, dict):
            raise TypeError("Article must be a JSON object.")

        published_at = datetime.fromisoformat(
            str(payload["publishedAt"])
        )
        if published_at.tzinfo is None:
            raise ValueError("publishedAt must include a timezone.")

        return EvaluationArticle(
            article_id=str(payload["articleId"]),
            title=str(payload["title"]),
            summary=str(payload["summary"]),
            source=str(payload["source"]),
            published_at=published_at,
        )

    @staticmethod
    def _encode_article(
        article: EvaluationArticle,
    ) -> dict[str, str]:
        return {
            "articleId": article.article_id,
            "title": article.title,
            "summary": article.summary,
            "source": article.source,
            "publishedAt": article.published_at.isoformat(),
        }
