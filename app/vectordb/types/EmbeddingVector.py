from collections.abc import Sequence
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Float
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.sql.operators import Operators
from sqlalchemy.types import TypeDecorator, TypeEngine

POSTGRESQL_DIALECT_NAME = "postgresql"


class EmbeddingVector(TypeDecorator[list[float]]):
    """Stores embeddings as pgvector values, with a JSON fallback.

    PostgreSQL deployments use the native ``vector`` type so that
    similarity search can be delegated to the database, while other
    dialects keep the same Python representation through JSON.
    """

    impl = JSON
    cache_ok = True

    class Comparator(TypeDecorator.Comparator[Sequence[float]]):
        def cosine_distance(
            self,
            other: object,
        ) -> Operators:
            return self.op("<=>", return_type=Float)(other)

    comparator_factory = Comparator

    def __init__(self, dimensions: int) -> None:
        if dimensions <= 0:
            raise ValueError(
                "Embedding dimensions must be greater than zero."
            )
        super().__init__()
        self.dimensions = dimensions

    def load_dialect_impl(
        self,
        dialect: Dialect,
    ) -> TypeEngine[Any]:
        if dialect.name == POSTGRESQL_DIALECT_NAME:
            return dialect.type_descriptor(Vector(self.dimensions))
        return dialect.type_descriptor(JSON())

    def process_bind_param(
        self,
        value: Sequence[float] | None,
        dialect: Dialect,
    ) -> list[float] | None:
        if value is None:
            return None
        return [float(component) for component in value]

    def process_result_value(
        self,
        value: Sequence[float] | None,
        dialect: Dialect,
    ) -> list[float] | None:
        if value is None:
            return None
        return [float(component) for component in value]
