from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.models.ArticleModel import ArticleModel

SEED_ARTICLES = (
    {
        "id": "article-1",
        "title": "Prva vest",
        "summary": "Privremeni clanak za prvu iteraciju Articles API-ja.",
        "source": "Demo izvor",
        "category": "SERBIA",
        "published_at": datetime(2026, 9, 23, 18, 0, tzinfo=UTC),
        "image_url": None,
        "article_url": "https://example.com/articles/1",
        "normalized_url": "https://example.com/articles/1",
        "related_city_ids": ["beograd"],
    },
    {
        "id": "article-2",
        "title": "Nova tehnoloska vest",
        "summary": "Drugi privremeni clanak za proveru liste.",
        "source": "Demo izvor",
        "category": "TECHNOLOGY",
        "published_at": datetime(2026, 9, 23, 17, 30, tzinfo=UTC),
        "image_url": "https://example.com/images/2.jpg",
        "article_url": "https://example.com/articles/2",
        "normalized_url": "https://example.com/articles/2",
        "related_city_ids": [],
    },
)


async def seed_articles(session: AsyncSession) -> int:
    existing_ids = set(
        await session.scalars(
            select(ArticleModel.id).where(
                ArticleModel.id.in_(
                    article["id"] for article in SEED_ARTICLES
                )
            )
        )
    )
    new_articles = [
        ArticleModel(**article)
        for article in SEED_ARTICLES
        if article["id"] not in existing_ids
    ]
    session.add_all(new_articles)
    await session.commit()
    return len(new_articles)
