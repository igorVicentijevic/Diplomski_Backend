from collections import defaultdict

from app.semantic_grouping.models.ProposedArticleGroup import (
    ProposedArticleGroup,
)
from app.semantic_grouping.models.SemanticGroupingDecisionModel import (
    SemanticGroupingDecisionModel,
)


class ProposedArticleGroupCollector:
    def collect(
        self,
        decisions: list[SemanticGroupingDecisionModel],
    ) -> list[ProposedArticleGroup]:
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

        return [
            ProposedArticleGroup(
                group_id=group_id,
                article_ids=frozenset(article_ids),
            )
            for group_id, article_ids in article_ids_by_group.items()
        ]
