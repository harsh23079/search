# Ingesting Your Custom CSV Format

Your CSV has a specific format with these key columns:
- `featured_image` - Image URLs
- `title` - Product names  
- `category` - Categories (e.g., "casual footwear")
- `lowest_price` - Prices
- `brand_name` - Brand names
- Many other metadata columns (tags.visual.*, tags.functional.*, etc.)

## Quick Start

### Using the Custom CLI

```bash
# Basic usage with your CSV format
uv run python cli/ingest_custom.py examples/sample_data.csv

# With custom options
uv run python cli/ingest_custom.py examples/sample_data.csv \
  --image-column featured_image \
  --name-column title \
  --category-column category \
  --price-column lowest_price \
  --brand-column brand_name \
  --batch-size 20 \
  --validate-categories
```

### Using Standard CLI with Column Mapping

```bash
# Specify column names manually
uv run python cli/ingest.py examples/sample_data.csv \
  --image-url-column featured_image \
  --product-name-column title \
  --category-column category
```

## Category Mapping

Your CSV uses categories like:
- `casual footwear` → Automatically mapped to `shoes`
- `formal footwear` → Automatically mapped to `shoes`
- Other categories will be detected from images

The system will:
1. Try to map CSV category to our Category enum
2. Detect actual category from image using YOLOv8
3. Use detected category if confidence > 70%
4. Log all corrections

## Metadata Preservation

All your CSV columns will be preserved as metadata:
- `tags.visual.*` → Stored as nested metadata
- `tags.functional.*` → Stored as nested metadata  
- `tags.usage.*` → Stored as nested metadata
- All other columns → Stored as flat metadata

Example metadata structure:
```json
{
  "product_id": "PROD-ABC123",
  "name": "Yeezy Boost 350 V2 Bone",
  "category": "shoes",
  "price": 6296,
  "brand": "Adidas",
  "tags": {
    "visual": {
      "pattern": "solid",
      "color": {
        "primary": {
          "value": "white"
        }
      }
    },
    "functional": {
      "flexibility_level": "low"
    }
  },
  "sub_category": "Shoes",
  "gender": "male",
  ...
}
```

## Testing

Test with a small subset first:

```bash
# Process only first 10 products
head -11 examples/sample_data.csv > test_sample.csv  # Header + 10 rows
uv run python cli/ingest_custom.py test_sample.csv
```

## Full Example

```bash
# Make sure services are running
devenv up

# In another terminal, ingest your data
uv run python cli/ingest_custom.py examples/sample_data.csv \
  --image-column featured_image \
  --name-column title \
  --category-column category \
  --price-column lowest_price \
  --brand-column brand_name \
  --validate-categories \
  --batch-size 20 \
  --output ingestion_stats.json
```

## Expected Output

```
============================================================
INGESTION STATISTICS
============================================================
Total products:        834
Processed:             834
Successful:            800
Failed:                34
Category corrected:    120  ← Shows wrong categories fixed
Skipped:               0
============================================================
```

## Category Corrections

The system will log corrections like:
```
Category corrected: Yeezy Boost 350 V2 Bone - CSV: casual footwear -> Detected: shoes
Category corrected: Nike Air Max - CSV: apparel -> Detected: shoes
```

## Troubleshooting

### Images Not Downloading
- Check if `featured_image` URLs are accessible
- Verify network connectivity
- Some URLs might require authentication

### Category Detection Issues
- Ensure images clearly show the product
- Check detection model is loaded
- Review confidence scores in logs

### Memory Issues with Large CSV
- Reduce batch size: `--batch-size 5`
- Process in chunks
- Use GPU if available

