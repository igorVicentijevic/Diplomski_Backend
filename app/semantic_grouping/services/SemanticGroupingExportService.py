from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.models.SemanticGroupingDecisionModel import (
    SemanticGroupingDecisionModel,
)
from app.semantic_grouping.models.SemanticGroupingRunModel import (
    SemanticGroupingRunModel,
)
from app.semantic_grouping.repositories.SemanticGroupingRepository import (
    SemanticGroupingRepository,
)


class SemanticGroupingExportService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def export(
        self,
        output: Path | None = None,
        run_id: str | None = None,
    ) -> Path:
        async with self._session_factory() as session:
            repository = SemanticGroupingRepository(session)
            run = await self._get_run(repository, run_id)
            decisions = await repository.list_grouped_decisions(run.id)
            article_ids = {
                article_id
                for decision in decisions
                for article_id in (
                    decision.left_article_id,
                    decision.right_article_id,
                )
            }
            articles = await repository.list_articles_by_ids(article_ids)

        output_path = output or self._default_output_path(run)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            self._build_report(run, decisions, articles),
            encoding="utf-8",
        )
        return output_path

    @staticmethod
    async def _get_run(
        repository: SemanticGroupingRepository,
        run_id: str | None,
    ) -> SemanticGroupingRunModel:
        run = (
            await repository.get_run(run_id)
            if run_id is not None
            else await repository.get_latest_run()
        )
        if run is None:
            if run_id is None:
                raise ValueError(
                    "No semantic grouping runs are available."
                )
            raise ValueError(
                f"Semantic grouping run '{run_id}' was not found."
            )
        return run

    def _build_report(
        self,
        run: SemanticGroupingRunModel,
        decisions: list[SemanticGroupingDecisionModel],
        articles: list[ArticleModel],
    ) -> str:
        decisions_by_group = self._group_decisions(decisions)
        articles_by_id = {
            article.id: article
            for article in articles
        }
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
                -len(self._article_ids(item[1])),
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
    def _build_header(
        run: SemanticGroupingRunModel,
        group_count: int,
    ) -> list[str]:
        return [
            "# Semantic grouping export",
            "",
            f"- Run ID: `{run.id}`",
            f"- Created at: {SemanticGroupingExportService._format_datetime(run.created_at)}",
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
        article_ids = self._article_ids(decisions)
        articles = sorted(
            (
                articles_by_id[article_id]
                for article_id in article_ids
                if article_id in articles_by_id
            ),
            key=lambda article: (
                self._as_utc(article.published_at),
                article.id,
            ),
        )
        similarities = [
            decision.similarity
            for decision in decisions
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
                f"{SemanticGroupingExportService._format_datetime(article.published_at)}"
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
    def _article_ids(
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
    def _default_output_path(
        run: SemanticGroupingRunModel,
    ) -> Path:
        created_at = SemanticGroupingExportService._as_utc(
            run.created_at
        )
        timestamp = created_at.strftime("%Y%m%d-%H%M%S")
        return Path("exports") / f"semantic-groups-{timestamp}.md"

    @staticmethod
    def _format_datetime(value: datetime) -> str:
        return SemanticGroupingExportService._as_utc(value).isoformat()

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
