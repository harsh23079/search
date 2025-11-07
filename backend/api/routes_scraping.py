"""FastAPI routes for social media scraping."""
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from fastapi.responses import Response
from typing import Optional
from loguru import logger
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
import math

from models.schemas import (
    ScrapeRequest, ScrapeResponse, BatchScrapeRequest, BatchScrapeResponse,
    InstagramPostPaginationRequest, InstagramPostPaginatedResponse,
    InstagramPostDetailResponse, InstagramPostMinimalSchema, PaginationMeta
)
from services.scraping_service import ScrapingService
from services.image_cache import get_image_cache
from services.post_storage import get_post_storage
from config.database import get_db
from repositories.instagram_post_repository import InstagramPostRepository

router = APIRouter()


@router.post("/scrape", response_model=ScrapeResponse, tags=["scraping"])
async def scrape_social_media(
    request: ScrapeRequest,
    save_to_db: bool = Query(default=False, description="Save scraped posts to database"),
    db: AsyncSession = Depends(get_db)
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
        # Create service with database session if save_to_db is True
        service = ScrapingService(db_session=db if save_to_db else None)
        response = await service.scrape_social_media_posts(request, save_to_db)
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
    save_to_db: bool = Query(default=False, description="Save scraped posts to database"),
    db: AsyncSession = Depends(get_db)
):
    """
    Scrape posts from multiple URLs in batch.
    
    Processes multiple Instagram or Pinterest URLs in a single request.
    """
    try:
        logger.info(f"Received batch scrape request for {len(request.urls)} URLs")
        # Create service with database session if save_to_db is True
        service = ScrapingService(db_session=db if save_to_db else None)
        response = await service.scrape_batch(request, save_to_db)
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


@router.get("/scraped-posts", tags=["scraping"])
async def get_saved_posts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    platform: Optional[str] = Query(None, description="Filter by platform (instagram, pinterest)")
):
    """Get saved scraped posts from file storage."""
    try:
        post_storage = get_post_storage()
        
        logger.info(f"Fetching posts: offset={offset}, limit={limit}, platform={platform}")
        
        posts, total = post_storage.get_posts(
            limit=limit,
            offset=offset,
            platform=platform
        )
        
        logger.info(f"Retrieved {len(posts)} posts, total={total}")
        
        return {
            "success": True,
            "posts": posts,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Error getting saved posts: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving saved posts: {str(e)}")


@router.get("/scraped-posts/{post_id}", tags=["scraping"])
async def get_saved_post(
    post_id: str
):
    """Get a single saved post by ID from file storage."""
    try:
        post_storage = get_post_storage()
        post = post_storage.get_post_by_id(post_id)
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return {
            "success": True,
            "post": post,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting saved post: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving post: {str(e)}")


@router.get("/posts", response_model=InstagramPostPaginatedResponse, tags=["scraping"])
async def get_instagram_posts(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of posts per page"),
    owner_username: Optional[str] = Query(default=None, description="Filter by owner username"),
    sort_by: str = Query(default="scraped_date", description="Sort field: scraped_date, timestamp, likes, comments"),
    sort_order: str = Query(default="desc", description="Sort order: asc or desc"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of saved Instagram posts.
    
    Retrieve posts that were previously scraped and saved to the database.
    """
    try:
        repository = InstagramPostRepository(db)
        posts, total_count = await repository.get_posts_paginated(
            page=page,
            page_size=page_size,
            owner_username=owner_username,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Convert to minimal schemas
        post_schemas = []
        for post in posts:
            post_schemas.append(InstagramPostMinimalSchema(
                id=post.id,
                type=post.type,
                url=post.url,
                display_url=post.display_url,
                caption=post.caption[:200] if post.caption else None,  # Truncate caption
                likes_count=post.likes_count,
                comments_count=post.comments_count,
                timestamp=post.timestamp,
                owner_username=post.owner_username,
                owner_full_name=post.owner_full_name,
                scraped_date=post.scraped_date
            ))
        
        # Calculate pagination metadata
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0
        
        pagination_meta = PaginationMeta(
            current_page=page,
            page_size=page_size,
            total_items=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
        
        filter_msg = f" for @{owner_username}" if owner_username else ""
        message = f"Retrieved {len(posts)} posts (page {page} of {total_pages}){filter_msg}"
        
        return InstagramPostPaginatedResponse(
            success=True,
            message=message,
            posts=post_schemas,
            pagination=pagination_meta
        )
        
    except Exception as e:
        logger.error(f"Error fetching posts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching posts: {str(e)}"
        )


@router.get("/posts/{post_id}", response_model=InstagramPostDetailResponse, tags=["scraping"])
async def get_instagram_post(
    post_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single Instagram post by ID with full details.
    """
    try:
        repository = InstagramPostRepository(db)
        post = await repository.get_post_by_id(post_id)
        
        if not post:
            raise HTTPException(
                status_code=404,
                detail=f"Instagram post not found with ID: {post_id}"
            )
        
        # Check if post has been extracted (for future use)
        is_extracted = await repository.check_post_extracted(post_id)
        
        # Convert to dict and add extraction flag
        post_dict = post.to_dict()
        post_dict["is_extracted"] = is_extracted
        
        return InstagramPostDetailResponse(
            success=True,
            message="Post retrieved successfully",
            post=post_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching post: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching post: {str(e)}"
        )

