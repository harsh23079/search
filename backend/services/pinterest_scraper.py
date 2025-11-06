"""Pinterest scraping service using Apify."""
from apify_client import ApifyClient
from typing import List, Dict
import asyncio
from datetime import datetime
from fastapi import HTTPException, status
from loguru import logger
from config import settings


class PinterestScraper:
    """Pinterest scraper using Apify."""
    
    def __init__(self):
        if not settings.apify_token:
            logger.warning("APIFY_TOKEN not set. Pinterest scraping will not work.")
            self.client = None
        else:
            self.client = ApifyClient(settings.apify_token)
        self.actor_id = settings.apify_pinterest_actor_id
        self.min_delay = settings.min_delay_between_requests
        self.last_request_time = None
        
    async def scrape_board_posts(
        self, 
        board_url: str, 
        post_limit: int = 50,
        use_api: bool = True
    ) -> List[Dict]:
        """Scrape Pinterest board posts using Apify."""
        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Apify token not configured. Please set APIFY_TOKEN in environment."
            )
        
        try:
            logger.info(f"Starting Pinterest board scraping: {board_url}")
            
            await self._enforce_rate_limit()
            
            # Validate URL
            if not board_url.startswith(("https://pinterest.com/", "https://www.pinterest.com/")):
                raise ValueError("Invalid Pinterest URL")
            
            # Prepare Actor input
            run_input = {
                "startUrls": [board_url],
                "maxItems": post_limit,
                "endPage": 1,
                "proxy": {"useApifyProxy": True}
            }
            
            # Run the Actor
            logger.info(f"Starting Apify actor: {self.actor_id}")
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            logger.info(f"Actor run completed. Run ID: {run.get('id', 'unknown')}")
            
            # Fetch results
            scraped_data = []
            for i, item in enumerate(self.client.dataset(run["defaultDatasetId"]).iterate_items()):
                raw_post = {
                    "source": "pinterest",
                    "raw_data": item,
                    "scraped_date": datetime.now(),
                    "extraction_method": "apify"
                }
                scraped_data.append(raw_post)
                
                if len(scraped_data) >= post_limit:
                    break
            
            logger.info(f"Successfully scraped {len(scraped_data)} posts")
            return scraped_data
            
        except Exception as e:
            logger.error(f"Error scraping Pinterest board: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error scraping Pinterest board: {str(e)}"
            )
    
    async def scrape_user_posts(
        self, 
        user_url: str, 
        post_limit: int = 50,
        use_api: bool = True
    ) -> List[Dict]:
        """Scrape Pinterest user posts using Apify."""
        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Apify token not configured. Please set APIFY_TOKEN in environment."
            )
        
        try:
            logger.info(f"Starting Pinterest user scraping: {user_url}")
            
            await self._enforce_rate_limit()
            
            # Validate URL
            if not user_url.startswith(("https://pinterest.com/", "https://www.pinterest.com/")):
                raise ValueError("Invalid Pinterest URL")
            
            # Prepare Actor input
            run_input = {
                "startUrls": [user_url],
                "maxItems": post_limit,
                "endPage": 1,
                "proxy": {"useApifyProxy": True}
            }
            
            # Run the Actor
            logger.info(f"Starting Apify actor: {self.actor_id}")
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            logger.info(f"Actor run completed. Run ID: {run.get('id', 'unknown')}")
            
            # Fetch results
            scraped_data = []
            for i, item in enumerate(self.client.dataset(run["defaultDatasetId"]).iterate_items()):
                raw_post = {
                    "source": "pinterest",
                    "raw_data": item,
                    "scraped_date": datetime.now(),
                    "extraction_method": "apify"
                }
                scraped_data.append(raw_post)
                
                if len(scraped_data) >= post_limit:
                    break
            
            logger.info(f"Successfully scraped {len(scraped_data)} posts")
            return scraped_data
            
        except Exception as e:
            logger.error(f"Error scraping Pinterest user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error scraping Pinterest user: {str(e)}"
            )
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        if self.last_request_time:
            time_since_last = (datetime.now() - self.last_request_time).total_seconds()
            if time_since_last < self.min_delay:
                delay = self.min_delay - time_since_last
                logger.info(f"Rate limiting: waiting {delay:.2f} seconds")
                await asyncio.sleep(delay)
        
        self.last_request_time = datetime.now()

