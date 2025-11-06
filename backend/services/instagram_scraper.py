"""Instagram scraping service using Apify."""
from apify_client import ApifyClient
from typing import List, Dict, Optional
import asyncio
from datetime import datetime
from fastapi import HTTPException, status
from loguru import logger
from config import settings


class InstagramScraper:
    """Instagram scraper using Apify."""
    
    def __init__(self):
        if not settings.apify_token:
            logger.warning("APIFY_TOKEN not set. Instagram scraping will not work.")
            self.client = None
        else:
            self.client = ApifyClient(settings.apify_token)
        self.actor_id = settings.apify_instagram_actor_id
        self.min_delay = settings.min_delay_between_requests
        self.last_request_time = None
        
    async def scrape_profile_posts(
        self, 
        profile_url: str, 
        post_limit: int = 50,
        save_to_db: bool = False
    ) -> List[Dict]:
        """Scrape Instagram profile posts using Apify."""
        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Apify token not configured. Please set APIFY_TOKEN in environment."
            )
        
        try:
            logger.info(f"Starting Instagram profile scraping: {profile_url}")
            
            await self._enforce_rate_limit()
            
            # Validate URL
            if not profile_url.startswith(("https://instagram.com/", "https://www.instagram.com/")):
                raise ValueError("Invalid Instagram URL")
            
            search_type = self._determine_instagram_search_type(profile_url)
            
            # Prepare Actor input
            run_input = {
                "directUrls": [profile_url],
                "resultsType": "posts",
                "resultsLimit": post_limit,
                "searchType": search_type,
                "searchLimit": 1,
                "useProxy": True
            }
            
            # Run the Actor
            logger.info(f"Starting Apify actor: {self.actor_id}")
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            logger.info(f"Actor run completed. Run ID: {run.get('id', 'unknown')}")
            
            # Fetch results
            scraped_data = []
            for i, item in enumerate(self.client.dataset(run["defaultDatasetId"]).iterate_items()):
                transformed_post = {
                    "source": "instagram",
                    "structured_data": item,
                    "scraped_date": datetime.now(),
                    "extraction_method": "apify"
                }
                scraped_data.append(transformed_post)
                
                if len(scraped_data) >= post_limit:
                    break
            
            logger.info(f"Successfully scraped {len(scraped_data)} posts")
            return scraped_data
            
        except Exception as e:
            logger.error(f"Error scraping Instagram profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error scraping Instagram profile: {str(e)}"
            )
    
    async def scrape_hashtag_posts(
        self, 
        hashtag_url: str, 
        post_limit: int = 50,
        save_to_db: bool = False
    ) -> List[Dict]:
        """Scrape Instagram hashtag posts using Apify."""
        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Apify token not configured. Please set APIFY_TOKEN in environment."
            )
        
        try:
            logger.info(f"Starting Instagram hashtag scraping: {hashtag_url}")
            
            await self._enforce_rate_limit()
            
            # Validate URL
            if not hashtag_url.startswith(("https://instagram.com/", "https://www.instagram.com/")):
                raise ValueError("Invalid Instagram hashtag URL")
            
            search_type = self._determine_instagram_search_type(hashtag_url)
            
            # Prepare Actor input
            run_input = {
                "directUrls": [hashtag_url],
                "resultsType": "posts",
                "resultsLimit": post_limit,
                "searchType": search_type,
                "searchLimit": 1,
                "useProxy": True
            }
            
            # Run the Actor
            logger.info(f"Starting Apify actor: {self.actor_id}")
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            logger.info(f"Actor run completed. Run ID: {run.get('id', 'unknown')}")
            
            # Fetch results
            scraped_data = []
            for i, item in enumerate(self.client.dataset(run["defaultDatasetId"]).iterate_items()):
                transformed_post = {
                    "source": "instagram",
                    "structured_data": item,
                    "scraped_date": datetime.now(),
                    "extraction_method": "apify"
                }
                scraped_data.append(transformed_post)
                
                if len(scraped_data) >= post_limit:
                    break
            
            logger.info(f"Successfully scraped {len(scraped_data)} posts")
            return scraped_data
            
        except Exception as e:
            logger.error(f"Error scraping Instagram hashtag: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error scraping Instagram hashtag: {str(e)}"
            )
    
    def _determine_instagram_search_type(self, url: str) -> str:
        """Determine Instagram search type based on URL."""
        if "/explore/tags/" in url:
            return "hashtag"
        elif "/p/" in url:
            return "post"
        else:
            return "user"
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        if self.last_request_time:
            time_since_last = (datetime.now() - self.last_request_time).total_seconds()
            if time_since_last < self.min_delay:
                delay = self.min_delay - time_since_last
                logger.info(f"Rate limiting: waiting {delay:.2f} seconds")
                await asyncio.sleep(delay)
        
        self.last_request_time = datetime.now()

