#!/bin/bash

# Test script for scraping endpoints using curl

BASE_URL="http://localhost:8000/api/v1"

echo "============================================================"
echo "SCRAPING ENDPOINTS TEST"
echo "============================================================"

# Test 1: Check if backend is running
echo ""
echo "1. Testing Backend Health..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ "$response" == "200" ]; then
    echo "✅ Backend is running!"
else
    echo "❌ Backend is not running. Please start it first."
    exit 1
fi

# Test 2: Instagram scraping
echo ""
echo "============================================================"
echo "2. Testing Instagram Scraping"
echo "============================================================"
echo "Request: POST $BASE_URL/scrape"
echo "Payload: Instagram profile URL"

curl -X POST "$BASE_URL/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.instagram.com/nike/",
    "post_limit": 10,
    "use_api": true
  }' \
  -w "\n\nStatus Code: %{http_code}\n" \
  | python -m json.tool 2>/dev/null || cat

# Test 3: Pinterest scraping
echo ""
echo "============================================================"
echo "3. Testing Pinterest Scraping"
echo "============================================================"
echo "Request: POST $BASE_URL/scrape"
echo "Payload: Pinterest board URL"

curl -X POST "$BASE_URL/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.pinterest.com/pinterest/fashion/",
    "post_limit": 10,
    "use_api": true
  }' \
  -w "\n\nStatus Code: %{http_code}\n" \
  | python -m json.tool 2>/dev/null || cat

# Test 4: Batch scraping
echo ""
echo "============================================================"
echo "4. Testing Batch Scraping"
echo "============================================================"
echo "Request: POST $BASE_URL/scrape/batch"
echo "Payload: Multiple URLs"

curl -X POST "$BASE_URL/scrape/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.instagram.com/nike/",
      "https://www.pinterest.com/pinterest/fashion/"
    ],
    "post_limit": 5,
    "use_api": true
  }' \
  -w "\n\nStatus Code: %{http_code}\n" \
  | python -m json.tool 2>/dev/null || cat

echo ""
echo "============================================================"
echo "Testing Complete!"
echo "============================================================"

