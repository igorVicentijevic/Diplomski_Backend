from app.news_sources.RssNewsSource import RssNewsSource


class PolitikaNewsSource(RssNewsSource):
    _SOURCE_ID = "politika"
    _DISPLAY_NAME = "Politika"
    _FEED_URL = "https://www.politika.rs/rss"
