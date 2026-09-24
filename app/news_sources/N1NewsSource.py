from app.news_sources.RssNewsSource import RssNewsSource


class N1NewsSource(RssNewsSource):
    _SOURCE_ID = "n1"
    _DISPLAY_NAME = "N1 Srbija"
    _FEED_URL = "https://n1info.rs/feed/"
