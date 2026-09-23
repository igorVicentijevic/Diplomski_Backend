from fastapi import APIRouter, HTTPException, status

from app.articles.schemas import ArticleListResponse, ArticleResponse
from app.articles.service import get_article, list_articles

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=ArticleListResponse)
async def get_articles() -> ArticleListResponse:
    return ArticleListResponse(articles=list_articles())


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article_by_id(article_id: str) -> ArticleResponse:
    article = get_article(article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    return article
