# PowerShell test script for scraping endpoints

$BASE_URL = "http://localhost:8000/api/v1"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "SCRAPING ENDPOINTS TEST" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Test 1: Check if backend is running
Write-Host "`n1. Testing Backend Health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend is running!" -ForegroundColor Green
        $data = $response.Content | ConvertFrom-Json
        Write-Host "   Message: $($data.message)" -ForegroundColor Gray
        Write-Host "   Version: $($data.version)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Backend is not running. Please start it first." -ForegroundColor Red
    Write-Host "   Run: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

# Test 2: Instagram scraping
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "2. Testing Instagram Scraping" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Request: POST $BASE_URL/scrape" -ForegroundColor Gray
Write-Host "Payload: Instagram profile URL" -ForegroundColor Gray

$instagramPayload = @{
    url = "https://www.instagram.com/nike/"
    post_limit = 10
    use_api = $true
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/scrape" -Method Post -Body $instagramPayload -ContentType "application/json" -TimeoutSec 300
    Write-Host "✅ Success!" -ForegroundColor Green
    Write-Host "   Platform: $($response.platform)" -ForegroundColor Gray
    Write-Host "   Total Posts: $($response.total_posts)" -ForegroundColor Gray
    Write-Host "   Estimated Cost: `$$([math]::Round($response.estimated_cost, 4))" -ForegroundColor Gray
    Write-Host "   Message: $($response.message)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Response: $responseBody" -ForegroundColor Red
    }
}

# Test 3: Pinterest scraping
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "3. Testing Pinterest Scraping" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Request: POST $BASE_URL/scrape" -ForegroundColor Gray
Write-Host "Payload: Pinterest board URL" -ForegroundColor Gray

$pinterestPayload = @{
    url = "https://www.pinterest.com/pinterest/fashion/"
    post_limit = 10
    use_api = $true
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/scrape" -Method Post -Body $pinterestPayload -ContentType "application/json" -TimeoutSec 300
    Write-Host "✅ Success!" -ForegroundColor Green
    Write-Host "   Platform: $($response.platform)" -ForegroundColor Gray
    Write-Host "   Total Posts: $($response.total_posts)" -ForegroundColor Gray
    Write-Host "   Estimated Cost: `$$([math]::Round($response.estimated_cost, 4))" -ForegroundColor Gray
    Write-Host "   Message: $($response.message)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Response: $responseBody" -ForegroundColor Red
    }
}

# Test 4: Batch scraping
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "4. Testing Batch Scraping" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Request: POST $BASE_URL/scrape/batch" -ForegroundColor Gray
Write-Host "Payload: Multiple URLs" -ForegroundColor Gray

$batchPayload = @{
    urls = @(
        "https://www.instagram.com/nike/",
        "https://www.pinterest.com/pinterest/fashion/"
    )
    post_limit = 5
    use_api = $true
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/scrape/batch" -Method Post -Body $batchPayload -ContentType "application/json" -TimeoutSec 600
    Write-Host "✅ Success!" -ForegroundColor Green
    Write-Host "   URLs Processed: $($response.urls_processed)" -ForegroundColor Gray
    Write-Host "   URLs Failed: $($response.urls_failed)" -ForegroundColor Gray
    Write-Host "   Total Posts: $($response.total_posts)" -ForegroundColor Gray
    Write-Host "   Total Cost: `$$([math]::Round($response.total_cost, 4))" -ForegroundColor Gray
    Write-Host "   Message: $($response.message)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Response: $responseBody" -ForegroundColor Red
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Testing Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

