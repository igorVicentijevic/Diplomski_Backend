"""Dopunjuje stvarne LLM analize tona kako bi ocenjivacki skup imao
dovoljno primera svake klase.

Pokretanje:
    TONE_ANALYSIS_PROVIDER=groq python -m experiments.tone_eval.backfill_model_analyses --limit 400
"""

import argparse
import asyncio
import time

from sqlalchemy.ext.asyncio import create_async_engine

from app.config.Settings import get_settings
from app.tone_analysis.factories.ToneAnalysisStrategyFactory import (
    ToneAnalysisStrategyFactory,
)
from app.tone_analysis.services.ToneAnalysisInputHasher import (
    ToneAnalysisInputHasher,
)
from experiments.tone_eval.repositories.ToneEvaluationRepository import (
    ToneEvaluationRepository,
)
from experiments.tone_eval.services.ToneBackfillService import (
    ToneBackfillService,
)


async def main(limit: int, concurrency: int) -> None:
    settings = get_settings()
    configured = ToneAnalysisStrategyFactory.create(settings)
    if configured.provider != "groq":
        raise SystemExit(
            "Postavi TONE_ANALYSIS_PROVIDER=groq pre pokretanja."
        )

    engine = create_async_engine(settings.database_url)
    async with engine.begin() as connection:
        repository = ToneEvaluationRepository(connection)
        pending = await repository.fetch_unanalysed_by_provider(
            provider=configured.provider,
            model_name=configured.model_name,
            prompt_version=configured.prompt_version,
            limit=limit,
        )
        print(f"clanaka bez analize: {len(pending)}")
        if not pending:
            await engine.dispose()
            return

        service = ToneBackfillService(
            connection=connection,
            configured=configured,
            hasher=ToneAnalysisInputHasher(),
            concurrency=concurrency,
        )
        started = time.perf_counter()
        stored, failed = await service.run(pending)
        elapsed = time.perf_counter() - started
        print(
            f"upisano: {stored}, neuspelo: {failed}, "
            f"trajanje: {elapsed:.1f} s ({elapsed / max(stored, 1):.2f} s/clanak)"
        )
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=400)
    parser.add_argument("--concurrency", type=int, default=4)
    arguments = parser.parse_args()
    asyncio.run(main(arguments.limit, arguments.concurrency))
