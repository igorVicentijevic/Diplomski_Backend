import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.news_sources.models.NewsArticle import NewsArticle
from app.tone_analysis.models.ConfiguredToneAnalysisStrategy import (
    ConfiguredToneAnalysisStrategy,
)
from app.tone_analysis.services.ToneAnalysisInputHasher import (
    ToneAnalysisInputHasher,
)


class ToneBackfillService:
    """Runs the configured tone strategy over articles that lack an analysis."""

    def __init__(
        self,
        connection: AsyncConnection,
        configured: ConfiguredToneAnalysisStrategy,
        hasher: ToneAnalysisInputHasher,
        concurrency: int = 4,
    ) -> None:
        self._connection = connection
        self._configured = configured
        self._hasher = hasher
        self._semaphore = asyncio.Semaphore(concurrency)

    async def run(
        self,
        articles: list[tuple[str, NewsArticle]],
    ) -> tuple[int, int]:
        results = await asyncio.gather(
            *(self._analyse(article_id, article) for article_id, article in articles)
        )
        stored = 0
        for payload in results:
            if payload is None:
                continue
            await self._store(payload)
            stored += 1
        return stored, len(articles) - stored

    async def _analyse(
        self,
        article_id: str,
        article: NewsArticle,
    ) -> dict | None:
        async with self._semaphore:
            try:
                result = await self._configured.strategy.analyze(article)
            except Exception as error:  # noqa: BLE001 - experiment script
                print(f"  preskocen {article_id}: {type(error).__name__}")
                return None
        return {
            "article_id": article_id,
            "negative": result.negative_percentage,
            "positive": result.positive_percentage,
            "neutral": result.neutral_percentage,
            "input_hash": self._hasher.calculate(article),
            "provider": self._configured.provider,
            "model_name": self._configured.model_name,
            "prompt_version": self._configured.prompt_version,
        }

    async def _store(self, payload: dict) -> None:
        statement = text(
            """
            INSERT INTO article_tone_analyses (
                article_id, negative_percentage, positive_percentage,
                neutral_percentage, input_hash, provider, model_name,
                prompt_version
            ) VALUES (
                :article_id, :negative, :positive, :neutral,
                :input_hash, :provider, :model_name, :prompt_version
            )
            ON CONFLICT (article_id) DO UPDATE SET
                negative_percentage = EXCLUDED.negative_percentage,
                positive_percentage = EXCLUDED.positive_percentage,
                neutral_percentage = EXCLUDED.neutral_percentage,
                input_hash = EXCLUDED.input_hash,
                provider = EXCLUDED.provider,
                model_name = EXCLUDED.model_name,
                prompt_version = EXCLUDED.prompt_version
            """
        )
        await self._connection.execute(statement, payload)
