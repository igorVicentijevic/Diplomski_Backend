from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.news_sources.models.NewsArticle import NewsArticle


@dataclass(frozen=True, slots=True)
class AnalysedArticle:
    article_id: str
    title: str
    summary: str
    source: str
    category: str
    negative: float
    positive: float
    neutral: float


class ToneEvaluationRepository:
    """Read-only access to articles and their stored tone analyses."""

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def fetch_unanalysed_by_provider(
        self,
        provider: str,
        model_name: str,
        prompt_version: str,
        limit: int,
    ) -> list[tuple[str, NewsArticle]]:
        statement = text(
            """
            SELECT a.id, a.source_id, a.source, a.title, a.summary,
                   a.category, a.published_at, a.image_url, a.article_url
            FROM articles a
            JOIN article_analyses an ON an.article_id = a.id
            LEFT JOIN article_tone_analyses t
                   ON t.article_id = a.id
                  AND t.provider = :provider
                  AND t.model_name = :model_name
                  AND t.prompt_version = :prompt_version
            WHERE t.article_id IS NULL
              AND a.summary IS NOT NULL
              AND length(trim(a.summary)) >= 40
            ORDER BY a.published_at DESC
            LIMIT :limit
            """
        )
        result = await self._connection.execute(
            statement,
            {
                "provider": provider,
                "model_name": model_name,
                "prompt_version": prompt_version,
                "limit": limit,
            },
        )
        return [
            (
                row.id,
                NewsArticle(
                    source_id=row.source_id,
                    source_name=row.source,
                    title=row.title,
                    summary=row.summary,
                    category=row.category,
                    published_at=row.published_at,
                    image_url=row.image_url,
                    article_url=row.article_url,
                ),
            )
            for row in result
        ]

    async def fetch_analysed(
        self,
        provider: str,
        model_name: str,
        prompt_version: str,
    ) -> list[AnalysedArticle]:
        statement = text(
            """
            SELECT a.id, a.title, a.summary, a.source, a.category,
                   t.negative_percentage, t.positive_percentage,
                   t.neutral_percentage
            FROM articles a
            JOIN article_tone_analyses t ON t.article_id = a.id
            WHERE t.provider = :provider
              AND t.model_name = :model_name
              AND t.prompt_version = :prompt_version
              AND length(trim(a.summary)) >= 40
            """
        )
        result = await self._connection.execute(
            statement,
            {
                "provider": provider,
                "model_name": model_name,
                "prompt_version": prompt_version,
            },
        )
        return [
            AnalysedArticle(
                article_id=row.id,
                title=row.title,
                summary=row.summary,
                source=row.source,
                category=row.category,
                negative=row.negative_percentage,
                positive=row.positive_percentage,
                neutral=row.neutral_percentage,
            )
            for row in result
        ]
