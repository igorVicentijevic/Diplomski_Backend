from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.models import ArticleModel
from ..models.EvaluationArticle import (
    EvaluationArticle,
)


class EvaluationArticleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_published_between(
        self,
        published_from: datetime,
        published_until: datetime,
    ) -> list[EvaluationArticle]:
        rows = await self._session.execute(
            select(
                ArticleModel.id,
                ArticleModel.title,
                ArticleModel.summary,
                ArticleModel.source,
                ArticleModel.published_at,
                ArticleModel.normalized_url,
            )
            .where(
                ArticleModel.published_at >= published_from,
                ArticleModel.published_at <= published_until,
            )
            .order_by(ArticleModel.published_at.desc())
        )

        articles: list[EvaluationArticle] = []
        seen_urls: set[str] = set()
        for row in rows:
            if row.normalized_url in seen_urls:
                continue

            seen_urls.add(row.normalized_url)
            published_at = row.published_at
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=UTC)

            articles.append(
                EvaluationArticle(
                    article_id=row.id,
                    title=row.title,
                    summary=row.summary,
                    source=row.source,
                    published_at=published_at,
                )
            )

        return articles
