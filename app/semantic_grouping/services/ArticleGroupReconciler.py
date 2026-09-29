from datetime import UTC, datetime
from uuid import uuid4

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.models.ArticleGroupMembershipModel import (
    ArticleGroupMembershipModel,
)
from app.semantic_grouping.models.ArticleGroupModel import ArticleGroupModel
from app.semantic_grouping.repositories.SemanticGroupingRepository import (
    SemanticGroupingRepository,
)


class ArticleGroupReconciler:
    def __init__(
        self,
        repository: SemanticGroupingRepository,
    ) -> None:
        self._repository = repository

    async def reconcile(
        self,
        proposed_groups: dict[str, set[str]],
        articles: list[ArticleModel],
        reconciled_at: datetime,
    ) -> None:
        
        groups = await self._repository.list_article_groups()
        memberships = await self._repository.list_group_memberships(
            {group.id for group in groups}
        )
        
        article_by_id = {article.id: article for article in articles}
        matched_groups = self._match_groups(
            proposed_groups,
            groups,
            memberships,
        )

        active_group_ids: set[str] = set()
        new_groups: list[ArticleGroupModel] = []
        new_memberships: list[ArticleGroupMembershipModel] = []
        for proposed_group_id, article_ids in proposed_groups.items():
            group = matched_groups.get(proposed_group_id)
            if group is None:
                group = self._create_group(
                    article_ids,
                    article_by_id,
                    reconciled_at,
                )
                new_groups.append(group)

            active_group_ids.add(group.id)
            group.active = True
            group.updated_at = reconciled_at
            group.latest_article_at = self._latest_article_at(
                article_ids,
                article_by_id,
                group.latest_article_at,
            )
            existing_article_ids = memberships.get(group.id, set())
            new_memberships.extend(
                ArticleGroupMembershipModel(
                    group_id=group.id,
                    article_id=article_id,
                    added_at=reconciled_at,
                )
                for article_id in article_ids - existing_article_ids
            )

        for group in groups:
            if group.active and group.id not in active_group_ids:
                group.active = False
                group.updated_at = reconciled_at

        await self._repository.add_article_groups(new_groups)
        self._repository.add_group_memberships(new_memberships)

    @staticmethod
    def _match_groups(
        proposed_groups: dict[str, set[str]],
        groups: list[ArticleGroupModel],
        memberships: dict[str, set[str]],
    ) -> dict[str, ArticleGroupModel]:
        candidates: list[tuple[int, int, str, str, ArticleGroupModel]] = []
        for proposed_group_id, proposed_article_ids in proposed_groups.items():
            for group in groups:
                overlap = len(
                    proposed_article_ids & memberships.get(group.id, set())
                )
                if overlap:
                    candidates.append(
                        (
                            -overlap,
                            -int(group.active),
                            proposed_group_id,
                            group.id,
                            group,
                        )
                    )

        matches: dict[str, ArticleGroupModel] = {}
        matched_group_ids: set[str] = set()
        for _, _, proposed_group_id, group_id, group in sorted(candidates):
            if (
                proposed_group_id not in matches
                and group_id not in matched_group_ids
            ):
                matches[proposed_group_id] = group
                matched_group_ids.add(group_id)
        return matches

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
    def _latest_article_at(
        article_ids: set[str],
        article_by_id: dict[str, ArticleModel],
        current_latest: datetime | None = None,
    ) -> datetime:
        timestamps = [
            ArticleGroupReconciler._as_utc(
                article_by_id[article_id].published_at
            )
            for article_id in article_ids
        ]
        if current_latest is not None:
            timestamps.append(
                ArticleGroupReconciler._as_utc(current_latest)
            )
        return max(timestamps)

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
