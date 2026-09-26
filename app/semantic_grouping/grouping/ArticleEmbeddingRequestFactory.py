from collections.abc import Sequence

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.grouping.ArticleEmbeddingInputHasher import (
    ArticleEmbeddingInputHasher,
)
from app.semantic_grouping.grouping.ArticleTextBuilder import (
    ArticleTextBuilder,
)
from app.semantic_grouping.models.ArticleEmbeddingRequest import (
    ArticleEmbeddingRequest,
)


class ArticleEmbeddingRequestFactory:
    def __init__(
        self,
        text_builder: ArticleTextBuilder,
        input_hasher: ArticleEmbeddingInputHasher,
    ) -> None:
        self._text_builder = text_builder
        self._input_hasher = input_hasher

    def create(
        self,
        articles: Sequence[ArticleModel],
    ) -> list[ArticleEmbeddingRequest]:
        return [self._create_request(article) for article in articles]

    def _create_request(
        self,
        article: ArticleModel,
    ) -> ArticleEmbeddingRequest:
        text = self._text_builder.build(article.title, article.summary)

        return ArticleEmbeddingRequest(
            article_id=article.id,
            text=text,
            input_hash=self._input_hasher.calculate(text),
        )
