from app.articles.models.ArticleModel import ArticleModel
from app.articles.services.ArticleService import ArticleService
from app.semantic_grouping.models.ProposedArticleGroup import (
    ProposedArticleGroup,
)
from app.semantic_grouping.schemas.ArticleGroupResponse import (
    ArticleGroupResponse,
)


class ArticleGroupResponseBuilder:
    def build(
        self,
        proposed_groups: list[ProposedArticleGroup],
        articles: list[ArticleModel],
    ) -> list[ArticleGroupResponse]:
        articles_by_id = {article.id: article for article in articles}
        groups = [
            self._create_group(
                proposed_group,
                articles_by_id,
            )
            for proposed_group in proposed_groups
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
        proposed_group: ProposedArticleGroup,
        articles_by_id: dict[str, ArticleModel],
    ) -> ArticleGroupResponse:
        articles = sorted(
            (
                ArticleService.to_response(articles_by_id[article_id])
                for article_id in proposed_group.article_ids
                if article_id in articles_by_id
            ),
            key=lambda article: article.published_at,
            reverse=True,
        )
        return ArticleGroupResponse(
            id=proposed_group.group_id,
            articles=articles,
        )
