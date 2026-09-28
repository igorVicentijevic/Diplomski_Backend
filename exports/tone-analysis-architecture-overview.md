# Analiza tona — pregled komponenti (visok nivo)

Tok od RSS fetch-a do upisane tonske analize, apstrahovan na glavne
komponente u interakciji.

```mermaid
flowchart LR
    subgraph Ingest["Prikupljanje (scheduler: news-refresh)"]
        direction TB
        SRC["Izvori vesti<br/>INewsSource (RSS)"]
        POLL["NewsSourcePollingService"]
        SRC --> POLL
    end

    subgraph Pipe["NewsArticleProcessingPipeline"]
        direction TB
        NORM["UrlNormalizationStep<br/>+ ArticleDeduplicationStep"]
        EXIST["ExistingToneAnalysisStep<br/>keš po input_hash / model / prompt"]
        STEP["ToneAnalysisStep<br/>ograničena paralelnost"]
        NORM --> EXIST --> STEP
    end

    subgraph Tone["Tonska analiza"]
        direction TB
        FACTORY["ToneAnalysisStrategyFactory<br/>(prema konfiguraciji)"]
        STRAT["IToneAnalysisStrategy"]
        LLM["LlmToneAnalysisStrategy<br/>+ IToneAnalysisLlmClient (Groq)"]
        RAND["RandomToneAnalysisStrategy<br/>(razvoj / test)"]
        FACTORY --> STRAT
        STRAT --> LLM
        STRAT --> RAND
    end

    PERS["ArticlePersistenceService"]
    DB[("PostgreSQL<br/>articles + analize / ton")]
    API["GET /api/articles<br/>ArticleService"]
    CLIENT(["Klijent (Android app)"])

    POLL -->|"NewsArticle"| NORM
    EXIST <-->|"postojeća analiza"| DB
    STEP -->|"samo članci bez validne analize"| STRAT
    LLM -->|"procenti negativno / pozitivno / neutralno"| STEP
    RAND --> STEP
    STEP -->|"ArticleProcessingContext + ton"| PERS
    PERS -->|"upsert članka i analize"| DB
    DB --> API --> CLIENT

    classDef store fill:#fff4e6,stroke:#d9822b
    classDef comp fill:#eaf4ff,stroke:#3b82c4
    class DB store
    class SRC,POLL,NORM,EXIST,STEP,FACTORY,STRAT,LLM,RAND,PERS,API comp
```

## Ključne poruke za prezentaciju

- **Analiza se ne ponavlja bez potrebe**: `ExistingToneAnalysisStep` po
  `input_hash`-u (naslov + sažetak) i po provajderu/modelu/verziji prompta
  odlučuje da li se postojeći rezultat može ponovo iskoristiti.
- **Strategija je zamenljiva**: `IToneAnalysisStrategy` — LLM (Groq) u
  produkciji, `Random` za razvoj; bira je fabrika iz konfiguracije.
- **Otpornost**: neuspela analiza jednog članka ne ruši ceo feed — članak se
  preskače pri upisu i pokušava se ponovo u sledećem ciklusu.
- **Performanse**: pozivi modela idu paralelno uz ograničenje broja
  istovremenih zahteva (semafor).
- **Normalizacija rezultata**: procenti se skaliraju da u zbiru daju 100%.
