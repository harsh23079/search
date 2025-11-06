# Inspecting Ingested Data

## Quick Commands

### Check Total Count
```bash
uv run python cli/inspect_db.py --count
```

### Show Statistics
```bash
uv run python cli/inspect_db.py --stats
```

### List Products
```bash
# List first 10 products
uv run python cli/inspect_db.py --list

# List more products
uv run python cli/inspect_db.py --list --limit 50
```

### Search Products
```bash
# Search by name
uv run python cli/inspect_db.py --search "Nike"

# Search with limit
uv run python cli/inspect_db.py --search "Yeezy" --limit 5
```

### Filter by Category
```bash
# Show only shoes
uv run python cli/inspect_db.py --category shoes

# Show only clothing
uv run python cli/inspect_db.py --category clothing
```

### Get Specific Product
```bash
uv run python cli/inspect_db.py --product-id PROD-ABC123
```

### JSON Output
```bash
# Get data as JSON
uv run python cli/inspect_db.py --stats --json
uv run python cli/inspect_db.py --list --json
```

## Examples

### 1. Quick Check
```bash
# See how many products you have
uv run python cli/inspect_db.py --count
```

### 2. Overview
```bash
# Get statistics about your data
uv run python cli/inspect_db.py --stats
```

### 3. Browse Products
```bash
# List first 20 products
uv run python cli/inspect_db.py --list --limit 20
```

### 4. Find Specific Brand
```bash
# Find all Adidas products
uv run python cli/inspect_db.py --search "Adidas"
```

### 5. Check Category Distribution
```bash
# See all shoes
uv run python cli/inspect_db.py --category shoes --limit 50
```

## Using Qdrant Dashboard

You can also use the Qdrant web dashboard:

1. Open: http://localhost:6333/dashboard
2. Select collection: `fashion_products`
3. Browse products, search, and filter

## API Endpoint

You can also query via the API once products are ingested:

```bash
# Search for similar products (after ingestion)
curl -X POST "http://localhost:8000/api/v1/search/similar" \
  -F "file=@your_image.jpg"
```

## Devenv Task

You can also add this as a devenv task:

```bash
# Add to devenv.nix tasks section if needed
devenv tasks run inspect  # (if you add it)
```

