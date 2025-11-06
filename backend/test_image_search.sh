#!/bin/bash
# Test script for image similarity search API

API_URL="http://localhost:8000/api/v1/search/similar"
LIMIT=5

echo "🧪 Testing Image Similarity Search API"
echo "========================================"
echo ""

# Test images
IMAGES=(
    "examples/NEED_MONEY_FOR_PORSCHE_2 (1).webp"
    "examples/IMG_6894.webp"
    "examples/02-04-2025-202143-dulopa_photo1.webp"
    "examples/896849_01.jpg.webp"
)

for img in "${IMAGES[@]}"; do
    if [ ! -f "$img" ]; then
        echo "❌ Image not found: $img"
        continue
    fi
    
    echo "📸 Testing: $(basename "$img")"
    echo "----------------------------------------"
    
    response=$(curl -s -X 'POST' \
      "${API_URL}?limit=${LIMIT}" \
      -H 'accept: application/json' \
      -H 'Content-Type: multipart/form-data' \
      -F "file=@${img}")
    
    # Check if request was successful
    if echo "$response" | grep -q '"query_info"'; then
        echo "✅ Success!"
        
        # Extract key information
        detected=$(echo "$response" | grep -o '"detected_items":[0-9]*' | cut -d: -f2)
        matches=$(echo "$response" | grep -o '"total_matches":[0-9]*' | cut -d: -f2)
        category=$(echo "$response" | grep -o '"category":"[^"]*"' | head -1 | cut -d'"' -f4)
        
        echo "   Detected items: ${detected:-0}"
        echo "   Category: ${category:-unknown}"
        echo "   Similar products found: ${matches:-0}"
        
        # Show first product if available
        first_product=$(echo "$response" | grep -o '"name":"[^"]*"' | head -1 | cut -d'"' -f4)
        if [ -n "$first_product" ]; then
            score=$(echo "$response" | grep -o '"similarity_score":[0-9.]*' | head -1 | cut -d: -f2)
            echo "   Top match: ${first_product} (score: ${score})"
        fi
    else
        echo "❌ Error:"
        echo "$response" | head -5
    fi
    
    echo ""
done

echo "✅ Testing complete!"

