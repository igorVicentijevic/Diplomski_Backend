from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


def to_camel_case(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(word.capitalize() for word in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel_case,
        populate_by_name=True,
    )


class NewsCategory(StrEnum):
    SERBIA = "SERBIA"
    WORLD = "WORLD"
    TECHNOLOGY = "TECHNOLOGY"
    BUSINESS = "BUSINESS"
    CULTURE = "CULTURE"
    SPORT = "SPORT"
    HEALTH = "HEALTH"


class ArticleResponse(ApiModel):
    id: str
    title: str
    summary: str
    source: str
    category: NewsCategory
    published_at: datetime
    image_url: str | None
    article_url: str
    related_city_ids: list[str]


class ArticleListResponse(ApiModel):
    articles: list[ArticleResponse]
