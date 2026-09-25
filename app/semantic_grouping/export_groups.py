import argparse
import asyncio
from pathlib import Path

from app.database.session import AsyncSessionFactory
from app.semantic_grouping.services.SemanticGroupingExportService import (
    SemanticGroupingExportService,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export proposed semantic article groups to Markdown."
        )
    )
    parser.add_argument(
        "--run-id",
        help="Export a specific run instead of the latest run.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Output Markdown file. Defaults to "
            "exports\\semantic-groups-<timestamp>.md."
        ),
    )
    return parser.parse_args()


async def export_groups(arguments: argparse.Namespace) -> Path:
    return await SemanticGroupingExportService(
        AsyncSessionFactory
    ).export(
        output=arguments.output,
        run_id=arguments.run_id,
    )


def main() -> None:
    arguments = parse_arguments()
    try:
        output_path = asyncio.run(export_groups(arguments))
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print(f"Semantic groups exported to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
