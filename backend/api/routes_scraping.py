"""FastAPI routes for social media scraping."""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
from loguru import logger

from models.schemas import ScrapeRequest, ScrapeResponse, BatchScrapeRequest, BatchScrapeResponse
from services.scraping_service import ScrapingService

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

