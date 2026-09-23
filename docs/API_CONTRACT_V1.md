# News Aggregator API v1

Ovaj dokument opisuje HTTP ugovor izmedju backend-a i klijentskih
aplikacija.

**Status:** razvojna verzija  
**Poslednje azuriranje:** 2026-09-23  
**Base URL za lokalni razvoj:** `http://127.0.0.1:8000`  
**API prefiks:** `/api`

Interaktivna Swagger dokumentacija dostupna je na `/docs`, a OpenAPI
specifikacija na `/openapi.json`.

## Opsta pravila

- Svi odgovori koriste JSON.
- Nazivi JSON polja koriste `camelCase`.
- Datumi koriste ISO 8601 format sa vremenskom zonom.
- Trenutni odgovori koriste UTC oznaku `Z`.
- Identifikator clanka je neproziran string. Klijent ne treba da tumaci
  njegov format.
- Autentifikacija trenutno nije potrebna.
- Paginacija i inkrementalna sinhronizacija jos nisu deo v1 ugovora.

## Model: Article

| Polje | Tip | Null | Opis |
|---|---|---:|---|
| `id` | string | ne | Stabilni identifikator clanka. |
| `title` | string | ne | Naslov clanka. |
| `summary` | string | ne | Ociscen tekstualni sazetak. |
| `source` | string | ne | Naziv izvora vesti. |
| `category` | string enum | ne | Kategorija clanka. |
| `publishedAt` | ISO 8601 datetime | ne | Vreme objavljivanja clanka. |
| `imageUrl` | string | da | URL glavne slike ili `null`. |
| `articleUrl` | string | ne | URL originalnog clanka. |
| `relatedCityIds` | array of string | ne | Identifikatori povezanih gradova; moze biti prazna lista. |

Dozvoljene vrednosti polja `category`:

```text
SERBIA
WORLD
TECHNOLOGY
BUSINESS
CULTURE
SPORT
HEALTH
```

Primer:

```json
{
  "id": "article-1",
  "title": "Prva vest",
  "summary": "Privremeni clanak za prvu iteraciju Articles API-ja.",
  "source": "Demo izvor",
  "category": "SERBIA",
  "publishedAt": "2026-09-23T18:00:00Z",
  "imageUrl": null,
  "articleUrl": "https://example.com/articles/1",
  "relatedCityIds": [
    "beograd"
  ]
}
```

## GET /api/articles

Vraca sve trenutno dostupne clanke.

### Request

Nema query parametara ni request body-ja.

```http
GET /api/articles
Accept: application/json
```

### Response: 200 OK

```json
{
  "articles": [
    {
      "id": "article-1",
      "title": "Prva vest",
      "summary": "Privremeni clanak za prvu iteraciju Articles API-ja.",
      "source": "Demo izvor",
      "category": "SERBIA",
      "publishedAt": "2026-09-23T18:00:00Z",
      "imageUrl": null,
      "articleUrl": "https://example.com/articles/1",
      "relatedCityIds": [
        "beograd"
      ]
    }
  ]
}
```

Lista `articles` je uvek prisutna. Kada nema clanaka, vrednost je prazna
lista:

```json
{
  "articles": []
}
```

## GET /api/articles/{articleId}

Vraca jedan clanak na osnovu identifikatora.

### Path parametri

| Parametar | Tip | Opis |
|---|---|---|
| `articleId` | string | Identifikator dobijen iz Article modela. |

### Request

```http
GET /api/articles/article-1
Accept: application/json
```

### Response: 200 OK

Response body je jedan `Article` objekat.

```json
{
  "id": "article-1",
  "title": "Prva vest",
  "summary": "Privremeni clanak za prvu iteraciju Articles API-ja.",
  "source": "Demo izvor",
  "category": "SERBIA",
  "publishedAt": "2026-09-23T18:00:00Z",
  "imageUrl": null,
  "articleUrl": "https://example.com/articles/1",
  "relatedCityIds": [
    "beograd"
  ]
}
```

### Response: 404 Not Found

```json
{
  "detail": "Article not found"
}
```

## Pomocni endpointi

### GET /health

Koristi se za proveru dostupnosti backend-a.

```json
{
  "status": "ok"
}
```

### GET /

Osnovni Hello World endpoint. Nije deo funkcionalnog ugovora Android
aplikacije.

```json
{
  "message": "Hello, World!"
}
```

## Kotlin DTO primer

Ovo je ilustracija mapiranja trenutnog ugovora. Klijent moze koristiti
drugu biblioteku ili nazive klasa, ali JSON polja i tipovi moraju ostati
kompatibilni.

```kotlin
data class ArticleListResponseDto(
    val articles: List<ArticleDto>,
)

data class ArticleDto(
    val id: String,
    val title: String,
    val summary: String,
    val source: String,
    val category: NewsCategoryDto,
    val publishedAt: String,
    val imageUrl: String?,
    val articleUrl: String,
    val relatedCityIds: List<String>,
)

enum class NewsCategoryDto {
    SERBIA,
    WORLD,
    TECHNOLOGY,
    BUSINESS,
    CULTURE,
    SPORT,
    HEALTH,
}
```

Klijent treba da parsira `publishedAt` kao datum sa vremenskom zonom, a
ne kao lokalno vreme uredjaja.

## Verzije i izmene ugovora

- Kompatibilna polja mogu biti dodata u postojece odgovore.
- Klijent ne treba da zavisi od redosleda JSON polja.
- Uklanjanje polja, promena tipa ili promena znacenja zahteva novu verziju
  ugovora i koordinisanu migraciju klijenta.
- Ovaj dokument mora biti azuriran zajedno sa promenom ruta ili Pydantic
  response modela.
