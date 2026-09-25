import asyncio
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app.articles.models.ArticleModel import ArticleModel
from app.database.Base import Base
from experiments.semantic_grouping.ArticleTextBuilder import (
    ArticleTextBuilder,
)
from experiments.semantic_grouping.EmbeddingEvaluator import (
    EmbeddingEvaluator,
)
from experiments.semantic_grouping.LabelledPairLoader import (
    LabelledPairLoader,
)
from experiments.semantic_grouping.embedding_engine.EmbeddingEngine import (
    EmbeddingEngine,
)
from experiments.semantic_grouping.label_dataset import (
    load_entries,
    save_entries,
)
from experiments.semantic_grouping.models.ArticlePair import ArticlePair
from experiments.semantic_grouping.models.EvaluationArticle import (
    EvaluationArticle,
)
from experiments.semantic_grouping.repositories.EvaluationArticleRepository import (
    EvaluationArticleRepository,
)
from experiments.semantic_grouping.services.ArticlePairGenerator import (
    HARD_NEGATIVE,
    PROBABLE_SAME_EVENT,
    RANDOM_NEGATIVE,
    ArticlePairGenerator,
)

PUBLISHED_AT = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)


class FakeEmbeddingEngine(EmbeddingEngine):
    def encode(self, texts: list[str]) -> list[list[float]]:
        embeddings = {
            "Title: Left\nSummary: Same": [1.0, 0.0],
            "Title: Right\nSummary: Same": [0.9, 0.1],
            "Title: Other\nSummary: Different": [0.0, 1.0],
        }
        return [embeddings[text] for text in texts]


def create_evaluation_article(
    article_id: str,
    title: str,
    summary: str,
    source: str,
    published_at: datetime = PUBLISHED_AT,
) -> EvaluationArticle:
    return EvaluationArticle(
        article_id=article_id,
        title=title,
        summary=summary,
        source=source,
        published_at=published_at,
    )


def create_pair_payload(
    same_event: bool | None,
) -> dict[str, object]:
    return {
        "id": "pair-1",
        "left": {
            "articleId": "left-1",
            "title": "Left",
            "summary": "Same",
            "source": "RTS",
            "publishedAt": PUBLISHED_AT.isoformat(),
        },
        "right": {
            "articleId": "right-1",
            "title": "Right",
            "summary": "Same",
            "source": "N1",
            "publishedAt": PUBLISHED_AT.isoformat(),
        },
        "sameEvent": same_event,
    }


def test_labelled_pair_loader_reads_jsonl(tmp_path: Path) -> None:
    dataset_path = tmp_path / "pairs.jsonl"
    dataset_path.write_text(
        json.dumps(create_pair_payload(True)),
        encoding="utf-8",
    )

    pairs = LabelledPairLoader().load(dataset_path)

    assert pairs == [
        ArticlePair(
            pair_id="pair-1",
            left=create_evaluation_article(
                "left-1",
                "Left",
                "Same",
                "RTS",
            ),
            right=create_evaluation_article(
                "right-1",
                "Right",
                "Same",
                "N1",
            ),
            same_event=True,
        )
    ]


