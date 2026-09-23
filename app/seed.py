import asyncio

from app.articles.seed import seed_articles
from app.database.session import AsyncSessionFactory


async def main() -> None:
    async with AsyncSessionFactory() as session:
        inserted_count = await seed_articles(session)
    print(f"Inserted {inserted_count} article(s).")


if __name__ == "__main__":
    asyncio.run(main())
