from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ArticleUpsertResult:
    changed_count: int
    article_ids_by_normalized_url: dict[str, str]
