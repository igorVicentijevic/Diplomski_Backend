from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ArticleEmbeddingRequest:
    article_id: str
    text: str
    input_hash: str

    def __post_init__(self) -> None:
        if not self.article_id:
            raise ValueError("Article identifier must not be empty.")
        if not self.text.strip():
            raise ValueError("Embedding input text must not be empty.")
        if not self.input_hash:
            raise ValueError("Embedding input hash must not be empty.")
