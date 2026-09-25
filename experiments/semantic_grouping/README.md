# Semantic grouping experiment

This experiment evaluates whether article title and RSS summary embeddings
can distinguish articles about the same concrete event from articles that
only share a topic. It does not modify the production pipeline or database.

## Generate candidates

The generator reads active and inactive articles published during the last
seven days. It only pairs articles from different sources, within 72 hours,
and with lexical overlap in the title or summary. A sliding time window and
reservoir sampling avoid materializing every possible pair.

From the `experiments` directory:

```powershell
python -m semantic_grouping.generate_dataset `
  --output semantic_grouping\datasets\candidates.jsonl
```

The default sample targets 75 probable same-event pairs, 100 hard-negative
candidates, and 50 weak/random negatives. Counts and the random seed can be
changed with CLI arguments. Existing files are protected unless `--force`
is supplied.

## Label candidates

```powershell
python -m semantic_grouping.label_dataset `
  --dataset semantic_grouping\datasets\candidates.jsonl
```

Use `s` for the same event, `d` for a different event, `p` to skip, and `q`
to exit. Every `s` or `d` decision is immediately persisted through an
atomic JSONL replacement, and a later run resumes from unlabelled pairs.

## Evaluate a model

Install the optional dependencies:

```powershell
python -m pip install -e ".[semantic-experiments]"
```

Then evaluate a fully labelled dataset:

```powershell
python -m semantic_grouping.evaluate `
  --dataset semantic_grouping\datasets\candidates.jsonl `
  --output semantic_grouping\results\minilm.json
```

The evaluator rejects entries whose `sameEvent` value is still `null`.
