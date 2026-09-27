from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.articles.models.ArticleModel import ArticleModel


class ArticleEmbeddingProvider(ABC):
    """Supplies one embedding vector per article, keyed by article id."""

    @abstractmethod
    async def provide(
        self,
        articles: Sequence[ArticleModel],
    ) -> dict[str, list[float]]:
        ...
