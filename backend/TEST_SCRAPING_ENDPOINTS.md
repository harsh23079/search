# How to Test Scraping Endpoints

## Prerequisites

1. **Backend must be running**
   ```powershell
   docker-compose up -d
   ```

2. **APIFY_TOKEN must be set**
   - Create a `.env` file in the project root with:
     ```
     APIFY_TOKEN=your_apify_token_here
     ```
   - Or set it as environment variable in docker-compose.yml
   - Get your token from: https://console.apify.com/account/integrations

## Method 1: Using API Documentation (Easiest)

1. Open your browser and go to: **http://localhost:8000/docs**

2. Find the **"scraping"** section in the API docs

3. Click on **POST /api/v1/scrape** to expand it

4. Click **"Try it out"** button

5. Enter the request body:
   ```json
   {
     "url": "https://www.instagram.com/nike/",
     "post_limit": 10,
     "use_api": true
   }
   ```

6. Click **"Execute"** to test

## Method 2: Using PowerShell (Windows)

### Test Single Scrape (Instagram)
```powershell
$body = @{
    url = "https://www.instagram.com/nike/"
    post_limit = 10
    use_api = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scrape" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

### Test Single Scrape (Pinterest)
```powershell
$body = @{
    url = "https://www.pinterest.com/pinterest/fashion/"
    post_limit = 10
    use_api = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scrape" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

### Test Batch Scrape
```powershell
$body = @{
    urls = @(
        "https://www.instagram.com/nike/",
        "https://www.pinterest.com/pinterest/fashion/"
    )
    post_limit = 5
    use_api = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scrape/batch" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

### Or use the test script:
```powershell
.\test_scraping.ps1
```

## Method 3: Using curl

### Test Instagram Scraping
```bash
curl -X POST "http://localhost:8000/api/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.instagram.com/nike/",
    "post_limit": 10,
    "use_api": true
  }'
```

### Test Pinterest Scraping
```bash
curl -X POST "http://localhost:8000/api/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.pinterest.com/pinterest/fashion/",
    "post_limit": 10,
    "use_api": true
  }'
```

### Test Batch Scraping
```bash
curl -X POST "http://localhost:8000/api/v1/scrape/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.instagram.com/nike/",
      "https://www.pinterest.com/pinterest/fashion/"
    ],
    "post_limit": 5,
    "use_api": true
  }'
```

## Method 4: Using Python

```python
import requests

# Test Instagram
response = requests.post(
    "http://localhost:8000/api/v1/scrape",
    json={
        "url": "https://www.instagram.com/nike/",
        "post_limit": 10,
        "use_api": True
    }
)
print(response.json())

# Or run the test script:
# python test_scraping.py
```

## Expected Response Format

### Success Response:
```json
{
  "success": true,
  "message": "Successfully scraped 10 posts from instagram",
  "total_posts": 10,
  "posts": [
    {
      "source": "instagram",
      "structured_data": { ... },
      "scraped_date": "2025-11-06T...",
      "extraction_method": "apify"
    }
  ],
  "url": "https://www.instagram.com/nike/",
  "platform": "instagram",
  "scraped_at": "2025-11-06T...",
  "estimated_cost": 0.015
}
```

### Error Response:
```json
{
  "detail": "Error message here"
}
```

## Common Issues

1. **"Apify token not configured"**
   - Solution: Set APIFY_TOKEN in .env file or environment variable

2. **"Backend not running"**
   - Solution: Run `docker-compose up -d`

3. **"Connection refused"**
   - Solution: Check if port 8000 is accessible: `curl http://localhost:8000/`

4. **"Timeout"**
   - Solution: Scraping can take time. Increase timeout or reduce post_limit

## Quick Test Commands

```powershell
# 1. Check if backend is running
curl http://localhost:8000/

# 2. Test Instagram (quick - 5 posts)
curl -X POST "http://localhost:8000/api/v1/scrape" -H "Content-Type: application/json" -d '{\"url\":\"https://www.instagram.com/nike/\",\"post_limit\":5,\"use_api\":true}'

# 3. View API docs
Start-Process "http://localhost:8000/docs"
```

