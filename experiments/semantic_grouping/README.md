# Semantic grouping experiment

This package evaluates embedding models and similarity thresholds without
changing the production application or RSS processing pipeline.

## Setup

```powershell
python -m pip install -e ".[dev,semantic-experiments]"
```

The first run downloads the configured model.

## Dataset

Add manually labelled pairs to:

```text
experiments/semantic_grouping/datasets/article_pairs.jsonl
```

Replace the example pairs with real articles before using the reported
threshold for production decisions.

## Run

```powershell
python -m experiments.semantic_grouping.evaluate
```

To save the JSON report:

```powershell
python -m experiments.semantic_grouping.evaluate `
  --output experiments/semantic_grouping/results/minilm.json
```

The command reports cosine similarity for every pair and selects the
threshold with the highest F1 score in the configured range.
