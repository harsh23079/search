"""Scraping service for Instagram and Pinterest."""
from typing import List, Dict, Optional
import re
from fastapi import HTTPException, status
from datetime import datetime
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from services.instagram_scraper import InstagramScraper
from services.pinterest_scraper import PinterestScraper
from services.post_storage import get_post_storage
from models.schemas import ScrapeRequest, ScrapeResponse, ScrapedPost, BatchScrapeRequest, BatchScrapeResponse
from config import settings


class ScrapingService:
    """Service for scraping social media posts."""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        logger.info("Initializing Instagram and Pinterest scrapers")
        self.db_session = db_session
        self.instagram_scraper = InstagramScraper(db_session)
        self.pinterest_scraper = PinterestScraper()
        logger.info("Scrapers initialized successfully")
    
    async def scrape_social_media_posts(self, request: ScrapeRequest, save_to_db: bool = False) -> ScrapeResponse:
        """Main method to scrape posts from Instagram or Pinterest."""
        try:
            logger.info(f"Starting scraping request for URL: {request.url}")
            
            # Validate post limit
            if request.post_limit > settings.max_posts_per_request:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Post limit cannot exceed {settings.max_posts_per_request}"
                )
            
            # Determine platform and scrape accordingly
            platform = self._detect_platform(str(request.url))
            logger.info(f"Detected platform: {platform}")
            
            if platform == "instagram":
                posts_data = await self._scrape_instagram(str(request.url), request.post_limit, save_to_db)
                estimated_cost = len(posts_data) * 0.0015  # $1.50 per 1000 results
            elif platform == "pinterest":
                posts_data = await self._scrape_pinterest(str(request.url), request.post_limit, request.use_api)
                estimated_cost = len(posts_data) * 0.001  # Estimated cost
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported platform. Only Instagram and Pinterest URLs are supported."
                )
            
            # Convert to Pydantic models
            scraped_posts = [ScrapedPost(**post) for post in posts_data]

            # Save to storage if requested
            if save_to_db:
                try:
                    post_storage = get_post_storage()
                    logger.info(f"Attempting to save {len(posts_data)} posts to storage")
                    saved_count = post_storage.save_posts(
                        posts=posts_data,
                        source_url=str(request.url),
                        platform=platform
                    )
                    if saved_count > 0:
                        logger.info(f"Successfully saved {saved_count} posts to storage")
                    else:
                        logger.warning(f"Failed to save posts to storage: saved_count is 0")
                except Exception as e:
                    logger.error(f"Failed to save posts to storage: {e}", exc_info=True)
                    # Don't fail the entire request if storage save fails

            response = ScrapeResponse(
                success=True,
                message=f"Successfully scraped {len(scraped_posts)} posts from {platform}",
                total_posts=len(scraped_posts),
                posts=scraped_posts,
                url=str(request.url),
                platform=platform,
                scraped_at=datetime.now(),
                estimated_cost=estimated_cost
            )
            
            logger.info(f"Scraping completed: {len(scraped_posts)} posts from {platform}")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred while scraping: {str(e)}"
            )
    
    async def scrape_batch(self, request: BatchScrapeRequest, save_to_db: bool = False) -> BatchScrapeResponse:
        """Scrape multiple URLs in batch."""
        try:
            logger.info(f"Starting batch scraping for {len(request.urls)} URLs")
            
            all_posts = []
            total_cost = 0.0
            errors = []
            urls_processed = 0
            
            for i, url in enumerate(request.urls):
                try:
                    logger.info(f"Processing URL {i+1}/{len(request.urls)}: {url}")
                    
                    # Create individual scrape request
                    individual_request = ScrapeRequest(url=url, post_limit=request.post_limit, use_api=request.use_api)
                    response = await self.scrape_social_media_posts(individual_request, save_to_db)
                    
                    # Add posts to the batch result
                    all_posts.extend(response.posts)
                    total_cost += response.estimated_cost or 0
                    urls_processed += 1
                    
                    logger.info(f"URL {i+1} completed successfully. Posts: {len(response.posts)}")
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error processing URL {i+1}: {error_msg}")
                    errors.append({
                        "url": str(url),
                        "error": error_msg
                    })
            
            logger.info(f"Batch scraping completed. Total posts: {len(all_posts)}, Total cost: ${total_cost:.4f}")
            
            return BatchScrapeResponse(
                success=len(errors) < len(request.urls),
                message=f"Batch scraping completed. Processed {urls_processed}/{len(request.urls)} URLs",
                total_posts=len(all_posts),
                posts=all_posts,
                urls_processed=urls_processed,
                urls_failed=len(errors),
                errors=errors,
                scraped_at=datetime.now(),
                total_cost=total_cost
            )
            
        except Exception as e:
            logger.error(f"Batch scraping failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Batch scraping failed: {str(e)}"
            )
    
    async def _scrape_instagram(self, url: str, post_limit: int, save_to_db: bool = False) -> List[Dict]:
        """Scrape Instagram posts."""
        logger.info(f"Determining Instagram scraping method for: {url}")
        
        # Determine if it's a profile or hashtag URL
        if "/explore/tags/" in url:
            logger.info("Using hashtag scraping method")
            return await self.instagram_scraper.scrape_hashtag_posts(url, post_limit, save_to_db)
        else:
            logger.info("Using profile scraping method")
            return await self.instagram_scraper.scrape_profile_posts(url, post_limit, save_to_db)
    
    async def _scrape_pinterest(self, url: str, post_limit: int, use_api: bool = True) -> List[Dict]:
        """Scrape Pinterest posts."""
        logger.info(f"Determining Pinterest scraping method for: {url}")
        
        # Determine if it's a board or user URL
        if self._is_pinterest_board_url(url):
            logger.info("Using board scraping method")
            return await self.pinterest_scraper.scrape_board_posts(url, post_limit, use_api)
        else:
            logger.info("Using user scraping method")
            return await self.pinterest_scraper.scrape_user_posts(url, post_limit, use_api)
    
    def _detect_platform(self, url: str) -> str:
        """Detect which platform the URL belongs to."""
        if "instagram.com" in url.lower():
            return "instagram"
        elif "pinterest.com" in url.lower():
            return "pinterest"
        else:
            raise ValueError("Unsupported platform")
    
    def _is_pinterest_board_url(self, url: str) -> bool:
        """Check if Pinterest URL is a board URL."""
        # Board URLs typically have format: pinterest.com/username/boardname
        pattern = r'pinterest\.com/([^/?]+)/([^/?]+)'
        match = re.search(pattern, url)
        if match:
            path_parts = url.split('/')
            return len([part for part in path_parts if part]) >= 4
        return False

