import asyncio

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.ArticleTextBuilder import ArticleTextBuilder
from app.semantic_grouping.embedding_engine.EmbeddingEngine import (
    EmbeddingEngine,
)


class ArticleEmbeddingService:
    def __init__(
        self,
        embedding_engine: EmbeddingEngine,
        text_builder: ArticleTextBuilder,
    ) -> None:
        self._embedding_engine = embedding_engine
        self._text_builder = text_builder

    async def create_embeddings(
        self,
        articles: list[ArticleModel],
    ) -> dict[str, list[float]]:
        texts = [
            self._text_builder.build(article.title, article.summary)
            for article in articles
        ]
        embeddings = await asyncio.to_thread(
            self._embedding_engine.encode,
            texts,
        )
        if len(embeddings) != len(articles):
            raise ValueError(
                "Embedding engine returned an unexpected number "
                "of embeddings."
            )

        return {
            article.id: embedding
            for article, embedding in zip(
                articles,
                embeddings,
                strict=True,
            )
        }
