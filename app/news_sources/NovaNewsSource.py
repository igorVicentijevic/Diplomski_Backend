from app.news_sources.RssNewsSource import RssNewsSource


class NovaNewsSource(RssNewsSource):
    _SOURCE_ID = "nova"
    _DISPLAY_NAME = "Nova.rs"
    _FEED_URL = "https://nova.rs/feed/"
