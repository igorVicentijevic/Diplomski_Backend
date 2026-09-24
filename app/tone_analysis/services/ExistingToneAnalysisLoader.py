from dataclasses import replace

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.articles.models.ArticleToneAnalysisModel import (
    ArticleToneAnalysisModel,
)
from app.articles.repositories.ArticleAnalysisRepository import (
    ArticleAnalysisRepository,
)
from app.articles.repositories.models.StoredToneAnalysis import (
    StoredToneAnalysis,
)
from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)
from app.tone_analysis.models.ToneAnalysisMetadata import (
    ToneAnalysisMetadata,
)
from app.tone_analysis.models.ToneAnalysisResult import (
    ToneAnalysisResult,
)
from app.tone_analysis.services.ToneAnalysisInputHasher import (
    ToneAnalysisInputHasher,
)


class ExistingToneAnalysisLoader:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        input_hasher: ToneAnalysisInputHasher,
        provider: str,
        model_name: str,
        prompt_version: str,
    ) -> None:
        self._session_factory = session_factory
        self._input_hasher = input_hasher
        self._provider = provider
        self._model_name = model_name
        self._prompt_version = prompt_version

    async def load_existing(
        self,
        contexts: list[ArticleProcessingContext],
    ) -> list[ArticleProcessingContext]:
        normalized_urls = [
            self._require_normalized_url(context)
            for context in contexts
        ]

        async with self._session_factory() as session:
            repository = ArticleAnalysisRepository(session)
            existing_by_url = (
                await repository.get_tone_analyses_by_normalized_urls(
                    normalized_urls
                )
            )

        return [
            self._prepare_context(
                context,
                existing_by_url.get(
                    self._require_normalized_url(context)
                ),
            )
            for context in contexts
        ]

    def _prepare_context(
        self,
        context: ArticleProcessingContext,
        existing: StoredToneAnalysis | None,
    ) -> ArticleProcessingContext:
        metadata = ToneAnalysisMetadata(
            input_hash=self._input_hasher.calculate(context.article),
            provider=self._provider,
            model_name=self._model_name,
            prompt_version=self._prompt_version,
        )
        tone_analysis = (
            self._to_result(existing.tone)
            if self._matches(existing, metadata)
            else None
        )

        return replace(
            context,
            tone_analysis=tone_analysis,
            tone_analysis_metadata=metadata,
            tone_analysis_processed_at=(
                existing.processed_at
                if tone_analysis is not None
                else None
            ),
        )

    @staticmethod
    def _matches(
        existing: StoredToneAnalysis | None,
        metadata: ToneAnalysisMetadata,
    ) -> bool:
        return (
            existing is not None
            and existing.tone.input_hash == metadata.input_hash
            and existing.tone.provider == metadata.provider
            and existing.tone.model_name == metadata.model_name
            and (
                existing.tone.prompt_version
                == metadata.prompt_version
            )
        )

    @staticmethod
    def _to_result(
        existing: ArticleToneAnalysisModel,
    ) -> ToneAnalysisResult:
        return ToneAnalysisResult(
            negative_percentage=existing.negative_percentage,
            positive_percentage=existing.positive_percentage,
            neutral_percentage=existing.neutral_percentage,
        )

    @staticmethod
    def _require_normalized_url(
        context: ArticleProcessingContext,
    ) -> str:
        if context.normalized_url is None:
            raise ValueError(
                "Article URL must be normalized before loading analysis."
            )

        return context.normalized_url
