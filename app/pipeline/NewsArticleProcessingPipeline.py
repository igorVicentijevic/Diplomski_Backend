from app.news_sources.models.NewsArticle import NewsArticle
from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)
from app.pipeline.NewsArticleProcessingStep import (
    NewsArticleProcessingStep,
)


class NewsArticleProcessingPipeline:
    def __init__(
        self,
        steps: list[NewsArticleProcessingStep],
    ) -> None:
        self._steps = steps

    async def process(
        self,
        articles: list[NewsArticle],
    ) -> list[ArticleProcessingContext]:
        
        contexts = [
            ArticleProcessingContext(article=article)
            for article in articles
        ]

        for step in self._steps:
            contexts = await step.process(contexts)

        return contexts
