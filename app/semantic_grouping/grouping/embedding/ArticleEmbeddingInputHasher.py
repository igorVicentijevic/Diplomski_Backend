import hashlib


class ArticleEmbeddingInputHasher:
    """Fingerprints the exact text that is fed to the embedding model."""

    def calculate(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
