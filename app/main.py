from fastapi import FastAPI

from app.api.routes.articles import router as articles_router

app = FastAPI(
    title="News Aggregator API",
    version="0.1.0",
)
app.include_router(articles_router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello, World!"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
