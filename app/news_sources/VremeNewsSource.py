from app.news_sources.RssNewsSource import RssNewsSource


class VremeNewsSource(RssNewsSource):
    _SOURCE_ID = "vreme"
    _DISPLAY_NAME = "Vreme"
    _FEED_URL = "https://www.vreme.com/feed/"
