"""Repository for Instagram post database operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from datetime import datetime
from loguru import logger

from models.instagram_post import InstagramPost


class InstagramPostRepository:
    """Repository for Instagram post operations."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def save_post(self, post_data: dict) -> Optional[InstagramPost]:
        """Save or update an Instagram post."""
        try:
            # Extract post ID from structured_data
            structured = post_data.get("structured_data") or {}
            post_id = (
                structured.get("id") or 
                structured.get("shortCode") or 
                structured.get("short_code") or
                post_data.get("id")
            )
            if not post_id:
                logger.warning("Post ID not found in data, skipping save")
                return None
            
            # Check if post already exists
            result = await self.db.execute(
                select(InstagramPost).where(InstagramPost.id == post_id)
            )
            existing_post = result.scalar_one_or_none()
            
            if existing_post:
                # Update existing post
                logger.info(f"Updating existing post: {post_id}")
                self._update_post_from_data(existing_post, post_data)
                await self.db.commit()
                await self.db.refresh(existing_post)
                return existing_post
            else:
                # Create new post
                logger.info(f"Creating new post: {post_id}")
                new_post = self._create_post_from_data(post_id, post_data)
                self.db.add(new_post)
                await self.db.commit()
                await self.db.refresh(new_post)
                return new_post
                
        except Exception as e:
            logger.error(f"Error saving post: {e}")
            await self.db.rollback()
            raise
    
    async def save_batch_posts(self, posts_data: List[dict]) -> int:
        """Save multiple posts in batch."""
        saved_count = 0
        for post_data in posts_data:
            try:
                post = await self.save_post(post_data)
                if post:
                    saved_count += 1
            except Exception as e:
                logger.error(f"Error saving post in batch: {e}")
                continue
        return saved_count
    
    async def get_post_by_id(self, post_id: str) -> Optional[InstagramPost]:
        """Get a post by ID."""
        try:
            result = await self.db.execute(
                select(InstagramPost).where(InstagramPost.id == post_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting post by ID: {e}")
            return None
    
    async def get_posts_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        owner_username: Optional[str] = None,
        sort_by: str = "scraped_date",
        sort_order: str = "desc"
    ) -> Tuple[List[InstagramPost], int]:
        """Get paginated posts with optional filtering."""
        try:
            # Build query
            query = select(InstagramPost)
            
            # Apply filters
            if owner_username:
                query = query.where(InstagramPost.owner_username == owner_username)
            
            # Get total count
            count_query = select(func.count()).select_from(InstagramPost)
            if owner_username:
                count_query = count_query.where(InstagramPost.owner_username == owner_username)
            
            total_result = await self.db.execute(count_query)
            total_count = total_result.scalar() or 0
            
            # Apply sorting
            if sort_by == "timestamp":
                sort_column = InstagramPost.timestamp
            elif sort_by == "likes":
                sort_column = InstagramPost.likes_count
            elif sort_by == "comments":
                sort_column = InstagramPost.comments_count
            else:  # default to scraped_date
                sort_column = InstagramPost.scraped_date
            
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
            
            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            # Execute query
            result = await self.db.execute(query)
            posts = result.scalars().all()
            
            return list(posts), total_count
            
        except Exception as e:
            logger.error(f"Error getting paginated posts: {e}")
            return [], 0
    
    async def check_post_extracted(self, post_id: str) -> bool:
        """Check if post has been extracted to products (for future use)."""
        # This can be extended to check if post has related products
        return False
    
    async def delete_post(self, post_id: str) -> bool:
        """Delete an Instagram post by ID."""
        try:
            result = await self.db.execute(
                select(InstagramPost).where(InstagramPost.id == post_id)
            )
            post = result.scalar_one_or_none()
            
            if not post:
                return False
            
            await self.db.delete(post)
            await self.db.commit()
            logger.info(f"Deleted post: {post_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting post {post_id}: {e}")
            await self.db.rollback()
            return False
    
    def _create_post_from_data(self, post_id: str, post_data: dict) -> InstagramPost:
        """Create InstagramPost model from scraped data."""
        structured = post_data.get("structured_data") or {}
        
        # Extract timestamp
        timestamp = None
        if structured.get("timestamp"):
            try:
                timestamp = datetime.fromtimestamp(structured["timestamp"])
            except:
                pass
        
        # Extract images
        images = []
        if structured.get("displayUrl"):
            images.append(structured["displayUrl"])
        if structured.get("images"):
            images.extend(structured["images"])
        
        # Extract hashtags and mentions from caption
        hashtags = structured.get("hashtags") or []
        mentions = structured.get("mentions") or []
        
        return InstagramPost(
            id=post_id,
            type=structured.get("type"),
            short_code=structured.get("shortCode") or structured.get("short_code"),
            url=structured.get("url"),
            display_url=structured.get("displayUrl") or structured.get("display_url"),
            images=images if images else None,
            caption=structured.get("caption"),
            alt=structured.get("alt"),
            likes_count=structured.get("likesCount") or structured.get("likes_count") or 0,
            comments_count=structured.get("commentsCount") or structured.get("comments_count") or 0,
            first_comment=structured.get("firstComment") or structured.get("first_comment"),
            latest_comments=structured.get("latestComments") or structured.get("latest_comments"),
            timestamp=timestamp,
            dimensions_height=structured.get("dimensions", {}).get("height") if isinstance(structured.get("dimensions"), dict) else None,
            dimensions_width=structured.get("dimensions", {}).get("width") if isinstance(structured.get("dimensions"), dict) else None,
            owner_full_name=structured.get("ownerFullName") or structured.get("owner_full_name"),
            owner_username=structured.get("ownerUsername") or structured.get("owner_username"),
            owner_id=structured.get("ownerId") or structured.get("owner_id"),
            hashtags=hashtags,
            mentions=mentions,
            tagged_users=structured.get("taggedUsers") or structured.get("tagged_users"),
            is_comments_disabled=structured.get("isCommentsDisabled") or structured.get("is_comments_disabled") or False,
            is_sponsored=structured.get("isSponsored") or structured.get("is_sponsored") or False,
            child_posts=structured.get("childPosts") or structured.get("child_posts"),
            raw_data=post_data.get("structured_data"),
            scraped_date=post_data.get("scraped_date") or datetime.now(),
        )
    
    def _update_post_from_data(self, post: InstagramPost, post_data: dict):
        """Update existing post with new data."""
        structured = post_data.get("structured_data") or {}
        
        # Update fields if they exist in new data
        if structured.get("type"):
            post.type = structured["type"]
        if structured.get("caption"):
            post.caption = structured["caption"]
        if structured.get("likesCount") or structured.get("likes_count"):
            post.likes_count = structured.get("likesCount") or structured.get("likes_count")
        if structured.get("commentsCount") or structured.get("comments_count"):
            post.comments_count = structured.get("commentsCount") or structured.get("comments_count")
        
        # Update timestamp
        post.updated_at = datetime.now()

