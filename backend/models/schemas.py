"""Pydantic schemas for request/response models."""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class Category(str, Enum):
    """Fashion item categories."""
    CLOTHING = "clothing"
    SHOES = "shoes"
    BAGS = "bags"
    ACCESSORIES = "accessories"


class DetectedItem(BaseModel):
    """Detected fashion item from image."""
    item_id: str
    category: Category
    subcategory: str
    colors: List[str] = Field(..., max_items=3)
    style_tags: List[str]
    pattern: str = "solid"
    material: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    bounding_box: List[float] = Field(..., min_items=4, max_items=4)


class DetectionResponse(BaseModel):
    """Response from image detection."""
    detected_items: List[DetectedItem]
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProductInfo(BaseModel):
    """Product information."""
    product_id: str
    name: str
    brand: Optional[str] = None
    price: float
    currency: str = "INR"
    image_url: Optional[HttpUrl] = None
    in_stock: bool = True


class SimilarProduct(BaseModel):
    """Similar product match."""
    product_id: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    product_info: ProductInfo
    match_reasoning: str
    key_similarities: List[str]


class QueryItem(BaseModel):
    """Query item from detection."""
    category: Category
    subcategory: str
    detected_features: Dict[str, Any]


class SearchResult(BaseModel):
    """Individual search result."""
    query_item: QueryItem
    similar_products: List[SimilarProduct]
    total_matches: int
    returned_count: int


class SearchResponse(BaseModel):
    """Search results response."""
    query_info: Dict[str, Any]
    results: List[SearchResult]
    filters_applied: Optional[Dict[str, Any]] = None
    suggestions: Optional[Dict[str, Any]] = None


class OutfitItem(BaseModel):
    """Item in an outfit recommendation."""
    slot: str
    product_id: Optional[str] = None
    name: str
    price: Optional[float] = None
    compatibility_score: float = Field(..., ge=0.0, le=10.0)
    reasoning: str
    alternatives: Optional[List[Dict[str, Any]]] = None


class OutfitRecommendation(BaseModel):
    """Complete outfit recommendation."""
    outfit_id: str
    theme: str
    style_description: str
    overall_compatibility_score: float = Field(..., ge=0.0, le=10.0)
    items: Dict[str, Any]
    total_outfit_price: Optional[float] = None
    styling_tips: List[str]
    occasion_suitability: Dict[str, float]
    purchase_links: Optional[Dict[str, Any]] = None


class OutfitResponse(BaseModel):
    """Outfit recommendation response."""
    request_info: Dict[str, Any]
    outfit_recommendations: List[OutfitRecommendation]
    alternative_outfits: Optional[List[OutfitRecommendation]] = None
    metadata: Dict[str, Any]


class CompatibilityBreakdown(BaseModel):
    """Detailed compatibility breakdown."""
    score: float
    analysis: str


class CompatibilityResponse(BaseModel):
    """Style compatibility analysis response."""
    overall_compatibility_score: float = Field(..., ge=0.0, le=10.0)
    breakdown: Dict[str, CompatibilityBreakdown]
    strengths: List[str]
    potential_improvements: List[str]
    verdict: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ColorHarmonyResponse(BaseModel):
    """Color harmony analysis response."""
    base_colors: List[str]
    color_analysis: Dict[str, Dict[str, Any]]
    harmony_recommendations: Dict[str, Dict[str, Any]]
    avoid_colors: List[Dict[str, str]]
    styling_tips: List[str]


class TextSearchResponse(BaseModel):
    """Text search response."""
    query: str
    results: List[SimilarProduct]
    total_matches: int
    returned_count: int
    search_method: str = "hybrid_bm25_semantic"
    bm25_weight: float = 0.4
    semantic_weight: float = 0.6
    processing_time_ms: Optional[float] = None


class ProductResponse(BaseModel):
    """Product response with all details."""
    product_id: str
    id: str
    name: str
    description: Optional[str] = None
    brand: Optional[str] = None
    price: float  # Always set (estimated if CSV had 0)
    currency: str = "INR"
    image_url: Optional[str] = None
    in_stock: bool = True
    category: Optional[str] = None
    subcategory: Optional[str] = None
    colors: List[str] = []
    style_tags: List[str] = []
    metadata: Dict[str, Any] = {}


