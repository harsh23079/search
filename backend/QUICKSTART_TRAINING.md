# Quick Start: Training on Your Data

## Step 1: Prepare Your CSV

Your CSV should have at least these columns:
- `image_url` - URL to product image
- `product_name` - Name of the product
- `category` - Category (will be auto-corrected if wrong)

Example:
```csv
image_url,product_name,category,price,brand
https://example.com/sneaker.jpg,Nike Air Max,shoes,120,Nike
https://example.com/jeans.jpg,Levi's 501,apparel,89,Levi's
```

## Step 2: Run Ingestion

### Using CLI (Recommended)

```bash
# Make sure Qdrant is running first
devenv up

# In another terminal, run ingestion
uv run python cli/ingest.py your_data.csv

# With custom column names
uv run python cli/ingest.py your_data.csv \
  --image-url-column image_url \
  --product-name-column name \
  --category-column category
```

### Using API

```bash
curl -X POST "http://localhost:8000/api/v1/ingest/csv" \
  -F "file=@your_data.csv"
```

## Step 3: Verify

Check the ingestion statistics - it will show:
- How many products were successfully indexed
- How many categories were corrected (e.g., shoes marked as apparel)
- Any errors that occurred

## Category Auto-Correction

The system automatically:
1. Detects category from image using YOLOv8
2. Compares with CSV category
3. Uses detected category if confidence > 70%
4. Logs all corrections

Example output:
```
Category corrected: Nike Air Max - CSV: apparel -> Detected: shoes
```

## That's It!

Your products are now indexed and ready for search. Try:
- Search similar products via API
- Test outfit recommendations
- Verify category corrections

For more details, see [TRAINING.md](TRAINING.md)

