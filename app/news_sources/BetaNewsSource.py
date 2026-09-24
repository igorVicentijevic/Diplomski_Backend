from app.news_sources.RssNewsSource import RssNewsSource


class BetaNewsSource(RssNewsSource):
    _SOURCE_ID = "beta"
    _DISPLAY_NAME = "Beta"
    _FEED_URL = "https://beta.rs/rss"
