# Backend — arhitektonski pregled (najviši nivo)

Slojeviti prikaz glavnih komponenti i njihovih zavisnosti. Zavisnosti idu
nadole: API i pozadinski poslovi zavise od domenskih servisa, servisi od
repozitorijuma, repozitorijumi od baze.

```mermaid
flowchart TB
    CLIENT(["Klijent<br/>(Android app)"])

    subgraph L1["Sloj 1 — Ulazne tačke"]
        direction LR
        API["REST API (FastAPI)<br/>/api/articles, /api/article-groups"]
        SCHED["Scheduler<br/>periodični poslovi"]
    end

    subgraph L2["Sloj 2 — Aplikativni servisi"]
        direction LR
        READ["Servisi za čitanje<br/>članci i grupe"]
        INGEST["Prikupljanje vesti<br/>polling + pipeline"]
        GROUPING["Semantičko grupisanje"]
    end

    subgraph L3["Sloj 3 — Domenske sposobnosti"]
        direction LR
        SOURCES["Izvori vesti<br/>INewsSource"]
        TONE["Analiza tona<br/>IToneAnalysisStrategy"]
        EMBED["Embeddinzi i sličnost<br/>IEmbeddingEngine, ICandidatePairFinder"]
    end

    subgraph L4["Sloj 4 — Pristup podacima"]
        direction LR
        REPOS["Repozitorijumi<br/>članci, analize, embeddinzi, grupisanje"]
    end

    subgraph L5["Sloj 5 — Infrastruktura"]
        direction LR
        DB[("PostgreSQL + pgvector")]
        EXT["Spoljni sistemi<br/>RSS feedovi, LLM provajder"]
        CFG["Konfiguracija<br/>Settings"]
    end

    CLIENT --> API
    API --> READ
    SCHED --> INGEST
    SCHED --> GROUPING

    INGEST --> SOURCES
    INGEST --> TONE
    GROUPING --> EMBED

    READ --> REPOS
    INGEST --> REPOS
    GROUPING --> REPOS
    EMBED --> REPOS

    REPOS --> DB
    SOURCES --> EXT
    TONE --> EXT
    CFG -.-> L1
    CFG -.-> L2
    CFG -.-> L3

    classDef entry fill:#eaf4ff,stroke:#3b82c4
    classDef app fill:#eef7ee,stroke:#4c9a4c
    classDef domain fill:#f5f0ff,stroke:#7a5cc4
    classDef data fill:#fff4e6,stroke:#d9822b
    class API,SCHED entry
    class READ,INGEST,GROUPING app
    class SOURCES,TONE,EMBED domain
    class REPOS,DB,EXT,CFG data
```

## Ključne poruke za prezentaciju

- **Dve ulazne tačke**: sinhrona (HTTP zahtevi) i asinhrona (periodični
  poslovi); obe koriste iste domenske servise.
- **Zavisnosti idu samo nadole** — niži slojevi ne znaju za više.
- **Domenske sposobnosti su iza apstrakcija**, pa su implementacije
  zamenljive (izvori vesti, LLM za ton, mehanizam sličnosti).
- **Baza je jedina tačka integracije** između prikupljanja vesti,
  semantičkog grupisanja i API-ja.
- **Konfiguracija** (provajder, model, pragovi, intervali) je izdvojena i
  utiče na sve slojeve bez menjanja koda.
