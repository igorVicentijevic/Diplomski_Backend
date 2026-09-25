import json
from pathlib import Path

from experiments.semantic_grouping.ArticleTextBuilder import (
    ArticleTextBuilder,
)
from experiments.semantic_grouping.EmbeddingEvaluator import (
    EmbeddingEvaluator,
)
from experiments.semantic_grouping.LabelledPairLoader import (
    LabelledPairLoader,
)
from experiments.semantic_grouping.models.ArticlePair import ArticlePair


class FakeEmbeddingModel:
    def encode(self, texts: list[str]) -> list[list[float]]:
        embeddings = {
            "Title: Left\nSummary: Same": [1.0, 0.0],
            "Title: Right\nSummary: Same": [0.9, 0.1],
            "Title: Other\nSummary: Different": [0.0, 1.0],
        }
        return [embeddings[text] for text in texts]


def test_labelled_pair_loader_reads_jsonl(tmp_path: Path) -> None:
    dataset_path = tmp_path / "pairs.jsonl"
    dataset_path.write_text(
        json.dumps(
            {
                "id": "pair-1",
                "left": {
                    "title": "Left",
                    "summary": "Same",
                },
                "right": {
                    "title": "Right",
                    "summary": "Same",
                },
                "sameEvent": True,
            }
        ),
        encoding="utf-8",
    )

    pairs = LabelledPairLoader().load(dataset_path)

    assert pairs == [
        ArticlePair(
            pair_id="pair-1",
            left_title="Left",
            left_summary="Same",
            right_title="Right",
            right_summary="Same",
            same_event=True,
        )
    ]


def test_embedding_evaluator_selects_threshold() -> None:
    evaluator = EmbeddingEvaluator(
        embedding_model=FakeEmbeddingModel(),
        text_builder=ArticleTextBuilder(),
    )
    pairs = [
        ArticlePair(
            pair_id="same",
            left_title="Left",
            left_summary="Same",
            right_title="Right",
            right_summary="Same",
            same_event=True,
        ),
        ArticlePair(
            pair_id="different",
            left_title="Left",
            left_summary="Same",
            right_title="Other",
            right_summary="Different",
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
