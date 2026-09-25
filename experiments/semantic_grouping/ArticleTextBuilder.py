class ArticleTextBuilder:
    def build(
        self,
        title: str,
        summary: str,
    ) -> str:
        
        normalized_title = " ".join(title.split())
        normalized_summary = " ".join(summary.split())

        if not normalized_title and not normalized_summary:
            raise ValueError(
                "Article title and summary must not both be empty."
            )

        return (
            f"Title: {normalized_title}\n"
            f"Summary: {normalized_summary}"
        )
