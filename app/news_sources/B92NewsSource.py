from app.news_sources.RssNewsSource import RssNewsSource


class B92NewsSource(RssNewsSource):
    _SOURCE_ID = "b92"
    _DISPLAY_NAME = "B92"
    _FEED_URL = "https://www.b92.net/info/rss/vesti.xml"
