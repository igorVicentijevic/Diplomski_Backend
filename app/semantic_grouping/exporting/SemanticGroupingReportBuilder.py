from collections import defaultdict
from datetime import UTC, datetime

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.models.SemanticGroupingDecisionModel import (
    SemanticGroupingDecisionModel,
)
from app.semantic_grouping.models.SemanticGroupingRunModel import (
    SemanticGroupingRunModel,
)


class SemanticGroupingReportBuilder:
    def build(
        self,
        run: SemanticGroupingRunModel,
        decisions: list[SemanticGroupingDecisionModel],
        articles: list[ArticleModel],
    ) -> str:
        decisions_by_group = self._group_decisions(decisions)
        articles_by_id = {article.id: article for article in articles}
        lines = self._build_header(run, len(decisions_by_group))

        if not decisions_by_group:
            lines.extend(
                [
                    "",
                    "No proposed groups were found for this run.",
                ]
            )
            return "\n".join(lines) + "\n"

        ordered_groups = sorted(
            decisions_by_group.items(),
            key=lambda item: (
                -len(self.article_ids(item[1])),
                item[0],
            ),
        )
        for group_index, (group_id, group_decisions) in enumerate(
            ordered_groups,
            start=1,
        ):
            lines.extend(
                self._build_group(
                    group_index,
                    group_id,
                    group_decisions,
                    articles_by_id,
                )
            )
        return "\n".join(lines) + "\n"

    @staticmethod
    def article_ids(
        decisions: list[SemanticGroupingDecisionModel],
    ) -> set[str]:
        return {
            article_id
            for decision in decisions
            for article_id in (
                decision.left_article_id,
                decision.right_article_id,
            )
        }

    @staticmethod
    def _build_header(
        run: SemanticGroupingRunModel,
        group_count: int,
    ) -> list[str]:
        return [
            "# Semantic grouping export",
            "",
            f"- Run ID: `{run.id}`",
            (
                "- Created at: "
                f"{SemanticGroupingReportBuilder._format_datetime(run.created_at)}"
            ),
            f"- Model: `{run.model_name}`",
            f"- Threshold: {run.threshold:.4f}",
            (
                "- Boundary range: "
                f"{run.boundary_min:.4f}-{run.boundary_max:.4f}"
            ),
            f"- Candidate window: {run.candidate_window_hours} hours",
            f"- Articles considered: {run.article_count}",
            f"- Pairs evaluated: {run.pair_count}",
            f"- Positive pairs: {run.positive_pair_count}",
            f"- Proposed groups: {group_count}",
        ]

    def _build_group(
        self,
        group_index: int,
        group_id: str,
        decisions: list[SemanticGroupingDecisionModel],
        articles_by_id: dict[str, ArticleModel],
    ) -> list[str]:
        articles = sorted(
            (
                articles_by_id[article_id]
                for article_id in self.article_ids(decisions)
                if article_id in articles_by_id
            ),
            key=lambda article: (
                self._as_utc(article.published_at),
                article.id,
            ),
        )
        similarities = [
            decision.similarity for decision in decisions
        ]
        lines = [
            "",
            f"## Group {group_index}",
            "",
            f"- Group ID: `{group_id}`",
            f"- Article count: {len(articles)}",
            f"- Positive links: {len(decisions)}",
            (
                "- Similarity: "
                f"min {min(similarities):.4f}, "
                f"average {sum(similarities) / len(similarities):.4f}, "
                f"max {max(similarities):.4f}"
            ),
        ]
        for article_index, article in enumerate(articles, start=1):
            lines.extend(
                self._build_article(article_index, article)
            )
        return lines

    @staticmethod
    def _build_article(
        article_index: int,
        article: ArticleModel,
    ) -> list[str]:
        title = " ".join(article.title.split())
        summary = " ".join(article.summary.split())
        return [
            "",
            f"### {article_index}. {title}",
            "",
            f"- Source: {article.source}",
            (
                "- Published at: "
                f"{SemanticGroupingReportBuilder._format_datetime(article.published_at)}"
            ),
            f"- Article ID: `{article.id}`",
            f"- URL: <{article.article_url}>",
            "",
            f"> {summary}",
        ]

    @staticmethod
    def _group_decisions(
        decisions: list[SemanticGroupingDecisionModel],
    ) -> dict[str, list[SemanticGroupingDecisionModel]]:
        grouped: defaultdict[
            str,
            list[SemanticGroupingDecisionModel],
        ] = defaultdict(list)
        for decision in decisions:
            if decision.proposed_group_id is not None:
                grouped[decision.proposed_group_id].append(decision)
        return dict(grouped)

    @staticmethod
    def _format_datetime(value: datetime) -> str:
        return SemanticGroupingReportBuilder._as_utc(value).isoformat()

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
