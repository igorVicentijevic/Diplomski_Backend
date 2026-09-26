from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ArticleEmbedding:
    article_id: str
    input_hash: str
    vector: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.article_id:
            raise ValueError("Article identifier must not be empty.")
        if not self.input_hash:
            raise ValueError("Embedding input hash must not be empty.")
        if not self.vector:
            raise ValueError("Embedding vector must not be empty.")
