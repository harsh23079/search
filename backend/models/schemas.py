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

