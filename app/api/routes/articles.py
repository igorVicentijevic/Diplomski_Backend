from fastapi import APIRouter, HTTPException, status

from app.articles.dependencies import ArticleServiceDependency
from app.articles.schemas.ArticleListResponse import ArticleListResponse
from app.articles.schemas.ArticleResponse import ArticleResponse

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=ArticleListResponse)
async def get_articles(
    article_service: ArticleServiceDependency,
) -> ArticleListResponse:

    articles = await article_service.list_articles() 

    return ArticleListResponse(
        articles=articles
    )


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article_by_id(
    article_id: str,
    article_service: ArticleServiceDependency,
) -> ArticleResponse:
    #database query to get the article by ID
    article = await article_service.get_article(article_id)
    
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    
    return article
