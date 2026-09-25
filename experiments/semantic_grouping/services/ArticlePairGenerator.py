import hashlib
import random
import re
import unicodedata
from datetime import timedelta

from ..models.ArticlePair import ArticlePair
from ..models.EvaluationArticle import (
    EvaluationArticle,
)

PROBABLE_SAME_EVENT = "probable_same_event"
HARD_NEGATIVE = "hard_negative"
RANDOM_NEGATIVE = "random_negative"

_WORD_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)
_STOP_WORDS = {
    "ali",
    "biti",
    "da",
    "do",
    "i",
    "iz",
    "je",
    "koji",
    "na",
    "ne",
    "o",
    "od",
    "po",
    "sa",
    "se",
    "su",
    "u",
    "za",
}


class ArticlePairGenerator:
    def __init__(
        self,
        max_time_difference: timedelta = timedelta(hours=72),
        seed: int = 42,
    ) -> None:
        if max_time_difference <= timedelta(0):
            raise ValueError(
                "Maximum time difference must be greater than zero."
            )
        self._max_time_difference = max_time_difference
        self._random = random.Random(seed)

    def generate(
        self,
        articles: list[EvaluationArticle],
        probable_same_event_count: int,
        hard_negative_count: int,
        random_negative_count: int,
    ) -> list[ArticlePair]:
        limits = {
            PROBABLE_SAME_EVENT: probable_same_event_count,
            HARD_NEGATIVE: hard_negative_count,
            RANDOM_NEGATIVE: random_negative_count,
        }
        if any(limit < 0 for limit in limits.values()):
            raise ValueError("Candidate counts must not be negative.")

        samples: dict[str, list[ArticlePair]] = {
            candidate_type: []
            for candidate_type in limits
        }
        seen_counts = {
            candidate_type: 0
            for candidate_type in limits
        }

        ordered_articles = sorted(
            articles,
            key=lambda article: article.published_at,
        )
        for left_index, left in enumerate(ordered_articles):
            for right in ordered_articles[left_index + 1 :]:
                if (
                    right.published_at - left.published_at
                    > self._max_time_difference
                ):
                    break
                if left.source.casefold() == right.source.casefold():
                    continue

                pair = self._create_pair(left, right)
                candidate_type = self.candidate_type(pair)
                if candidate_type is None:
                    continue

                seen_counts[candidate_type] += 1
                self._add_to_reservoir(
                    samples[candidate_type],
                    pair,
                    limits[candidate_type],
                    seen_counts[candidate_type],
                )

        generated = [
            pair
            for candidate_type in (
                PROBABLE_SAME_EVENT,
                HARD_NEGATIVE,
                RANDOM_NEGATIVE,
            )
            for pair in samples[candidate_type]
        ]
        self._random.shuffle(generated)
        return generated

    def candidate_type(
        self,
        pair: ArticlePair,
    ) -> str | None:
        left_title = self._tokenize(pair.left.title)
        right_title = self._tokenize(pair.right.title)
        left_all = left_title | self._tokenize(pair.left.summary)
        right_all = right_title | self._tokenize(pair.right.summary)

        shared_title = left_title & right_title
        shared_all = left_all & right_all
        if not shared_all:
            return None

        title_overlap = self._overlap_coefficient(
            left_title,
            right_title,
        )
        combined_overlap = self._jaccard(left_all, right_all)
        if (
            len(shared_title) >= 2
            and title_overlap >= 0.5
        ) or combined_overlap >= 0.3:
            return PROBABLE_SAME_EVENT
        if len(shared_all) >= 2 or combined_overlap >= 0.12:
            return HARD_NEGATIVE
        return RANDOM_NEGATIVE

    def _add_to_reservoir(
        self,
        reservoir: list[ArticlePair],
        pair: ArticlePair,
        limit: int,
        seen_count: int,
    ) -> None:
        if limit == 0:
            return
        if len(reservoir) < limit:
            reservoir.append(pair)
            return

        replacement_index = self._random.randrange(seen_count)
        if replacement_index < limit:
            reservoir[replacement_index] = pair

    @staticmethod
    def _create_pair(
        left: EvaluationArticle,
        right: EvaluationArticle,
    ) -> ArticlePair:
        ordered = sorted(
            (left, right),
            key=lambda article: article.article_id,
        )
        identity = "\0".join(
            article.article_id for article in ordered
        )
        pair_hash = hashlib.sha256(
            identity.encode("utf-8")
        ).hexdigest()[:16]
        return ArticlePair(
            pair_id=f"pair-{pair_hash}",
            left=ordered[0],
            right=ordered[1],
            same_event=None,
        )

    @staticmethod
    def _tokenize(value: str) -> set[str]:
        normalized = unicodedata.normalize(
            "NFKC",
            value,
        ).casefold()
        return {
            word
            for word in _WORD_PATTERN.findall(normalized)
            if len(word) >= 3 and word not in _STOP_WORDS
        }

    @staticmethod
    def _jaccard(left: set[str], right: set[str]) -> float:
        union = left | right
        if not union:
            return 0.0
        return len(left & right) / len(union)

    @staticmethod
    def _overlap_coefficient(
        left: set[str],
        right: set[str],
    ) -> float:
        smaller_size = min(len(left), len(right))
        if smaller_size == 0:
            return 0.0
        return len(left & right) / smaller_size
