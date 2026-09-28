# Semantičko grupisanje — pregled komponenti (visok nivo)

Napomena: pipeline **ne poziva** `ShadowSemanticGroupingService`. Dva toka su
razdvojena i spojena preko baze — pipeline upisuje članke, a grupisanje na
svom intervalu čita ono što je upisano.

```mermaid
flowchart LR
    subgraph Ingest["Prikupljanje vesti (scheduler: news-refresh)"]
        direction TB
        SRC["Izvori vesti<br/>INewsSource (RSS)"]
        POLL["NewsSourcePollingService<br/>fetch svih feedova"]
        PIPE["NewsArticleProcessingPipeline<br/>normalizacija → dedup → tonska analiza"]
        PERS["ArticlePersistenceService<br/>upsert + deaktivacija"]
        SRC --> POLL --> PIPE --> PERS
    end

    subgraph Store["Baza (PostgreSQL + pgvector)"]
        direction TB
        TA[("articles<br/>+ analize / ton")]
        TE[("article_embeddings")]
        TR[("grouping runs<br/>+ decisions")]
    end

    subgraph Group["Semantičko grupisanje (scheduler: semantic-grouping-shadow)"]
        direction TB
        SHADOW["ShadowSemanticGroupingService<br/>orkestrator run-a"]
        EMB["IArticleEmbeddingProvider<br/>reuse + generisanje vektora"]
        ENGINE["IEmbeddingEngine<br/>SentenceTransformer model"]
        FIND["ICandidatePairFinder<br/>parovi + kosinusna sličnost"]
        DEC["SemanticPairEvaluator<br/>+ ProposedGroupAssigner<br/>prag → grupe"]
        SHADOW --> EMB --> ENGINE
        SHADOW --> FIND
        SHADOW --> DEC
    end

    subgraph Api["API sloj"]
        direction TB
        GSVC["ArticleGroupService<br/>čita poslednji run"]
        EP["GET /api/article-groups"]
        GSVC --> EP
    end

    CLIENT(["Klijent<br/>(Android app)"])

    PERS -->|"upis članaka"| TA
    TA -->|"kandidati u vremenskom prozoru"| SHADOW
    EMB <-->|"čuvanje / ponovna upotreba"| TE
    FIND -->|"pgvector self-join"| TE
    DEC -->|"upis run-a i odluka"| TR
    TR --> GSVC
    TA --> GSVC
    EP --> CLIENT

    classDef store fill:#fff4e6,stroke:#d9822b
    classDef comp fill:#eaf4ff,stroke:#3b82c4
    class TA,TE,TR store
    class SRC,POLL,PIPE,PERS,SHADOW,EMB,ENGINE,FIND,DEC,GSVC,EP comp
```

## Ključne poruke za prezentaciju

- **Razdvojeni tokovi**: prikupljanje vesti i semantičko grupisanje rade na
  zasebnim intervalima; sporo grupisanje ne usporava dohvatanje vesti.
- **Baza kao integraciona tačka**: komponente ne zovu jedna drugu direktno.
- **Apstrakcije**: `INewsSource`, `IArticleEmbeddingProvider`,
  `IEmbeddingEngine`, `ICandidatePairFinder` — zamenljive implementacije
  (npr. pgvector u Postgresu vs. Python fallback).
- **Šta se čuva**: članci + tonska analiza, embeddinzi (keširani po hash-u
  ulaza), i run sa odlukama o parovima i predloženim grupama.
- **API samo čita** rezultat poslednjeg run-a — bez računanja u zahtevu.
