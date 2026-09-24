import re

from app.news_sources.RssNewsSource import RssNewsSource


class RtsNewsSource(RssNewsSource):
    _SOURCE_ID = "rts"
    _DISPLAY_NAME = "RTS"
    _FEED_URL = "https://www.rts.rs/vesti/rss.html"

    @staticmethod
    def _normalize_image_url(url: str) -> str:
        secure_url = re.sub(
            r"^http://(?:www\.)?rts\.rs/",
            "https://www.rts.rs/",
            url,
            flags=re.IGNORECASE,
        )
        normalized_path = secure_url.replace(
            "/upload/thumbnail//",
            "/upload//",
        )
        parent_path, separator, file_name = normalized_path.rpartition("/")
        if separator and parent_path.endswith(f"/{file_name}"):
            return parent_path
        return normalized_path
