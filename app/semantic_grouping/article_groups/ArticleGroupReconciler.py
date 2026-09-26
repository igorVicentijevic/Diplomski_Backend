from datetime import datetime

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.article_groups.ArticleGroupMatcher import (
    ArticleGroupMatcher,
)
from app.semantic_grouping.article_groups.ArticleGroupSynchronizer import (
    ArticleGroupSynchronizer,
)
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
        self._matcher = ArticleGroupMatcher()
        self._synchronizer = ArticleGroupSynchronizer()

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
        matched_groups = self._matcher.match(
            proposed_groups,
            groups,
            memberships,
        )

        active_group_ids: set[str] = set()
        new_groups: list[ArticleGroupModel] = []
        new_memberships: list[ArticleGroupMembershipModel] = []
        for proposed_group_id, article_ids in proposed_groups.items():
            group = matched_groups.get(proposed_group_id)
            is_new_group = group is None
            existing_article_ids = (
                memberships.get(group.id, set())
                if group is not None
                else set()
            )
            group, memberships_to_add = self._synchronizer.synchronize(
                group=group,
                article_ids=article_ids,
                existing_article_ids=existing_article_ids,
                article_by_id=article_by_id,
                synchronized_at=reconciled_at,
            )
            if is_new_group:
                new_groups.append(group)

            active_group_ids.add(group.id)
            new_memberships.extend(memberships_to_add)

        for group in groups:
            if group.active and group.id not in active_group_ids:
                group.active = False
                group.updated_at = reconciled_at

        await self._repository.add_article_groups(new_groups)
        self._repository.add_group_memberships(new_memberships)
