# Text Search: BM25 + Sentence-Transformers

Hybrid text search implementation combining BM25 (keyword-based) and Sentence-Transformers (semantic search) for contextual understanding.

## Overview

The text search service provides a powerful hybrid search that combines:

1. **BM25** (Best Matching 25) - Fast keyword-based search
   - Excellent for exact matches (brand names, product names, SKUs)
   - Fast and efficient for keyword queries
   - Weight: 40% by default

2. **Sentence-Transformers** - Semantic/contextual search
   - Understands meaning and context
   - Handles synonyms and related concepts
   - Weight: 60% by default

## API Endpoint

### POST `/api/v1/search/text`

Search products using natural language text queries.

**Request Body:**
```json
{
  "query": "Nike sneakers",
  "limit": 10,
  "category": "shoes",
  "bm25_weight": 0.4,
  "semantic_weight": 0.6,
  "min_score": 0.3
}
```

**Parameters:**
- `query` (required): Search query text
- `limit` (optional, default: 10): Maximum number of results (1-100)
- `category` (optional): Filter by category (clothing, shoes, bags, accessories)
- `bm25_weight` (optional, default: 0.4): Weight for BM25 keyword search (0.0-1.0)
- `semantic_weight` (optional, default: 0.6): Weight for semantic search (0.0-1.0)
- `min_score` (optional, default: 0.3): Minimum similarity score threshold (0.0-1.0)

**Response:**
```json
{
  "query": "Nike sneakers",
  "results": [
    {
      "product_id": "uuid-here",
      "similarity_score": 0.85,
      "product_info": {
        "product_id": "uuid-here",
        "name": "Nike Air Max 90",
        "brand": "Nike",
        "price": 120.00,
        "currency": "INR",
        "image_url": "https://...",
        "in_stock": true
      },
      "match_reasoning": "Matched by: brand match, product name match, high semantic similarity (score: 85.00%)",
      "key_similarities": [
        "Name: Nike Air Max 90",
        "Brand: Nike"
      ]
    }
  ],
  "total_matches": 5,
  "returned_count": 5,
  "search_method": "hybrid_bm25_semantic",
  "bm25_weight": 0.4,
  "semantic_weight": 0.6,
  "processing_time_ms": 125.5
}
```

## Example Queries

### Keyword Queries (BM25 excels)
- `"Nike"` - Exact brand match
- `"Yeezy Boost 350"` - Exact product name
- `"Air Jordan 1"` - Specific model

### Semantic Queries (Sentence-Transformers excels)
- `"running shoes"` - Finds sneakers, trainers, athletic footwear
- `"casual footwear"` - Finds casual shoes, sneakers, etc.
- `"red sneakers"` - Finds red shoes, red trainers, red athletic footwear

### Hybrid Queries (Both methods work)
- `"Nike running shoes"` - Combines brand (BM25) + category (semantic)
- `"Adidas Yeezy"` - Brand + product name
- `"red Nike sneakers"` - Color + brand + category

## Usage Examples

### Python
```python
import requests

# Search for Nike sneakers
response = requests.post(
    "http://localhost:8000/api/v1/search/text",
    json={
        "query": "Nike sneakers",
        "limit": 10,
        "category": "shoes"
    }
)

results = response.json()
for product in results["results"]:
    print(f"{product['product_info']['name']} - {product['similarity_score']:.2%}")
```

### cURL
```bash
curl -X POST "http://localhost:8000/api/v1/search/text" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Nike sneakers",
    "limit": 10,
    "category": "shoes"
  }'
```

### JavaScript/TypeScript
```javascript
const response = await fetch('http://localhost:8000/api/v1/search/text', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Nike sneakers',
    limit: 10,
    category: 'shoes'
  })
});

const results = await response.json();
console.log(results);
```

## Tuning Weights

Adjust the weights based on your use case:

### Keyword-Heavy (More BM25)
```json
{
  "query": "Nike Air Max",
  "bm25_weight": 0.7,
  "semantic_weight": 0.3
}
```
Best for: Exact product names, SKUs, brand searches

### Semantic-Heavy (More Sentence-Transformers)
```json
{
  "query": "comfortable running shoes",
  "bm25_weight": 0.2,
  "semantic_weight": 0.8
}
```
Best for: Natural language queries, descriptions, style searches

### Balanced (Default)
```json
{
  "query": "Nike running shoes",
  "bm25_weight": 0.4,
  "semantic_weight": 0.6
}
```
Best for: General searches combining brands/products with descriptions

## How It Works

1. **BM25 Scoring**: 
   - Tokenizes query and product texts
   - Computes BM25 relevance scores
   - Normalizes to [0, 1] range

2. **Semantic Scoring**:
   - Encodes query using Sentence-Transformer model (`all-MiniLM-L6-v2`)
   - Encodes all product texts
   - Computes cosine similarity
   - Normalizes to [0, 1] range

3. **Score Combination**:
   - Weighted combination: `final_score = (bm25_weight × bm25_score) + (semantic_weight × semantic_score)`
   - Sorts by combined score
   - Filters by minimum score threshold
   - Applies category filter if specified

4. **Index Building**:
   - Automatically builds BM25 index from all products in Qdrant
   - Index is built on service initialization
   - Can be refreshed manually: `text_search_service.refresh_indices()`

## Searchable Fields

The search indexes the following product metadata:
- Product name
- Brand name
- Category and subcategory
- Colors
- Style tags
- Description (if available)
- Model name
- Colorways
- Product type
- Gender

## Performance

- **BM25**: Very fast (< 10ms for most queries)
- **Semantic**: Moderate speed (100-500ms depending on corpus size)
- **Combined**: Typically 150-600ms for full hybrid search
- **Index Building**: One-time cost on startup or refresh

## Notes

- The Sentence-Transformer model (`all-MiniLM-L6-v2`) is loaded on service initialization
- BM25 index is built from all products in Qdrant on startup
- Indices are automatically refreshed if empty on first search
- For large datasets (>10k products), consider caching or incremental updates

## Integration

The text search service is automatically integrated with:
- FastAPI routes (`/api/v1/search/text`)
- Product ingestion (indices refresh after new products added)
- Qdrant vector database (reads product metadata)

## Future Enhancements

- [ ] Caching for frequent queries
- [ ] Incremental index updates
- [ ] Multiple model support
- [ ] Query expansion
- [ ] Faceted search
- [ ] Typo tolerance

