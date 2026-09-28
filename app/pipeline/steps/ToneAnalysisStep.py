import asyncio
import logging
from dataclasses import replace

from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)
from app.pipeline.IArticleTransformationStep import (
    IArticleTransformationStep,
)
from app.tone_analysis.exceptions.ToneAnalysisUnavailableError import (
    ToneAnalysisUnavailableError,
)
from app.tone_analysis.models.ToneAnalysisAvailability import (
    ToneAnalysisAvailability,
)
from app.tone_analysis.strategies.IToneAnalysisStrategy import (
    IToneAnalysisStrategy,
)

logger = logging.getLogger(__name__)


class ToneAnalysisStep(IArticleTransformationStep):
    """Analyzes tone for the articles that do not have it yet.

    Analysis is the slowest part of the ingestion pipeline because it
    calls an external model per article, so the requests are overlapped
    with a bounded concurrency instead of being awaited one by one.

    The provider is probed once before the batch starts: when it cannot
    serve analyses, for example because the quota is spent, every
    article is skipped instead of paying a failing request for each of
    them. The same happens as soon as a request inside the batch reports
    that the provider ran out of capacity.
    """

    MAX_CONCURRENCY = 8

    def __init__(
        self,
        strategy: IToneAnalysisStrategy,
        max_concurrency: int = MAX_CONCURRENCY,
    ) -> None:
        if max_concurrency <= 0:
            raise ValueError(
                "Tone analysis concurrency must be greater than zero."
            )

        self._strategy = strategy
        self._max_concurrency = max_concurrency

    async def process(
        self,
        contexts: list[ArticleProcessingContext],
    ) -> list[ArticleProcessingContext]:
        if not contexts:
            return []

        pending_count = sum(
            1
            for context in contexts
            if context.tone_analysis is None
        )
        if pending_count == 0:
            return contexts

        availability = await self._check_availability()

        if not availability.is_available:
            logger.warning(
                "Skipping tone analysis of %s article(s): %s",
                pending_count,
                availability.reason,
            )
            return contexts

        semaphore = asyncio.Semaphore(self._max_concurrency)
        
        became_unavailable = asyncio.Event()

        return list(
            await asyncio.gather(
                *(
                    self._transform_with_limit(
                        context,
                        semaphore,
                        became_unavailable,
                    )
                    for context in contexts
                )
            )
        )

    async def _check_availability(self) -> ToneAnalysisAvailability:
        try:
            return await self._strategy.check_availability()
        except Exception:
            logger.exception(
                "Could not check whether tone analysis is available."
            )
            return ToneAnalysisAvailability.unavailable(
                "The availability check itself failed."
            )

    async def _transform_with_limit(
        self,
        context: ArticleProcessingContext,
        semaphore: asyncio.Semaphore,
        became_unavailable: asyncio.Event,
    ) -> ArticleProcessingContext:
        if context.tone_analysis is not None:
            return context

        async with semaphore:
            if became_unavailable.is_set():
                return context

            try:
                return await self.transform(context)
            except ToneAnalysisUnavailableError as error:
                self._report_unavailable(became_unavailable, error)
                return context
            except Exception:
                #a failing provider must not discard a whole feed, the
                #article is simply retried on the next refresh
                logger.exception(
                    "Could not analyze the tone of article %s",
                    context.article.article_url,
                )
                return context

    @staticmethod
    def _report_unavailable(
        became_unavailable: asyncio.Event,
        error: ToneAnalysisUnavailableError,
    ) -> None:
        if became_unavailable.is_set():
            return

        became_unavailable.set()
        logger.warning(
            "Skipping tone analysis of the remaining articles: %s",
            error,
        )

    async def transform(
        self,
        context: ArticleProcessingContext,
    ) -> ArticleProcessingContext:
        if context.tone_analysis is not None:
            return context

        tone_analysis = await self._strategy.analyze(context.article)

        return replace(
            context,
            tone_analysis=tone_analysis,
        )

    async def transform(
        self,
        context: ArticleProcessingContext,
    ) -> ArticleProcessingContext:
        if context.tone_analysis is not None:
            return context

        tone_analysis = await self._strategy.analyze(context.article)

        return replace(
            context,
            tone_analysis=tone_analysis,
        )
