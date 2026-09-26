from app.semantic_grouping.article_groups.ProposedArticleGroupCollector import (
    ProposedArticleGroupCollector,
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
        self._group_collector = ProposedArticleGroupCollector()
        self._response_builder = ArticleGroupResponseBuilder()

    async def list_groups(self) -> list[ArticleGroupResponse]:
        run = await self._repository.get_latest_run()
        if run is None:
            return []

        decisions = await self._repository.list_grouped_decisions(run.id)
        article_ids_by_group = self._group_collector.collect(decisions)
        articles = await self._repository.list_active_analyzed_articles_by_ids(
            {
                article_id
                for article_ids in article_ids_by_group.values()
                for article_id in article_ids
            }
        )
        return self._response_builder.build(
            article_ids_by_group,
            articles,
        )
