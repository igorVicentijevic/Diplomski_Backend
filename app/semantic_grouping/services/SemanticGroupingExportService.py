from datetime import UTC
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.semantic_grouping.exporting.SemanticGroupingReportBuilder import (
    SemanticGroupingReportBuilder,
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
        self._report_builder = SemanticGroupingReportBuilder()

    async def export(
        self,
        output: Path | None = None,
        run_id: str | None = None,
    ) -> Path:
        async with self._session_factory() as session:
            repository = SemanticGroupingRepository(session)
            run = await self._get_run(repository, run_id)
            decisions = await repository.list_grouped_decisions(run.id)
            articles = await repository.list_articles_by_ids(
                self._report_builder.article_ids(decisions)
            )

        output_path = output or self._default_output_path(run)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            self._report_builder.build(run, decisions, articles),
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

    @staticmethod
    def _default_output_path(
        run: SemanticGroupingRunModel,
    ) -> Path:
        created_at = run.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        else:
            created_at = created_at.astimezone(UTC)
        timestamp = created_at.strftime("%Y%m%d-%H%M%S")
        return Path("exports") / f"semantic-groups-{timestamp}.md"
