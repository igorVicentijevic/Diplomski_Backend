from datetime import UTC, datetime
from uuid import uuid4

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.models.ArticleGroupMembershipModel import (
    ArticleGroupMembershipModel,
)
from app.semantic_grouping.models.ArticleGroupModel import ArticleGroupModel


class ArticleGroupSynchronizer:
    def synchronize(
        self,
        group: ArticleGroupModel | None,
        article_ids: set[str],
        existing_article_ids: set[str],
        article_by_id: dict[str, ArticleModel],
        synchronized_at: datetime,
    ) -> tuple[
        ArticleGroupModel,
        list[ArticleGroupMembershipModel],
    ]:
        if group is None:
            group = self._create_group(
                article_ids,
                article_by_id,
                synchronized_at,
            )
        else:
            group.latest_article_at = self._latest_article_at(
                article_ids,
                article_by_id,
                group.latest_article_at,
            )

        group.active = True
        group.updated_at = synchronized_at
        return group, self._create_missing_memberships(
            group.id,
            article_ids - existing_article_ids,
            synchronized_at,
        )

    def _create_group(
        self,
        article_ids: set[str],
        article_by_id: dict[str, ArticleModel],
        created_at: datetime,
    ) -> ArticleGroupModel:
        return ArticleGroupModel(
            id=str(uuid4()),
            created_at=created_at,
            updated_at=created_at,
            latest_article_at=self._latest_article_at(
                article_ids,
                article_by_id,
            ),
            active=True,
        )

    @staticmethod
    def _create_missing_memberships(
        group_id: str,
        article_ids: set[str],
        added_at: datetime,
    ) -> list[ArticleGroupMembershipModel]:
        return [
            ArticleGroupMembershipModel(
                group_id=group_id,
                article_id=article_id,
                added_at=added_at,
            )
            for article_id in article_ids
        ]

    @staticmethod
    def _latest_article_at(
        article_ids: set[str],
        article_by_id: dict[str, ArticleModel],
        current_latest: datetime | None = None,
    ) -> datetime:
        timestamps = [
            ArticleGroupSynchronizer._as_utc(
                article_by_id[article_id].published_at
            )
            for article_id in article_ids
        ]
        if current_latest is not None:
            timestamps.append(
                ArticleGroupSynchronizer._as_utc(current_latest)
            )
        return max(timestamps)

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
