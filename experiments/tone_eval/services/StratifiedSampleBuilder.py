import hashlib
import random

from experiments.tone_eval.models.EvaluationItem import EvaluationItem
from experiments.tone_eval.models.ToneLabel import ToneLabel
from experiments.tone_eval.repositories.ToneEvaluationRepository import (
    AnalysedArticle,
)


class StratifiedSampleBuilder:
    """Builds a sample with a fixed number of items per model-predicted class.

    Stratification is deliberate: the neutral class dominates the corpus, so a
    purely random sample would contain too few positive articles for a stable
    per-class recall. The consequence is that overall accuracy on this sample
    is not an estimate of accuracy in production, and that limitation is stated
    in the thesis.
    """

    def __init__(self, per_class: int, seed: int) -> None:
        self._per_class = per_class
        self._random = random.Random(seed)

    def build(self, articles: list[AnalysedArticle]) -> list[EvaluationItem]:
        buckets: dict[ToneLabel, list[AnalysedArticle]] = {
            label: [] for label in ToneLabel
        }
        for article in articles:
            label = ToneLabel.from_percentages(
                negative=article.negative,
                positive=article.positive,
                neutral=article.neutral,
            )
            buckets[label].append(article)

        selected: list[AnalysedArticle] = []
        for label, bucket in buckets.items():
            if len(bucket) < self._per_class:
                raise ValueError(
                    f"Klasa {label.value} ima samo {len(bucket)} clanaka, "
                    f"a trazi se {self._per_class}."
                )
            bucket.sort(key=lambda item: item.article_id)
            selected.extend(self._random.sample(bucket, self._per_class))

        self._random.shuffle(selected)
        return [
            EvaluationItem(
                item_id=self._item_id(article.article_id),
                article_id=article.article_id,
                title=article.title.strip(),
                summary=article.summary.strip(),
                source=article.source,
                category=article.category,
                model_negative=article.negative,
                model_positive=article.positive,
                model_neutral=article.neutral,
            )
            for article in selected
        ]

    @staticmethod
    def _item_id(article_id: str) -> str:
        return hashlib.sha256(article_id.encode("utf-8")).hexdigest()[:12]

    def class_counts(
        self,
        articles: list[AnalysedArticle],
    ) -> dict[ToneLabel, int]:
        counts = {label: 0 for label in ToneLabel}
        for article in articles:
            label = ToneLabel.from_percentages(
                negative=article.negative,
                positive=article.positive,
                neutral=article.neutral,
            )
            counts[label] += 1
        return counts
