# Semantic grouping dataset

`article_pairs.jsonl` contains manually labelled article pairs used to
select an embedding model and similarity threshold.

Each line must contain one JSON object:

```json
{
  "id": "pair-001",
  "left": {
    "title": "First article title",
    "summary": "First article summary."
  },
  "right": {
    "title": "Second article title",
    "summary": "Second article summary."
  },
  "sameEvent": true
}
```

`sameEvent` is `true` only when both articles describe the same concrete
event. Articles about the same general subject but different events must
be labelled `false`.

The initial target is at least 50 positive and 50 negative pairs.
