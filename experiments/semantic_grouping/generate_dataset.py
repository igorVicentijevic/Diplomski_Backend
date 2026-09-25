import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database.session import AsyncSessionFactory
from .ArticlePairJsonCodec import (
    ArticlePairJsonCodec,
)
from .repositories.EvaluationArticleRepository import (
    EvaluationArticleRepository,
)
from .services.ArticlePairGenerator import (
    HARD_NEGATIVE,
    PROBABLE_SAME_EVENT,
    RANDOM_NEGATIVE,
    ArticlePairGenerator,
)

DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parent
    / "datasets"
    / "article_pairs.jsonl"
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate article-pair candidates from recent database data."
        )
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--max-hours", type=int, default=72)
    parser.add_argument("--probable-same", type=int, default=75)
    parser.add_argument("--hard-negatives", type=int, default=100)
    parser.add_argument("--random-negatives", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


async def generate_dataset(arguments: argparse.Namespace) -> None:
    if arguments.days <= 0:
        raise ValueError("--days must be greater than zero.")
    if arguments.max_hours <= 0:
        raise ValueError("--max-hours must be greater than zero.")
    if arguments.output.exists() and not arguments.force:
        raise FileExistsError(
            f"{arguments.output} already exists. Use --force to replace it."
        )

    published_until = datetime.now(UTC)
    published_from = published_until - timedelta(days=arguments.days)
    async with AsyncSessionFactory() as session:
        repository = EvaluationArticleRepository(session)
        articles = await repository.list_published_between(
            published_from,
            published_until,
        )

    generator = ArticlePairGenerator(
        max_time_difference=timedelta(
            hours=arguments.max_hours
        ),
        seed=arguments.seed,
    )
    pairs = generator.generate(
        articles,
        probable_same_event_count=arguments.probable_same,
        hard_negative_count=arguments.hard_negatives,
        random_negative_count=arguments.random_negatives,
    )
    codec = ArticlePairJsonCodec()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("w", encoding="utf-8") as dataset:
        for pair in pairs:
            payload = codec.encode(
                pair,
                candidate_type=generator.candidate_type(pair),
            )
            dataset.write(
                json.dumps(payload, ensure_ascii=False) + "\n"
            )

    counts = {
        candidate_type: sum(
            generator.candidate_type(pair) == candidate_type
            for pair in pairs
        )
        for candidate_type in (
            PROBABLE_SAME_EVENT,
            HARD_NEGATIVE,
            RANDOM_NEGATIVE,
        )
    }
    print(
        f"Loaded {len(articles)} articles and wrote {len(pairs)} "
        f"candidate pairs to {arguments.output}."
    )
    print(json.dumps(counts, indent=2))


def main() -> None:
    asyncio.run(generate_dataset(parse_arguments()))


if __name__ == "__main__":
    main()
