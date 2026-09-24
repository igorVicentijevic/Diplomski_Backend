from app.news_sources.RssNewsSource import RssNewsSource


class JuzneVestiNewsSource(RssNewsSource):
    _SOURCE_ID = "juzne-vesti"
    _DISPLAY_NAME = "Južne vesti"
    _FEED_URL = "https://www.juznevesti.com/feed/"
