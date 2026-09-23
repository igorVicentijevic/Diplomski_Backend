from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.models.ArticleModel import ArticleModel


class ArticleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_articles(self) -> list[ArticleModel]:
        result = await self._session.scalars(
            select(ArticleModel).order_by(
                ArticleModel.published_at.desc()
            )
        )
        return list(result)

    async def get_article(
        self,
        article_id: str,
    ) -> ArticleModel | None:
        return await self._session.get(ArticleModel, article_id)

    async def upsert_articles(
        self,
        articles: list[ArticleModel],
    ) -> int:
        if not articles:
            return 0

        normalized_urls = [article.normalized_url for article in articles]
        existing_articles = await self._session.scalars(
            select(ArticleModel).where(
                ArticleModel.normalized_url.in_(normalized_urls)
            )
        )
        existing_by_url = {
            article.normalized_url: article
            for article in existing_articles
        }

        changed_count = 0
        for article in articles:
            existing = existing_by_url.get(article.normalized_url)
            if existing is None:
                self._session.add(article)
                existing_by_url[article.normalized_url] = article
                changed_count += 1
                continue

            changed_count += self._update_article(existing, article)

        await self._session.commit()
        return changed_count

    @staticmethod
    def _update_article(
        existing: ArticleModel,
        incoming: ArticleModel,
    ) -> int:
        changed = False
        for column in ArticleModel.__table__.columns:
            if column.name in {
                "id",
                "normalized_url",
                "first_seen_at",
                "updated_at",
            }:
                continue

            field_name = column.key
            incoming_value = getattr(incoming, field_name)
            if not ArticleRepository._values_equal(
                getattr(existing, field_name),
                incoming_value,
            ):
                setattr(existing, field_name, incoming_value)
                changed = True

        return int(changed)

    @staticmethod
    def _values_equal(
        existing: object,
        incoming: object,
    ) -> bool:
        if isinstance(existing, datetime) and isinstance(
            incoming,
            datetime,
        ):
            existing_utc = (
                existing.replace(tzinfo=UTC)
                if existing.tzinfo is None
                else existing.astimezone(UTC)
            )
            incoming_utc = (
                incoming.replace(tzinfo=UTC)
                if incoming.tzinfo is None
                else incoming.astimezone(UTC)
            )
            return existing_utc == incoming_utc

        return existing == incoming
