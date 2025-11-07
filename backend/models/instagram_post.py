"""Database model for Instagram posts."""
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Index
from sqlalchemy.sql import func
from config.database import Base
from datetime import datetime
from typing import Optional, Dict, Any, List


class InstagramPost(Base):
    """Instagram post database model."""
    __tablename__ = "instagram_posts"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)  # Instagram post ID
    
    # Post metadata
    type = Column(String, nullable=True)  # post, carousel, video, etc.
    short_code = Column(String, nullable=True, index=True)  # Instagram short code
    url = Column(String, nullable=True)  # Full Instagram URL
    display_url = Column(String, nullable=True)  # Image display URL
    
    # Images (stored as JSON array)
    images = Column(JSON, nullable=True)  # List of image URLs
    
    # Content
    caption = Column(Text, nullable=True)  # Post caption
    alt = Column(String, nullable=True)  # Alt text
    
    # Engagement metrics
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    first_comment = Column(Text, nullable=True)
    latest_comments = Column(JSON, nullable=True)  # Array of comments
    
    # Timestamps
    timestamp = Column(DateTime, nullable=True)  # Original post timestamp
    scraped_date = Column(DateTime, default=func.now(), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Dimensions
    dimensions_height = Column(Integer, nullable=True)
    dimensions_width = Column(Integer, nullable=True)
    
    # Owner information
    owner_full_name = Column(String, nullable=True)
    owner_username = Column(String, nullable=True, index=True)
    owner_id = Column(String, nullable=True)
    
    # Tags and mentions
    hashtags = Column(JSON, nullable=True)  # Array of hashtags
    mentions = Column(JSON, nullable=True)  # Array of mentioned usernames
    tagged_users = Column(JSON, nullable=True)  # Array of tagged users
    
    # Flags
    is_comments_disabled = Column(Boolean, default=False)
    is_sponsored = Column(Boolean, default=False)
    
    # Carousel posts
    child_posts = Column(JSON, nullable=True)  # Array of child post data
    
    # Raw data from scraper
    raw_data = Column(JSON, nullable=True)  # Full raw data from Apify
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_owner_username', 'owner_username'),
        Index('idx_scraped_date', 'scraped_date'),
        Index('idx_timestamp', 'timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "short_code": self.short_code,
            "url": self.url,
            "display_url": self.display_url,
            "images": self.images,
            "caption": self.caption,
            "alt": self.alt,
            "likes_count": self.likes_count,
            "comments_count": self.comments_count,
            "first_comment": self.first_comment,
            "latest_comments": self.latest_comments,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "dimensions_height": self.dimensions_height,
            "dimensions_width": self.dimensions_width,
            "owner_full_name": self.owner_full_name,
            "owner_username": self.owner_username,
            "owner_id": self.owner_id,
            "hashtags": self.hashtags,
            "mentions": self.mentions,
            "tagged_users": self.tagged_users,
            "is_comments_disabled": self.is_comments_disabled,
            "is_sponsored": self.is_sponsored,
            "child_posts": self.child_posts,
            "scraped_date": self.scraped_date.isoformat() if self.scraped_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "raw_data": self.raw_data,
        }

