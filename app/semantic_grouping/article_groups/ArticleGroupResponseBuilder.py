from app.articles.models.ArticleModel import ArticleModel
from app.articles.services.ArticleService import ArticleService
from app.semantic_grouping.schemas.ArticleGroupResponse import (
    ArticleGroupResponse,
)


class ArticleGroupResponseBuilder:
    def build(
        self,
        article_ids_by_group: dict[str, set[str]],
        articles: list[ArticleModel],
    ) -> list[ArticleGroupResponse]:
        articles_by_id = {article.id: article for article in articles}
        groups = [
            self._create_group(
                group_id,
                article_ids,
                articles_by_id,
            )
            for group_id, article_ids in article_ids_by_group.items()
        ]
        visible_groups = [
            group for group in groups if len(group.articles) >= 2
        ]
        return sorted(
            visible_groups,
            key=lambda group: group.articles[0].published_at,
            reverse=True,
        )

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