class ProductsListResponse(BaseModel):
    """Response for products list endpoint."""
    products: List[ProductResponse]
    total: int
    limit: int
    offset: int
    returned_count: int


class ErrorResponse(BaseModel):
    """Error response model."""
    status: str
    message: str
    issues_detected: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None


# Scraping Schemas
class ScrapeRequest(BaseModel):
    """Request model for scraping social media posts."""
    url: HttpUrl
    post_limit: int = Field(default=50, ge=1, le=1000)
    use_api: bool = True


class ScrapedPost(BaseModel):
    """Scraped post data."""
    source: str
    structured_data: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None
    scraped_date: datetime
    extraction_method: str


class ScrapeResponse(BaseModel):
    """Response model for scraping operation."""
    success: bool
    message: str
    total_posts: int
    posts: List[ScrapedPost]
    url: str
    platform: str
    scraped_at: datetime
    estimated_cost: Optional[float] = None


class BatchScrapeRequest(BaseModel):
    """Request model for batch scraping."""
    urls: List[HttpUrl] = Field(..., min_items=1, max_items=50)
    post_limit: int = Field(default=50, ge=1, le=1000)
    use_api: bool = True


class BatchScrapeResponse(BaseModel):
    """Response model for batch scraping operation."""
    success: bool
    message: str
    total_posts: int
    posts: List[ScrapedPost]
    urls_processed: int
    urls_failed: int
    errors: List[Dict[str, str]] = []
    scraped_at: datetime
    total_cost: Optional[float] = None


# Instagram Post Retrieval Schemas
class InstagramPostMinimalSchema(BaseModel):
    """Minimal Instagram post schema for list views."""
    id: str
    type: Optional[str] = None
    url: Optional[str] = None
    display_url: Optional[str] = None
    caption: Optional[str] = None
    likes_count: int = 0
    comments_count: int = 0
    timestamp: Optional[datetime] = None
    owner_username: Optional[str] = None
    owner_full_name: Optional[str] = None
    scraped_date: datetime


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    current_page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class InstagramPostPaginationRequest(BaseModel):
    """Request model for paginated Instagram posts."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    owner_username: Optional[str] = None
    sort_by: str = Field(default="scraped_date")  # scraped_date, timestamp, likes, comments
    sort_order: str = Field(default="desc")  # asc, desc


class InstagramPostPaginatedResponse(BaseModel):
    """Paginated response for Instagram posts."""
    success: bool
    message: str
    posts: List[InstagramPostMinimalSchema]
    pagination: PaginationMeta


class InstagramPostDetailResponse(BaseModel):
    """Detailed Instagram post response."""
    success: bool
    message: str
    post: Dict[str, Any]


# Semantic Extraction Schemas
class ExtractedItemSchema(BaseModel):
    """Extracted fashion item schema."""
    id: str
    instagram_post_id: str
    category: str
    subcategory: Optional[str] = None
    colors: Optional[List[str]] = None
    style_tags: Optional[List[str]] = None
    pattern: Optional[str] = None
    material: Optional[str] = None
    brand: Optional[str] = None
    item_name: Optional[str] = None
    keywords: Optional[List[str]] = None
    detection_confidence: Optional[float] = None
    extraction_confidence: Optional[float] = None
    best_match_product_id: Optional[str] = None
    best_match_score: Optional[float] = None
    extraction_method: Optional[str] = None
    extraction_date: datetime
    image_url: Optional[str] = None
    post_display_url: Optional[str] = None


class ExtractionResponse(BaseModel):
    """Response from extraction operation."""
    success: bool
    message: str
    post_id: str
    items_extracted: int
    items: List[ExtractedItemSchema]
    processing_time_ms: Optional[float] = None


class ExtractedItemsPaginatedResponse(BaseModel):
    """Paginated response for extracted items."""
    success: bool
    message: str
    items: List[ExtractedItemSchema]
    pagination: PaginationMeta


class ExtractedItemWithMatchesResponse(BaseModel):
    """Extracted item with matched store products."""
    success: bool
    message: str
    item: ExtractedItemSchema
    matched_products: Optional[List[SimilarProduct]] = None