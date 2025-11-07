"""FastAPI routes for fashion AI system."""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body
from fastapi.responses import Response
from typing import Optional, List
from PIL import Image
import io
import time
from datetime import datetime
from loguru import logger
from pydantic import BaseModel
import httpx

from models.schemas import (
    DetectionResponse, SearchResponse, OutfitResponse,
    CompatibilityResponse, ColorHarmonyResponse, ErrorResponse,
    TextSearchResponse, Category, ProductsListResponse, ProductResponse
)
from services import (
    get_detection_service, get_embedding_service,
    VectorDBService, OutfitService, ColorService,
    get_text_search_service
)

router = APIRouter()


@router.post("/detect", response_model=DetectionResponse)
async def detect_fashion_items(file: UploadFile = File(...)):
    """Detect fashion items in uploaded image."""
    start_time = time.time()
    
    try:
        # Validate file type
        if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            raise HTTPException(
                status_code=400,
                detail="Unsupported image format. Use JPEG, PNG, or WebP."
            )
        
        # Read and process image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Detect items
        detection_service = get_detection_service()
        detected_items = detection_service.detect_items(image)
        
        processing_time = (time.time() - start_time) * 1000
        
        return DetectionResponse(
            detected_items=detected_items,
            processing_time_ms=processing_time,
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection error: {str(e)}")


@router.post("/search/similar", response_model=SearchResponse)
async def search_similar_products(
    file: UploadFile = File(...),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None
):
    """Search for visually similar products."""
    start_time = time.time()
    
    try:
        # Read and process image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Generate embeddings for visual similarity search
        embedding_service = get_embedding_service()
        vector_db = VectorDBService()
        
        # Generate embedding for the entire image (works even without item detection)
        embedding = embedding_service.encode_image(image)
        
        # Try to detect items (optional - for metadata)
        detection_service = get_detection_service()
        detected_items = detection_service.detect_items(image)
        
        # Search similar products using visual similarity
        similar_products = vector_db.search_similar(
            query_embedding=embedding,
            limit=limit
        )
        
        # Build results
        results = []
        
        if detected_items:
            # If items were detected, use that metadata
            for item in detected_items:
                results.append({
                    "query_item": {
                        "category": item.category.value,
                        "subcategory": item.subcategory,
                        "detected_features": {
                            "colors": item.colors,
                            "style": item.style_tags
                        }
                    },
                    "similar_products": [
                        {
                            "product_id": sp.product_id,
                            "similarity_score": sp.similarity_score,
                            "product_info": {
                                "product_id": sp.product_info.product_id,
                                "name": sp.product_info.name,
                                "brand": sp.product_info.brand,
                                "price": sp.product_info.price,
                                "currency": sp.product_info.currency,
                                "image_url": str(sp.product_info.image_url) if sp.product_info.image_url else None,
                                "in_stock": sp.product_info.in_stock
                            },
                            "match_reasoning": sp.match_reasoning,
                            "key_similarities": sp.key_similarities
                        }
                        for sp in similar_products
                    ],
                    "total_matches": len(similar_products),
                    "returned_count": len(similar_products)
                })
        else:
            # No items detected, but still perform visual similarity search
            # This is useful for product-on-plain-background images
            # Use a default category (clothing) since we don't know what it is
            results.append({
                "query_item": {
                    "category": Category.CLOTHING,  # Use Category enum
                    "subcategory": "visual_similarity",
                    "detected_features": {
                        "colors": [],
                        "style": []
                    }
                },
                "similar_products": [
                    {
                        "product_id": sp.product_id,
                        "similarity_score": sp.similarity_score,
                        "product_info": {
                            "product_id": sp.product_info.product_id,
                            "name": sp.product_info.name,
                            "brand": sp.product_info.brand,
                            "price": sp.product_info.price,
                            "currency": sp.product_info.currency,
                            "image_url": str(sp.product_info.image_url) if sp.product_info.image_url else None,
                            "in_stock": sp.product_info.in_stock
                        },
                        "match_reasoning": sp.match_reasoning,
                        "key_similarities": sp.key_similarities
                    }
                    for sp in similar_products
                ],
                "total_matches": len(similar_products),
                "returned_count": len(similar_products)
            })
        
        processing_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            query_info={
                "query_type": "image_search",
                "detected_items": len(detected_items),
                "processing_time_ms": processing_time,
                "timestamp": datetime.utcnow().isoformat()
            },
            results=results,
            filters_applied={"category": category} if category else None,
            suggestions={
                "refine_search": ["Try filtering by price range", "Filter by brand"],
                "related_searches": ["Similar styles", "Same color palette"]
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.post("/outfit/recommend", response_model=OutfitResponse)
async def recommend_outfit(
    anchor_product_id: Optional[str] = None,
    anchor_item: Optional[dict] = None,
    occasion: str = Query("casual"),
    season: str = Query("all-season"),
    gender: str = Query("unisex"),
    budget_range: str = Query("mid-range")
):
    """Generate complete outfit recommendation."""
    try:
        outfit_service = OutfitService()
        
        # If anchor_product_id provided, fetch from DB
        # For now, use anchor_item directly
        if not anchor_item:
            anchor_item = {
                "category": "shoes",
                "subcategory": "sneakers",
                "colors": ["white", "black"],
                "style_tags": ["casual", "athletic"]
            }
        
        # Generate outfit
        outfit = outfit_service.generate_outfit(
            anchor_product=anchor_item,
            occasion=occasion,
            season=season,
            gender=gender,
            budget_range=budget_range
        )
        
        return OutfitResponse(
            request_info={
                "anchor_product_id": anchor_product_id,
                "occasion": occasion,
                "season": season,
                "budget_range": budget_range
            },
            outfit_recommendations=[outfit],
            metadata={
                "total_outfits_generated": 1,
                "generation_time_ms": 0,
                "ai_confidence": 0.91
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Outfit recommendation error: {str(e)}")


@router.post("/compatibility/analyze", response_model=CompatibilityResponse)
async def analyze_compatibility(items: List[dict]):
    """Analyze compatibility between fashion items."""
    try:
        outfit_service = OutfitService()
        compatibility = outfit_service.analyze_compatibility(items)
        return compatibility
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compatibility analysis error: {str(e)}")


@router.post("/color/harmony", response_model=ColorHarmonyResponse)
async def analyze_color_harmony(
    base_colors: List[str],
    occasion: str = Query("casual"),
    season: str = Query("all-season")
):
    """Analyze color harmony and provide recommendations."""
    try:
        color_service = ColorService()
        harmony = color_service.analyze_harmony(base_colors, occasion, season)
        return harmony
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Color analysis error: {str(e)}")


class TextSearchRequest(BaseModel):
    """Text search request model."""
    query: str
    limit: int = 10
    category: Optional[str] = None
    bm25_weight: float = 0.4
    semantic_weight: float = 0.6
    min_score: float = 0.3


@router.post("/search/text", response_model=TextSearchResponse)
async def search_by_text(request: TextSearchRequest):
    """
    Hybrid text search using BM25 (keyword) + Sentence-Transformers (semantic).
    
    Combines:
    - BM25: Fast keyword-based search (exact matches, brand names, etc.)
    - Sentence-Transformers: Semantic understanding (synonyms, context, meaning)
    
    Example queries:
    - "Nike sneakers"
    - "red running shoes"
    - "casual footwear"
    - "Yeezy Boost 350"
    """
    start_time = time.time()
    
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Validate limit
        if request.limit < 1 or request.limit > 100:
            request.limit = 10
        
        # Get text search service
        text_search_service = get_text_search_service()
        
        # Perform hybrid search
        results = text_search_service.search(
            query=request.query.strip(),
            limit=request.limit,
            bm25_weight=request.bm25_weight,
            semantic_weight=request.semantic_weight,
            category=request.category,
            min_score=request.min_score
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return TextSearchResponse(
            query=request.query,
            results=results,
            total_matches=len(results),
            returned_count=len(results),
            search_method="hybrid_bm25_semantic",
            bm25_weight=request.bm25_weight,
            semantic_weight=request.semantic_weight,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text search error: {e}")
        raise HTTPException(status_code=500, detail=f"Text search error: {str(e)}")


@router.get("/products", response_model=ProductsListResponse)
async def get_products(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get all products from the database.
    
    Returns a list of products with all metadata including description.
    """
    try:
        vector_db = VectorDBService()
        
        # Get products
        products_data = vector_db.get_all_products(limit=limit, offset=offset)
        
        # Get total count
        total = vector_db.get_total_count()
        
        # Convert to response models
        products = []
        for product_data in products_data:
            # Extract description from metadata if not in main fields
            description = product_data.get("description")
            if not description:
                # Try to get from metadata
                metadata = product_data.get("metadata", {})
                description = metadata.get("description") or metadata.get("title") or ""
            
            product = ProductResponse(
                product_id=product_data.get("product_id", product_data.get("id", "")),
                id=product_data.get("id", ""),
                name=product_data.get("name", "Unknown"),
                description=description,
                brand=product_data.get("brand"),
                price=product_data.get("price", 0.0),  # Default to 0.0 if missing
                currency=product_data.get("currency", "INR"),
                image_url=product_data.get("image_url"),
                in_stock=product_data.get("in_stock", True),
                category=product_data.get("category"),
                subcategory=product_data.get("subcategory"),
                colors=product_data.get("colors", []),
                style_tags=product_data.get("style_tags", []),
                metadata=product_data.get("metadata", {})
            )
            products.append(product)
        
        return ProductsListResponse(
            products=products,
            total=total,
            limit=limit,
            offset=offset,
            returned_count=len(products)
        )
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving products: {str(e)}")


@router.get("/product/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """
    Get a single product by ID.
    
    Returns product details including description and all metadata.
    """
    try:
        vector_db = VectorDBService()
        
        # Get product
        product_data = vector_db.get_product_by_id(product_id)
        
        if not product_data:
            raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
        
        # Extract description from metadata if not in main fields
        description = product_data.get("description")
        if not description:
            metadata = product_data.get("metadata", {})
            description = metadata.get("description") or metadata.get("title") or ""
        
        product = ProductResponse(
            product_id=product_data.get("product_id", product_data.get("id", "")),
            id=product_data.get("id", ""),
            name=product_data.get("name", "Unknown"),
            description=description,
            brand=product_data.get("brand"),
            price=product_data.get("price"),  # Can be None
            currency=product_data.get("currency", "INR"),
            image_url=product_data.get("image_url"),
            in_stock=product_data.get("in_stock", True),
            category=product_data.get("category"),
            subcategory=product_data.get("subcategory"),
            colors=product_data.get("colors", []),
            style_tags=product_data.get("style_tags", []),
            metadata=product_data.get("metadata", {})
        )
        
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving product: {str(e)}")


@router.get("/products/image-proxy")
async def proxy_product_image(url: str = Query(..., description="Image URL to proxy")):
    """
    Proxy image from external URL to bypass CORS restrictions.
    
    This endpoint fetches images from external sources and serves them
    through the backend to avoid CORS issues. Used by PostsGallery and other components.
    """
    try:
        logger.info(f"Product image proxy request for URL: {url[:100]}...")
        
        # Validate URL
        if not url or not url.startswith(("http://", "https://")):
            logger.error(f"Invalid URL format: {url}")
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        # Fetch image with timeout and browser-like headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.instagram.com/",
            "Accept-Encoding": "gzip, deflate, br",
        }
        
        logger.info(f"Fetching product image from: {url[:100]}...")
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
            
            content_length = len(response.content)
            logger.info(f"Successfully fetched product image: {content_length} bytes, content-type: {content_type}")
            
            # Return image with appropriate headers
            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Expose-Headers": "*",
                    "Content-Length": str(content_length),
                }
            )
    
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching product image: {url[:100]}")
        raise HTTPException(status_code=504, detail="Image fetch timeout")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching product image: {e.response.status_code} - {url[:100]}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch image: HTTP {e.response.status_code}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error proxying product image: {str(e)} - URL: {url[:100]}")
        raise HTTPException(status_code=500, detail=f"Error proxying image: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

