import hashlib
import json

from app.news_sources.models.NewsArticle import NewsArticle


class ToneAnalysisInputHasher:
    def calculate(self, article: NewsArticle) -> str:
        serialized_input = json.dumps(
            {
                "summary": article.summary.strip(),
                "title": article.title.strip(),
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        return hashlib.sha256(
            serialized_input.encode("utf-8")
        ).hexdigest()
