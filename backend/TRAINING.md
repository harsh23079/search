# Training Data Ingestion Guide

This guide explains how to ingest your custom CSV data into the Fashion AI system, including automatic category validation and correction.

## Overview

The system can ingest products from CSV files with the following features:
- **Automatic category detection** from images using YOLOv8
- **Category validation** - corrects wrong categories (e.g., shoes marked as apparel)
- **Batch processing** for efficient ingestion
- **Duplicate detection** to skip already indexed products
- **Error handling** with detailed statistics

## CSV Format

Your CSV file should contain at minimum:

```csv
image_url,product_name,category,price,brand,currency
https://example.com/image1.jpg,Nike Sneakers,shoes,99.99,Nike,USD
https://example.com/image2.jpg,Blue Jeans,apparel,49.99,Levi's,USD
```

### Required Columns

- **image_url**: URL to product image (or local path)
- **product_name**: Name of the product

### Optional Columns

- **category**: Product category (will be validated/corrected if wrong)
- **price**: Product price
- **brand**: Brand name
- **currency**: Currency code (default: INR)
- Any other metadata columns will be stored as metadata

### Category Validation

The system automatically detects categories from images. If your CSV has wrong categories (e.g., shoes marked as "apparel"), the system will:

1. Detect the actual category from the image
2. Compare with CSV category
3. Use detected category if confidence > 70%
4. Log all corrections for review

## Usage

### Method 1: Using CLI Command

```bash
# Basic usage
uv run python cli/ingest.py data/products.csv

# With custom column names
uv run python cli/ingest.py data/products.csv \
  --image-url-column image_url \
  --product-name-column name \
  --category-column category

# With category validation disabled (use CSV categories as-is)
uv run python cli/ingest.py data/products.csv \
  --no-validate-categories

# Adjust batch size for faster processing
uv run python cli/ingest.py data/products.csv \
  --batch-size 20

# Don't skip existing products (re-index)
uv run python cli/ingest.py data/products.csv \
  --no-skip-existing

# Save statistics to file
uv run python cli/ingest.py data/products.csv \
  --output ingestion_stats.json
```

### Method 2: Using API Endpoint

```bash
# Upload CSV via API
curl -X POST "http://localhost:8000/api/v1/ingest/csv" \
  -F "file=@data/products.csv" \
  -F "validate_categories=true" \
  -F "batch_size=10"
```

### Method 3: Using Python Script

```python
from services.data_ingestion import DataIngestionService

service = DataIngestionService()

stats = service.ingest_from_csv(
    csv_path="data/products.csv",
    image_url_column="image_url",
    product_name_column="product_name",
    category_column="category",
    validate_categories=True,  # Validate/correct categories
    batch_size=10,
    skip_existing=True
)

print(f"Successfully ingested {stats['successful']} products")
print(f"Category corrections: {stats['category_corrected']}")
```

## Category Mapping

The system maps common category names:

| CSV Category | Mapped To |
|-------------|-----------|
| `apparel` | `clothing` |
| `footwear` | `shoes` |
| `handbags` | `bags` |
| `accessory` | `accessories` |

## Example CSV

```csv
image_url,product_name,category,price,brand,currency,description
https://example.com/sneaker1.jpg,Nike Air Max 90,shoes,120.00,Nike,USD,Classic running shoes
https://example.com/jeans1.jpg,Levi's 501 Jeans,apparel,89.99,Levi's,USD,Straight fit jeans
https://example.com/sneaker2.jpg,Adidas Stan Smith,apparel,80.00,Adidas,USD,White sneakers
https://example.com/handbag1.jpg,Coach Leather Handbag,bags,350.00,Coach,USD,Luxury handbag
```

**Note**: The Adidas Stan Smith is marked as "apparel" but will be corrected to "shoes" during ingestion.

## Processing Statistics

After ingestion, you'll get statistics:

```
============================================================
INGESTION STATISTICS
============================================================
Total products:        1000
Processed:             1000
Successful:            950
Failed:                50
Category corrected:    120
Skipped:               0
============================================================
```

## Category Correction Log

The system logs all category corrections:

```
Category corrected: Adidas Stan Smith - CSV: apparel -> Detected: shoes
Category corrected: Nike Running Shoes - CSV: accessories -> Detected: shoes
```

## Troubleshooting

### Images Not Downloading

- Check image URLs are accessible
- Verify network connectivity
- Check for timeout issues (default: 10 seconds)

### Category Detection Issues

- Ensure images are clear and show the product
- Use higher confidence threshold
- Check detection model is loaded correctly

### Slow Processing

- Increase batch size (default: 10)
- Use GPU if available (set `DEVICE=cuda` in config)
- Process in smaller chunks

### Memory Issues

- Reduce batch size
- Process CSV in chunks
- Use smaller image sizes

## Best Practices

1. **Validate CSV before ingestion**
   - Check all required columns exist
   - Verify image URLs are accessible
   - Clean up data (remove duplicates, fix URLs)

2. **Start with small batch**
   - Test with 10-20 products first
   - Verify category corrections are accurate
   - Check embedding quality

3. **Monitor category corrections**
   - Review correction logs
   - Adjust confidence threshold if needed
   - Consider manual review for edge cases

4. **Handle errors gracefully**
   - Use `--skip-existing` to avoid duplicates
   - Save statistics to file for analysis
   - Retry failed products separately

5. **Optimize performance**
   - Use GPU for faster processing
   - Batch process multiple CSVs
   - Use background tasks for large datasets

## Advanced Configuration

### Custom Category Mapping

Edit `services/data_ingestion.py` to add custom category mappings:

```python
category_mapping = {
    "clothing": Category.CLOTHING,
    "apparel": Category.CLOTHING,
    "shoes": Category.SHOES,
    "footwear": Category.SHOES,
    # Add your custom mappings
    "custom_category": Category.CLOTHING,
}
```

### Confidence Threshold

Adjust category correction confidence in `services/data_ingestion.py`:

```python
if validate and csv_category_value != detected_category:
    # Use detected category if confidence is high
    if best_item.confidence > 0.7:  # Adjust threshold
        final_category = detected_category
```

## Next Steps

After ingestion:
1. Test search functionality with ingested products
2. Verify category corrections are accurate
3. Fine-tune detection model if needed
4. Add more products incrementally

