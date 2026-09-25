# Semantic grouping dataset

`candidates.jsonl` is the working file used for manual labelling.
`article_pairs_v1.jsonl` is the frozen, labelled-only snapshot used for the
first model comparison. Each line is one JSON object:

```json
{
  "id": "pair-123",
  "left": {
    "articleId": "article-1",
    "title": "Naslov",
    "summary": "Sažetak",
    "source": "RTS",
    "publishedAt": "2026-09-25T18:00:00+00:00"
  },
  "right": {
    "articleId": "article-2",
    "title": "Drugi naslov",
    "summary": "Drugi sažetak",
    "source": "N1",
    "publishedAt": "2026-09-25T19:00:00+00:00"
  },
  "sameEvent": null,
  "candidateType": "hard_negative"
}
```

`sameEvent` is `true` only when both articles describe the same concrete
event, `false` when they do not, and `null` while the pair is waiting for
manual labelling. `candidateType` records the generator stratum and is not
a ground-truth label.

The v1 snapshot is preliminary because it contains 11 positive and 98
negative pairs. At least half of the negative pairs are hard negatives:
semantically related articles about different concrete events. Model
selection and thresholds must be recalculated after collecting more positive
examples.
