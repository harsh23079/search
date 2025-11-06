# Data Ingestion Commands

## Using Devenv CLI

### Quick Ingest (Recommended)

```bash
# Basic ingestion
devenv run ingest examples/sample_data.csv

# With custom options
devenv run ingest-custom examples/sample_data.csv --batch-size 20 --validate-categories
```

### All Available Options

```bash
devenv run ingest-custom examples/sample_data.csv \
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

## Direct Python CLI

```bash
# Using uv directly
uv run python cli/ingest_custom.py examples/sample_data.csv

# With all options
uv run python cli/ingest_custom.py examples/sample_data.csv \
  --image-column featured_image \
  --name-column title \
  --category-column category \
  --price-column lowest_price \
  --brand-column brand_name \
  --batch-size 20 \
  --validate-categories
```

## Examples

### 1. Basic Ingestion
```bash
devenv run ingest examples/sample_data.csv
```

### 2. Fast Processing (Larger Batch)
```bash
devenv run ingest-custom examples/sample_data.csv --batch-size 50
```

### 3. Without Category Validation
```bash
devenv run ingest-custom examples/sample_data.csv --no-validate-categories
```

### 4. Save Statistics
```bash
devenv run ingest-custom examples/sample_data.csv --output stats.json
```

### 5. Test with Small Sample
```bash
# Create test file first
head -11 examples/sample_data.csv > test_sample.csv
devenv run ingest test_sample.csv
```

## Column Mapping

Your CSV uses these columns (automatically detected):
- `featured_image` - Image URLs
- `title` - Product names
- `category` - Categories (will be validated/corrected)
- `lowest_price` - Prices
- `brand_name` - Brand names

If your CSV uses different column names:
```bash
devenv run ingest-custom your_file.csv \
  --image-column image_url \
  --name-column product_name \
  --category-column category
```

## What Happens

1. **Category Detection**: Automatically detects category from images
2. **Category Correction**: Fixes wrong categories (e.g., "casual footwear" → "shoes")
3. **Embedding Generation**: Creates FashionCLIP embeddings for each product
4. **Indexing**: Stores products in Qdrant vector database
5. **Statistics**: Shows ingestion results and corrections

## Expected Output

```
============================================================
INGESTION STATISTICS
============================================================
Total products:        834
Processed:             834
Successful:            800
Failed:                34
Category corrected:    120
Skipped:               0
============================================================
```

## Troubleshooting

### CSV Not Found
```bash
# Check file exists
ls -lh examples/sample_data.csv

# Use full path if needed
devenv run ingest /full/path/to/data.csv
```

### Services Not Running
```bash
# Make sure services are up
devenv up

# Check Qdrant
curl http://localhost:6333/health

# Check FastAPI
curl http://localhost:8000/api/v1/health
```

### Memory Issues
```bash
# Reduce batch size
devenv run ingest-custom examples/sample_data.csv --batch-size 5
```

