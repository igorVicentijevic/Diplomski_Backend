from collections import defaultdict

from app.articles.models.ArticleModel import ArticleModel
from app.articles.services.ArticleService import ArticleService
from app.semantic_grouping.repositories.SemanticGroupingRepository import (
    SemanticGroupingRepository,
)
from app.semantic_grouping.models.SemanticGroupingDecisionModel import (
    SemanticGroupingDecisionModel,
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

    async def list_groups(self) -> list[ArticleGroupResponse]:

        article_ids_by_group = await self._gather_articles_into_groups()

        articles_by_id = await self._load_articles_by_id(
            article_ids_by_group
        )

        #join article IDs with their corresponding articles to form groups
        groups = self._create_groups(
            article_ids_by_group,
            articles_by_id,
        )

        #sort groups by the published date of the first article in each group
        return self._sort_groups(self._filter_visible_groups(groups))

    async def _gather_articles_into_groups(
        self,
    ) -> dict[str, set[str]]:
        
        run = await self._repository.get_latest_run()
        
        if run is None:
            return {}

        decisions = await self._repository.list_grouped_decisions(run.id)
        return self._collect_article_ids(decisions)

    async def _load_articles_by_id(
        self,
        article_ids_by_group: dict[str, set[str]],
    ) -> dict[str, ArticleModel]:
        article_ids = {
            article_id
            for group_article_ids in article_ids_by_group.values()
            for article_id in group_article_ids
        }
        
        articles = (
            await self._repository.list_active_analyzed_articles_by_ids(
                article_ids
            )
        )
        return {
            article.id: article
            for article in articles
        }

    def _create_groups(
        self,
        article_ids_by_group: dict[str, set[str]],
        articles_by_id: dict[str, ArticleModel],
    ) -> list[ArticleGroupResponse]:
        return [
            self._create_group(group_id, group_article_ids, articles_by_id)
            for group_id, group_article_ids in article_ids_by_group.items()
        ]

    @staticmethod
    def _filter_visible_groups(
        groups: list[ArticleGroupResponse],
    ) -> list[ArticleGroupResponse]:
        return [
            group
            for group in groups
            if len(group.articles) >= 2
        ]

    @staticmethod
    def _sort_groups(
        groups: list[ArticleGroupResponse],
    ) -> list[ArticleGroupResponse]:
        return sorted(
            groups,
            key=lambda group: group.articles[0].published_at,
            reverse=True,
        )

    @staticmethod
    def _collect_article_ids(
        decisions: list[SemanticGroupingDecisionModel],
    ) -> dict[str, set[str]]:
        article_ids_by_group: defaultdict[str, set[str]] = defaultdict(set)
        for decision in decisions:
            if decision.proposed_group_id is None:
                continue
            article_ids_by_group[decision.proposed_group_id].update(
                (
                    decision.left_article_id,
                    decision.right_article_id,
                )
            )
        return dict(article_ids_by_group)

    @staticmethod
    def _create_group(
        group_id: str,
        article_ids: set[str],
        articles_by_id: dict[str, ArticleModel],
    ) -> ArticleGroupResponse:
        articles = sorted(
            (
                ArticleService.to_response(articles_by_id[article_id])
                for article_id in article_ids
                if article_id in articles_by_id
            ),
            key=lambda article: article.published_at,
            reverse=True,
        )
        return ArticleGroupResponse(
            id=group_id,
            articles=articles,
        )
