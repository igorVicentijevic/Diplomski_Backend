from datetime import UTC, datetime

from app.articles.schemas import ArticleResponse, NewsCategory

ARTICLES = (
    ArticleResponse(
        id="article-1",
        title="Prva vest",
        summary="Privremeni clanak za prvu iteraciju Articles API-ja.",
        source="Demo izvor",
        category=NewsCategory.SERBIA,
        published_at=datetime(2026, 9, 23, 18, 0, tzinfo=UTC),
        image_url=None,
        article_url="https://example.com/articles/1",
        related_city_ids=["beograd"],
    ),
    ArticleResponse(
        id="article-2",
        title="Nova tehnoloska vest",
        summary="Drugi privremeni clanak za proveru liste.",
        source="Demo izvor",
        category=NewsCategory.TECHNOLOGY,
        published_at=datetime(2026, 9, 23, 17, 30, tzinfo=UTC),
        image_url="https://example.com/images/2.jpg",
        article_url="https://example.com/articles/2",
        related_city_ids=[],
    ),
)


def list_articles() -> list[ArticleResponse]:
    return list(ARTICLES)


def get_article(article_id: str) -> ArticleResponse | None:
    return next(
        (article for article in ARTICLES if article.id == article_id),
        None,
    )
