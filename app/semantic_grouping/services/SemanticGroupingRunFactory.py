from datetime import datetime
from uuid import uuid4

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.models.SemanticGroupingConfiguration import (
    SemanticGroupingConfiguration,
)
from app.semantic_grouping.models.SemanticGroupingDecision import (
    SemanticGroupingDecision,
)
from app.semantic_grouping.models.SemanticGroupingDecisionModel import (
    SemanticGroupingDecisionModel,
)
from app.semantic_grouping.models.SemanticGroupingRunModel import (
    SemanticGroupingRunModel,
)


class SemanticGroupingRunFactory:
    def __init__(
        self,
        configuration: SemanticGroupingConfiguration,
    ) -> None:
        self._configuration = configuration

    def create(
        self,
        articles: list[ArticleModel],
        decisions: list[SemanticGroupingDecision],
        created_at: datetime,
    ) -> tuple[
        SemanticGroupingRunModel,
        list[SemanticGroupingDecisionModel],
    ]:
        run = SemanticGroupingRunModel(
            id=str(uuid4()),
            model_name=self._configuration.model_name,
            threshold=self._configuration.threshold,
            boundary_min=self._configuration.boundary_min,
            boundary_max=self._configuration.boundary_max,
            candidate_window_hours=int(
                self._configuration.candidate_window.total_seconds()
                // 3600
            ),
            article_count=len(articles),
            pair_count=len(decisions),
            positive_pair_count=sum(
                decision.predicted_same_event
                for decision in decisions
            ),
            boundary_pair_count=sum(
                decision.is_boundary_candidate
                for decision in decisions
            ),
            created_at=created_at,
        )
        decision_models = [
            self._create_decision_model(run.id, decision)
            for decision in decisions
        ]
        return run, decision_models

    @staticmethod
    def _create_decision_model(
        run_id: str,
        decision: SemanticGroupingDecision,
    ) -> SemanticGroupingDecisionModel:
        return SemanticGroupingDecisionModel(
            id=str(uuid4()),
            run_id=run_id,
            left_article_id=decision.left_article_id,
            right_article_id=decision.right_article_id,
            similarity=decision.similarity,
            predicted_same_event=decision.predicted_same_event,
            proposed_group_id=decision.proposed_group_id,
            is_boundary_candidate=decision.is_boundary_candidate,
        )
