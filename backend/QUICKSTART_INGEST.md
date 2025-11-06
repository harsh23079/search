# Quick Start: Ingest Your Data

## Using Devenv Tasks

```bash
# Basic ingestion
devenv tasks ingest examples/sample_data.csv
```

## Direct Command (Alternative)

```bash
# Using uv directly
uv run python cli/ingest_custom.py examples/sample_data.csv

# With options
uv run python cli/ingest_custom.py examples/sample_data.csv \
  --batch-size 20 \
  --validate-categories \
  --output stats.json
```

## All Available Options

```bash
uv run python cli/ingest_custom.py examples/sample_data.csv \
  --image-column featured_image \
  --name-column title \
  --category-column category \
  --price-column lowest_price \
  --brand-column brand_name \
  --batch-size 20 \
  --validate-categories \
  --skip-existing \
  --output ingestion_stats.json
```

## Quick Examples

### 1. Basic (Recommended)
```bash
devenv tasks ingest examples/sample_data.csv
```

### 2. Fast Processing
```bash
uv run python cli/ingest_custom.py examples/sample_data.csv --batch-size 50
```

### 3. Test with Small Sample
```bash
head -11 examples/sample_data.csv > test.csv
devenv tasks ingest test.csv
```

### 4. Save Statistics
```bash
uv run python cli/ingest_custom.py examples/sample_data.csv --output stats.json
```

## Prerequisites

Make sure services are running:
```bash
devenv up
```

Then in another terminal:
```bash
devenv tasks ingest examples/sample_data.csv
```

