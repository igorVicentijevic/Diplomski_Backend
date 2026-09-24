from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class ArticleUrlNormalizer:
    def normalize(self, url: str) -> str:
        parsed = urlsplit(url)
        query = [
            (key, value)
            for key, value in parse_qsl(
                parsed.query,
                keep_blank_values=True,
            )
            if not key.casefold().startswith("utm_")
            and key.casefold() not in {"fbclid", "gclid"}
        ]
        path = parsed.path.rstrip("/") or "/"

        return urlunsplit(
            (
                parsed.scheme.casefold(),
                parsed.netloc.casefold(),
                path,
                urlencode(query),
                "",
            )
        )
