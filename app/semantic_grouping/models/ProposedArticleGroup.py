from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProposedArticleGroup:
    """A set of articles proposed to describe the same event."""

    group_id: str
    article_ids: frozenset[str]

    def __post_init__(self) -> None:
        if not self.group_id.strip():
            raise ValueError("Group id must not be empty.")
        if not self.article_ids:
            raise ValueError("A group must contain at least one article.")
