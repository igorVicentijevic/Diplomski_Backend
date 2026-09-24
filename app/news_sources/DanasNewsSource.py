from app.news_sources.RssNewsSource import RssNewsSource


class DanasNewsSource(RssNewsSource):
    _SOURCE_ID = "danas"
    _DISPLAY_NAME = "Danas"
    _FEED_URL = "https://www.danas.rs/feed/"
