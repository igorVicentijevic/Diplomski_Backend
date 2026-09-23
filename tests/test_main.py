from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_articles() -> None:
    response = client.get("/api/v1/articles")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["articles"]) == 2
    assert payload["articles"][0] == {
        "id": "article-1",
        "title": "Prva vest",
        "summary": "Privremeni clanak za prvu iteraciju Articles API-ja.",
        "source": "Demo izvor",
        "category": "SERBIA",
        "publishedAt": "2026-09-23T18:00:00Z",
        "imageUrl": None,
        "articleUrl": "https://example.com/articles/1",
        "relatedCityIds": ["beograd"],
    }


def test_get_article() -> None:
    response = client.get("/api/v1/articles/article-2")

    assert response.status_code == 200
    assert response.json()["id"] == "article-2"


def test_get_missing_article() -> None:
    response = client.get("/api/v1/articles/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Article not found"}
