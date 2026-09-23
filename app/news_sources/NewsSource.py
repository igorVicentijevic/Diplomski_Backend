from abc import ABC, abstractmethod

from app.news_sources.models.NewsArticle import NewsArticle


class NewsSource(ABC):
    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        pass

    @abstractmethod
    async def fetch_articles(self) -> list[NewsArticle]:
        pass
