"""Pravi stratifikovan skup za rucno oznacavanje tona.

Pokretanje:
    python -m experiments.tone_eval.build_dataset --per-class 30
"""

import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine

from app.config.Settings import get_settings
from experiments.tone_eval.repositories.ToneEvaluationRepository import (
    ToneEvaluationRepository,
)
from experiments.tone_eval.services.StratifiedSampleBuilder import (
    StratifiedSampleBuilder,
)

DATASETS = Path(__file__).parent / "datasets"
PROVIDER = "groq"


async def main(per_class: int, seed: int, model_name: str, prompt_version: str) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as connection:
        repository = ToneEvaluationRepository(connection)
        articles = await repository.fetch_analysed(
            provider=PROVIDER,
            model_name=model_name,
            prompt_version=prompt_version,
        )
    await engine.dispose()

    builder = StratifiedSampleBuilder(per_class=per_class, seed=seed)
    counts = builder.class_counts(articles)
    print("raspolozivo po klasi:", {k.value: v for k, v in counts.items()})
    items = builder.build(articles)

    DATASETS.mkdir(exist_ok=True)
    public = DATASETS / "tone_items.jsonl"
    hidden = DATASETS / "tone_model_labels.jsonl"

    with public.open("w", encoding="utf-8") as handle:
        for index, item in enumerate(items, start=1):
            handle.write(
                json.dumps(
                    {
                        "ordinal": index,
                        "item_id": item.item_id,
                        "title": item.title,
                        "summary": item.summary,
                        "source": item.source,
                        "category": item.category,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    with hidden.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(
                json.dumps(
                    {
                        "item_id": item.item_id,
                        "article_id": item.article_id,
                        "model_label": item.model_label.value,
                        "negative": item.model_negative,
                        "positive": item.model_positive,
                        "neutral": item.model_neutral,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(f"upisano {len(items)} stavki u {public.name} i {hidden.name}")
    print("korpus ukupno:", len(articles), "clanaka sa stvarnom LLM analizom")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-class", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260929)
    parser.add_argument("--model-name", default="openai/gpt-oss-20b")
    parser.add_argument("--prompt-version", default="v2")
    arguments = parser.parse_args()
    asyncio.run(
        main(
            arguments.per_class,
            arguments.seed,
            arguments.model_name,
            arguments.prompt_version,
        )
    )
