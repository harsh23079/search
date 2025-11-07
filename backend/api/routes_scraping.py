"""FastAPI routes for social media scraping."""
from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import Response
from typing import Optional
from loguru import logger
import httpx

from models.schemas import ScrapeRequest, ScrapeResponse, BatchScrapeRequest, BatchScrapeResponse
from services.scraping_service import ScrapingService
from services.image_cache import get_image_cache

router = APIRouter()

# Initialize scraping service
scraping_service = ScrapingService()


@router.post("/scrape", response_model=ScrapeResponse, tags=["scraping"])
async def scrape_social_media(
    request: ScrapeRequest,
    save_to_db: bool = Query(default=False, description="Save scraped posts to database")
):
    """
    Scrape posts from Instagram or Pinterest.
    
    Supports:
    - Instagram profiles: https://instagram.com/username
    - Instagram hashtags: https://instagram.com/explore/tags/hashtag
    - Pinterest boards: https://pinterest.com/username/boardname
    - Pinterest users: https://pinterest.com/username
    """
    try:
        logger.info(f"Received scrape request for: {request.url}")
        response = await scraping_service.scrape_social_media_posts(request, save_to_db)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in scrape endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/scrape/batch", response_model=BatchScrapeResponse, tags=["scraping"])
async def scrape_batch(
    request: BatchScrapeRequest,
    save_to_db: bool = Query(default=False, description="Save scraped posts to database")
):
    """
    Scrape posts from multiple URLs in batch.
    
    Processes multiple Instagram or Pinterest URLs in a single request.
    """
    try:
        logger.info(f"Received batch scrape request for {len(request.urls)} URLs")
        response = await scraping_service.scrape_batch(request, save_to_db)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch scrape endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/proxy-image", tags=["scraping"])
async def proxy_image(url: str = Query(..., description="Image URL to proxy")):
    """
    Proxy image from external URL to bypass CORS restrictions.
    
    This endpoint fetches images from external sources (like Instagram CDN)
    and serves them through the backend to avoid CORS issues. Images are cached
    locally for 5 minutes to handle expiring Instagram CDN URLs.
    """
    try:
        logger.info(f"Proxy request received for URL: {url[:100]}...")
        
        # Validate URL
        if not url or not url.startswith(("http://", "https://")):
            logger.error(f"Invalid URL format: {url}")
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        # Only allow Instagram CDN URLs for security
        allowed_domains = [
            "cdninstagram.com",
            "instagram.com",
            "scontent",
            "fbcdn.net",
            "fbcdn",
        ]
        url_lower = url.lower()
        if not any(domain in url_lower for domain in allowed_domains):
            logger.warning(f"URL not in allowed domains: {url[:100]}")
            raise HTTPException(status_code=403, detail="URL domain not allowed")
        
        # Check cache first
        image_cache = get_image_cache()
        cached_result = image_cache.get(url)
        
        if cached_result:
            image_bytes, content_type = cached_result
            logger.info(f"Serving cached image for {url[:100]}... ({len(image_bytes)} bytes)")
            return Response(
                content=image_bytes,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=300",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Expose-Headers": "*",
                    "Content-Length": str(len(image_bytes)),
                    "X-Cache": "HIT",
                }
            )
        
        # Cache miss - fetch from source
        logger.info(f"Cache miss, fetching image from: {url[:100]}...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.instagram.com/",
            "Accept-Encoding": "gzip, deflate, br",
        }
        
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            # Get content type - ensure it's a valid image type
            content_type = response.headers.get("content-type", "image/jpeg")
            # Clean content type (remove charset if present)
            if ";" in content_type:
                content_type = content_type.split(";")[0].strip()
            
            # Ensure we have valid image content
            if not response.content:
                logger.error("Empty image content received")
                raise HTTPException(status_code=502, detail="Empty image content received")
            
            image_bytes = response.content
            content_length = len(image_bytes)
            
            # Cache the image for future requests
            image_cache.set(url, image_bytes, content_type)
            
            logger.info(f"Successfully fetched and cached image: {content_length} bytes, content-type: {content_type}")
            
            # Return image with appropriate headers
            return Response(
                content=image_bytes,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=300",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Expose-Headers": "*",
                    "Content-Length": str(content_length),
                    "X-Cache": "MISS",
                }
            )
    
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching image: {url[:100]}")
        raise HTTPException(status_code=504, detail="Image fetch timeout")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching image: {e.response.status_code} - {url[:100]}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch image: HTTP {e.response.status_code}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error proxying image: {str(e)} - URL: {url[:100]}")
        raise HTTPException(status_code=500, detail=f"Error proxying image: {str(e)}")

