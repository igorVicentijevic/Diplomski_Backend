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

## Freeze the labelled evaluation dataset

Create an immutable evaluation snapshot from the labelled entries while
leaving unlabelled candidates in the working file:

```powershell
python -m semantic_grouping.prepare_evaluation_dataset
```

The command creates `datasets\article_pairs_v1.jsonl`, refuses to replace
it unless `--force` is explicitly supplied, and prints positive, negative,
hard-negative, and excluded counts.

## Compare embedding models

Install the optional dependencies:

```powershell
python -m pip install -e ".[semantic-experiments]"
```

Then compare at least two models on the same frozen dataset:

```powershell
python -m semantic_grouping.compare_models
```

The benchmark uses the same article text, grouped folds, cosine similarity,
and threshold range for every model. Pairs connected through a shared article
remain in the same fold to prevent text leakage. Thresholds are selected on
four folds and evaluated on the held-out fold.

The generated `results\model_comparison_v1.json` contains per-fold and
aggregate precision, recall, F1, PR-AUC, confusion counts, threshold
statistics, hard-negative results, every pair similarity, false positives,
false negatives, and embedding generation time.

The v1 result and its thresholds are preliminary because the frozen dataset
contains only 11 positive and 98 negative pairs. The current shared-article
graph has fewer positive components than folds, so leakage-safe stratification
cannot put a positive example in every test fold; this limitation is recorded
in the report. Re-run the benchmark after collecting more positive examples.
