from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ArticlePairSimilarity:
    """A candidate article pair together with its cosine similarity."""

    left_article_id: str
    right_article_id: str
    similarity: float