def test_labelled_pair_loader_rejects_unlabelled_pair(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "pairs.jsonl"
    dataset_path.write_text(
        json.dumps(create_pair_payload(None)),
        encoding="utf-8",
    )

    try:
        LabelledPairLoader().load(dataset_path)
    except ValueError as error:
        assert "Invalid dataset entry at line 1." == str(error)
    else:
        raise AssertionError("Unlabelled pair was accepted.")


def test_embedding_evaluator_selects_threshold() -> None:
    evaluator = EmbeddingEvaluator(
        embedding_engine=FakeEmbeddingEngine(),
        text_builder=ArticleTextBuilder(),
    )
    left = create_evaluation_article(
        "left",
        "Left",
        "Same",
        "RTS",
    )
    pairs = [
        ArticlePair(
            pair_id="same",
            left=left,
            right=create_evaluation_article(
                "right",
                "Right",
                "Same",
                "N1",
            ),
            same_event=True,
        ),
        ArticlePair(
            pair_id="different",
            left=left,
            right=create_evaluation_article(
                "other",
                "Other",
                "Different",
                "Danas",
            ),
            same_event=False,
        ),
    ]

    results = evaluator.calculate_similarities(pairs)
    metrics = evaluator.find_best_threshold(
        results,
        threshold_start=0.5,
        threshold_end=0.9,
        threshold_step=0.1,
    )

    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1 == 1.0


def test_article_pair_generator_creates_candidate_mix() -> None:
    articles = [
        create_evaluation_article(
            "same-left",
            "Zvezda pobedila Partizan u derbiju",
            "Crveno-beli slavili rezultatom 2:1.",
            "RTS",
        ),
        create_evaluation_article(
            "same-right",
            "Zvezda savladala Partizan u derbiju",
            "Pobeda crveno-belih rezultatom 2:1.",
            "N1",
            PUBLISHED_AT + timedelta(hours=2),
        ),
        create_evaluation_article(
            "hard-left",
            "Vlada usvojila novi budzet Srbije",
            "Ministri glasali o planu javnih prihoda.",
            "Politika",
        ),
        create_evaluation_article(
            "hard-right",
            "Skupstina raspravlja o budzet planu Srbije",
            "Poslanici otvorili novu sednicu parlamenta.",
            "Danas",
            PUBLISHED_AT + timedelta(hours=3),
        ),
        create_evaluation_article(
            "random-left",
            "Predsednik otvorio fabriku u Nisu",
            "Nova radna mesta otvorena su danas.",
            "Beta",
        ),
        create_evaluation_article(
            "random-right",
            "Kosarkasi stigli u Nisu",
            "Ekipa se priprema za gostujucu utakmicu.",
            "Vreme",
            PUBLISHED_AT + timedelta(hours=4),
        ),
    ]
    generator = ArticlePairGenerator(seed=1)

    pairs = generator.generate(
        articles,
        probable_same_event_count=1,
        hard_negative_count=1,
        random_negative_count=1,
    )

    assert {
        generator.candidate_type(pair)
        for pair in pairs
    } == {
        PROBABLE_SAME_EVENT,
        HARD_NEGATIVE,
        RANDOM_NEGATIVE,
    }
    assert all(pair.left.source != pair.right.source for pair in pairs)
    assert all(pair.same_event is None for pair in pairs)


def test_article_pair_generator_excludes_invalid_candidates() -> None:
    generator = ArticlePairGenerator()
    articles = [
        create_evaluation_article(
            "same-source-left",
            "Zvezda pobedila Partizan",
            "Derbi zavrsen pobedom.",
            "RTS",
        ),
        create_evaluation_article(
            "same-source-right",
            "Zvezda savladala Partizan",
            "Derbi zavrsen pobedom.",
            "RTS",
        ),
        create_evaluation_article(
            "too-late",
            "Zvezda pobedila Partizan",
            "Derbi zavrsen pobedom.",
            "N1",
            PUBLISHED_AT + timedelta(hours=73),
        ),
    ]

    pairs = generator.generate(
        articles,
        probable_same_event_count=10,
        hard_negative_count=10,
        random_negative_count=10,
    )

    assert pairs == []


def test_evaluation_article_repository_reads_active_and_inactive(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "evaluation.db"
    database_url = URL.create(
        drivername="sqlite+aiosqlite",
        database=str(database_path),
    )

    async def run_test() -> list[EvaluationArticle]:
        engine = create_async_engine(database_url)
        session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with session_factory() as session:
            session.add_all(
                [
                    _create_article_model(
                        "active",
                        PUBLISHED_AT,
                        True,
                    ),
                    _create_article_model(
                        "inactive",
                        PUBLISHED_AT - timedelta(days=1),
                        False,
                    ),
                    _create_article_model(
                        "old",
                        PUBLISHED_AT - timedelta(days=8),
                        True,
                    ),
                ]
            )
            await session.commit()
            repository = EvaluationArticleRepository(session)
            result = await repository.list_published_between(
                PUBLISHED_AT - timedelta(days=7),
                PUBLISHED_AT,
            )
        await engine.dispose()
        return result

    articles = asyncio.run(run_test())

    assert {article.article_id for article in articles} == {
        "active",
        "inactive",
    }
    assert all(
        article.published_at.tzinfo is not None
        for article in articles
    )


def _create_article_model(
    article_id: str,
    published_at: datetime,
    is_active: bool,
) -> ArticleModel:
    return ArticleModel(
        id=article_id,
        source_id="source",
        title=f"Title {article_id}",
        summary=f"Summary {article_id}",
        source=f"Source {article_id}",
        category="SERBIA",
        published_at=published_at,
        image_url=None,
        article_url=f"https://example.com/{article_id}",
        normalized_url=f"https://example.com/{article_id}",
        related_city_ids=[],
        is_active=is_active,
    )


def test_label_dataset_persists_updated_entry(tmp_path: Path) -> None:
    dataset_path = tmp_path / "pairs.jsonl"
    payload = create_pair_payload(None)
    dataset_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    entries = load_entries(dataset_path)
    entries[0]["sameEvent"] = False

    save_entries(dataset_path, entries)

    reloaded = load_entries(dataset_path)
    assert reloaded[0]["sameEvent"] is False
    assert not dataset_path.with_suffix(".jsonl.tmp").exists()


def test_cli_modules_run_from_experiments_directory() -> None:
    project_root = Path(__file__).resolve().parents[1]
    experiments_directory = project_root / "experiments"

    for module in (
        "semantic_grouping.generate_dataset",
        "semantic_grouping.label_dataset",
        "semantic_grouping.evaluate",
    ):
        result = subprocess.run(
            [sys.executable, "-m", module, "--help"],
            cwd=experiments_directory,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
