# Dohvatanje semantičkih grupa preko API-ja

Sekvencijalni dijagram obrade HTTP zahteva `GET /api/article-groups`.
Grupe se ne računaju tokom zahteva — čitaju se rezultati poslednjeg
shadow grouping run-a koji periodično upisuje `ShadowSemanticGroupingService`.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Klijent (Android app)
    participant API as FastAPI app
    participant Route as article_groups.py ruter<br/>get_article_groups()
    participant Svc as ArticleGroupService
    participant Repo as SemanticGroupingRepository
    participant DB as PostgreSQL
    participant Collector as ProposedArticleGroupCollector
    participant Builder as ArticleGroupResponseBuilder
    participant Schema as ArticleGroupResponse /<br/>ArticleGroupListResponse

    Client->>API: GET /api/article-groups
    API->>Route: get_article_groups(service)
    Note over Route,Repo: ArticleGroupService i SemanticGroupingRepository<br/>dobijaju se injekcijom, sa AsyncSession vezanom za zahtev

    Route->>Svc: list_groups()

    Svc->>Repo: get_latest_run()
    Repo->>DB: SELECT semantic_grouping_runs<br/>ORDER BY created_at DESC LIMIT 1
    DB-->>Repo: poslednji run | None
    Repo-->>Svc: SemanticGroupingRunModel | None

    alt nijedan run još nije izvršen
        Svc-->>Route: []
        Route-->>Client: 200 OK sa {"groups": []}
    else postoji poslednji run
        Svc->>Repo: list_grouped_decisions(run.id)
        Repo->>DB: SELECT decisions<br/>WHERE run_id = ? AND proposed_group_id IS NOT NULL<br/>ORDER BY proposed_group_id, similarity DESC
        DB-->>Repo: odluke o parovima
        Repo-->>Svc: list[SemanticGroupingDecisionModel]

        Svc->>Collector: collect(decisions)
        Collector->>Collector: grupiši left/right article_id<br/>po proposed_group_id
        Collector-->>Svc: list[ProposedArticleGroup]

        Svc->>Repo: list_active_analyzed_articles_by_ids(article_ids)
        Repo->>DB: SELECT articles<br/>JOIN analysis JOIN tone<br/>WHERE id IN (...) AND is_active = True<br/>(selectinload analysis→tone)
        DB-->>Repo: aktivni članci sa analizom
        Repo-->>Svc: list[ArticleModel]
        Note right of Repo: deaktivirani članci (nestali iz feeda)<br/>ispadaju iz grupa

        Svc->>Builder: build(proposed_groups, articles)
        loop za svaku predloženu grupu
            Builder->>Schema: ArticleService.to_response(article) po članku
            Builder->>Builder: sortiraj članke po published_at DESC
        end
        Builder->>Builder: zadrži samo grupe sa >= 2 članka<br/>i sortiraj grupe po najnovijem članku
        Builder-->>Svc: list[ArticleGroupResponse]

        Svc-->>Route: list[ArticleGroupResponse]
        Route->>Schema: ArticleGroupListResponse(groups=[...])
        Route-->>API: ArticleGroupListResponse
        API-->>Client: 200 OK + JSON {"groups": [...]}
    end
```
