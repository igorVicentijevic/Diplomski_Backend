from datetime import datetime

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.article_groups.ArticleGroupReconciler import (
    ArticleGroupReconciler,
)
from app.semantic_grouping.article_groups.ArticleGroupResponseBuilder import (
    ArticleGroupResponseBuilder,
)
from app.semantic_grouping.repositories.SemanticGroupingRepository import (
    SemanticGroupingRepository,
)
from app.semantic_grouping.schemas.ArticleGroupResponse import (
    ArticleGroupResponse,
)


class ArticleGroupService:
    def __init__(
        self,
        repository: SemanticGroupingRepository,
    ) -> None:
        self._repository = repository
        self._response_builder = ArticleGroupResponseBuilder()

    async def list_groups(self) -> list[ArticleGroupResponse]:
        groups = await self._repository.list_active_article_groups()
        article_ids_by_group = (
            await self._repository.list_group_memberships(
                {group.id for group in groups}
            )
        )
        articles = (
            await self._repository.list_active_analyzed_articles_by_ids(
                {
                    article_id
                    for article_ids in article_ids_by_group.values()
                    for article_id in article_ids
                }
            )
        )
        return self._response_builder.build(
            article_ids_by_group,
            articles,
        )

    async def reconcile(
        self,
        proposed_groups: dict[str, set[str]],
        articles: list[ArticleModel],
        reconciled_at: datetime,
    ) -> None:
        await ArticleGroupReconciler(self._repository).reconcile(
            proposed_groups,
            articles,
            reconciled_at,
        )
