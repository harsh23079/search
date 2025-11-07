"""Database model for extracted fashion items from Instagram posts."""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.database import Base
from datetime import datetime
from typing import Optional, Dict, Any, List


class ExtractedFashionItem(Base):
    """Extracted fashion item from Instagram post analysis."""
    __tablename__ = "extracted_fashion_items"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)  # UUID or generated ID
    
    # Foreign key to Instagram post
    instagram_post_id = Column(String, ForeignKey("instagram_posts.id"), nullable=False, index=True)
    
    # Item identification
    category = Column(String, nullable=False, index=True)  # clothing, shoes, bags, accessories
    subcategory = Column(String, nullable=True)  # watch, sneakers, shirt, etc.
    
    # Visual features (from image detection)
    colors = Column(JSON, nullable=True)  # List of color names
    style_tags = Column(JSON, nullable=True)  # List of style tags (casual, formal, etc.)
    pattern = Column(String, nullable=True)  # solid, striped, etc.
    material = Column(String, nullable=True)  # cotton, leather, etc.
    bounding_box = Column(JSON, nullable=True)  # [x1, y1, x2, y2] from image detection
    
    # Text-based features (from caption/hashtags analysis)
    brand = Column(String, nullable=True, index=True)  # Extracted brand name
    item_name = Column(String, nullable=True)  # Extracted item name/description
    keywords = Column(JSON, nullable=True)  # List of relevant keywords
    hashtags_related = Column(JSON, nullable=True)  # Relevant hashtags from post
    
    # Semantic embeddings for similarity matching
    image_embedding = Column(JSON, nullable=True)  # Image embedding vector (stored as list)
    text_embedding = Column(JSON, nullable=True)  # Text embedding vector (stored as list)
    
    # Confidence scores
    detection_confidence = Column(Float, nullable=True)  # Confidence from image detection
    extraction_confidence = Column(Float, nullable=True)  # Overall confidence in extraction
    
    # Matching information (for store products)
    matched_store_products = Column(JSON, nullable=True)  # List of matched product IDs with scores
    best_match_product_id = Column(String, nullable=True, index=True)  # Best matching store product
    best_match_score = Column(Float, nullable=True)  # Similarity score for best match
    
    # Metadata
    extraction_method = Column(String, nullable=True)  # "image_detection", "text_analysis", "hybrid"
    extraction_date = Column(DateTime, default=func.now(), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Image URL from Instagram post
    image_url = Column(String, nullable=True)  # URL of the image where item was detected
    post_display_url = Column(String, nullable=True)  # Original post display URL
    
    # Additional extracted data
    raw_extraction_data = Column(JSON, nullable=True)  # Full raw extraction data
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_instagram_post_id', 'instagram_post_id'),
        Index('idx_category', 'category'),
        Index('idx_brand', 'brand'),
        Index('idx_best_match_product', 'best_match_product_id'),
        Index('idx_extraction_date', 'extraction_date'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "instagram_post_id": self.instagram_post_id,
            "category": self.category,
            "subcategory": self.subcategory,
            "colors": self.colors,
            "style_tags": self.style_tags,
            "pattern": self.pattern,
            "material": self.material,
            "bounding_box": self.bounding_box,
            "brand": self.brand,
            "item_name": self.item_name,
            "keywords": self.keywords,
            "hashtags_related": self.hashtags_related,
            "detection_confidence": self.detection_confidence,
            "extraction_confidence": self.extraction_confidence,
            "matched_store_products": self.matched_store_products,
            "best_match_product_id": self.best_match_product_id,
            "best_match_score": self.best_match_score,
            "extraction_method": self.extraction_method,
            "extraction_date": self.extraction_date.isoformat() if self.extraction_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "image_url": self.image_url,
            "post_display_url": self.post_display_url,
            "raw_extraction_data": self.raw_extraction_data,
        }

