"""FastAPI routes for semantic extraction of fashion items from Instagram posts."""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from loguru import logger
import math
import time

from models.schemas import (
    ExtractionResponse, ExtractedItemsPaginatedResponse,
    ExtractedItemWithMatchesResponse, ExtractedItemSchema, PaginationMeta
)
from models.instagram_post import InstagramPost
from models.extracted_fashion_item import ExtractedFashionItem
from services.semantic_extraction_service import SemanticExtractionService
from repositories.extracted_item_repository import ExtractedItemRepository
from repositories.instagram_post_repository import InstagramPostRepository
from config.database import get_db

router = APIRouter()


@router.post("/extract/{post_id}", response_model=ExtractionResponse, tags=["extraction"])
async def extract_items_from_post(
    post_id: str,
    match_to_store: bool = Query(default=True, description="Match extracted items to store products"),
    similarity_threshold: float = Query(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score for matching"),
    db: AsyncSession = Depends(get_db)
):
    """
    Extract fashion items from a specific Instagram post.
    
    This endpoint:
    1. Analyzes the post's images using computer vision
    2. Analyzes the post's text (caption, hashtags) for fashion information
    3. Combines both to extract fashion items
    4. Optionally matches extracted items to store products
    """
    start_time = time.time()
    
    try:
        # Get the Instagram post
        post_repo = InstagramPostRepository(db)
        post = await post_repo.get_post_by_id(post_id)
        
        if not post:
            raise HTTPException(status_code=404, detail=f"Instagram post not found: {post_id}")
        
        # Initialize extraction service
        extraction_service = SemanticExtractionService()
        
        # Extract items
        extracted_items = await extraction_service.extract_items_from_post(
            post=post,
            match_to_store=match_to_store,
            similarity_threshold=similarity_threshold
        )
        
        if not extracted_items:
            return ExtractionResponse(
                success=True,
                message="No fashion items detected in this post",
                post_id=post_id,
                items_extracted=0,
                items=[],
                processing_time_ms=(time.time() - start_time) * 1000
            )
        
        # Save extracted items to database
        item_repo = ExtractedItemRepository(db)
        saved_count = await item_repo.save_batch_items(extracted_items)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Convert to schemas
        item_schemas = [ExtractedItemSchema(**item.to_dict()) for item in extracted_items]
        
        return ExtractionResponse(
            success=True,
            message=f"Successfully extracted {saved_count} fashion items from post",
            post_id=post_id,
            items_extracted=saved_count,
            items=item_schemas,
            processing_time_ms=processing_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting items from post {post_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting items: {str(e)}"
        )


@router.post("/extract/batch", tags=["extraction"])
async def extract_items_batch(
    post_ids: List[str] = Query(..., description="List of Instagram post IDs to extract from"),
    match_to_store: bool = Query(default=True, description="Match extracted items to store products"),
    similarity_threshold: float = Query(default=0.7, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db)
):
    """
    Extract fashion items from multiple Instagram posts in batch.
    """
    start_time = time.time()
    results = []
    errors = []
    
    extraction_service = SemanticExtractionService()
    post_repo = InstagramPostRepository(db)
    item_repo = ExtractedItemRepository(db)
    
    for post_id in post_ids:
        try:
            post = await post_repo.get_post_by_id(post_id)
            if not post:
                errors.append({"post_id": post_id, "error": "Post not found"})
                continue
            
            extracted_items = await extraction_service.extract_items_from_post(
                post=post,
                match_to_store=match_to_store,
                similarity_threshold=similarity_threshold
            )
            
            if extracted_items:
                saved_count = await item_repo.save_batch_items(extracted_items)
                results.append({
                    "post_id": post_id,
                    "items_extracted": saved_count,
                    "success": True
                })
            else:
                results.append({
                    "post_id": post_id,
                    "items_extracted": 0,
                    "success": True
                })
        
        except Exception as e:
            logger.error(f"Error processing post {post_id}: {e}")
            errors.append({"post_id": post_id, "error": str(e)})
    
    total_items = sum(r.get("items_extracted", 0) for r in results)
    processing_time = (time.time() - start_time) * 1000
    
    return {
        "success": True,
        "message": f"Processed {len(post_ids)} posts, extracted {total_items} items",
        "posts_processed": len(results),
        "posts_failed": len(errors),
        "total_items_extracted": total_items,
        "results": results,
        "errors": errors,
        "processing_time_ms": processing_time
    }


@router.get("/extracted-items", response_model=ExtractedItemsPaginatedResponse, tags=["extraction"])
async def get_extracted_items(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    brand: Optional[str] = Query(default=None, description="Filter by brand"),
    has_match: Optional[bool] = Query(default=None, description="Filter by whether item has store match"),
    sort_by: str = Query(default="extraction_date", description="Sort field: extraction_date, confidence, match_score"),
    sort_order: str = Query(default="desc", description="Sort order: asc or desc"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of extracted fashion items.
    """
    try:
        item_repo = ExtractedItemRepository(db)
        items, total_count = await item_repo.get_items_paginated(
            page=page,
            page_size=page_size,
            category=category,
            brand=brand,
            has_match=has_match,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        item_schemas = [ExtractedItemSchema(**item.to_dict()) for item in items]
        
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0
        
        pagination_meta = PaginationMeta(
            current_page=page,
            page_size=page_size,
            total_items=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
        
        filter_msg = ""
        if category:
            filter_msg += f" category={category}"
        if brand:
            filter_msg += f" brand={brand}"
        if has_match is not None:
            filter_msg += f" has_match={has_match}"
        
        message = f"Retrieved {len(items)} extracted items (page {page} of {total_pages}){filter_msg}"
        
        return ExtractedItemsPaginatedResponse(
            success=True,
            message=message,
            items=item_schemas,
            pagination=pagination_meta
        )
    
    except Exception as e:
        logger.error(f"Error getting extracted items: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving extracted items: {str(e)}"
        )


@router.get("/extracted-items/{item_id}", response_model=ExtractedItemWithMatchesResponse, tags=["extraction"])
async def get_extracted_item(
    item_id: str,
    include_matches: bool = Query(default=True, description="Include matched store products"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single extracted fashion item with details and matched products.
    """
    try:
        item_repo = ExtractedItemRepository(db)
        item = await item_repo.get_item_by_id(item_id)
        
        if not item:
            raise HTTPException(status_code=404, detail=f"Extracted item not found: {item_id}")
        
        item_schema = ExtractedItemSchema(**item.to_dict())
        
        # Get matched products if requested
        matched_products = None
        if include_matches and item.matched_store_products:
            # Here you would fetch full product details from your store
            # For now, we'll return the basic match info
            from services.vector_db_service import VectorDBService
            vector_db = VectorDBService()
            
            matched_products = []
            for match in item.matched_store_products[:5]:  # Top 5 matches
                try:
                    # Get product details from vector DB
                    # This is a simplified version - you may need to adjust based on your product storage
                    matched_products.append({
                        "product_id": match["product_id"],
                        "similarity_score": match["similarity_score"],
                        "match_reasoning": match.get("match_reasoning", "Visual similarity")
                    })
                except Exception as e:
                    logger.warning(f"Error fetching product {match['product_id']}: {e}")
        
        return ExtractedItemWithMatchesResponse(
            success=True,
            message="Extracted item retrieved successfully",
            item=item_schema,
            matched_products=matched_products
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting extracted item: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving item: {str(e)}"
        )


@router.get("/extracted-items/post/{post_id}", tags=["extraction"])
async def get_extracted_items_for_post(
    post_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all extracted items for a specific Instagram post.
    """
    try:
        item_repo = ExtractedItemRepository(db)
        items = await item_repo.get_items_by_post_id(post_id)
        
        item_schemas = [ExtractedItemSchema(**item.to_dict()) for item in items]
        
        return {
            "success": True,
            "message": f"Found {len(items)} extracted items for post {post_id}",
            "post_id": post_id,
            "items": item_schemas,
            "total": len(items)
        }
    
    except Exception as e:
        logger.error(f"Error getting items for post: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving items: {str(e)}"
        )


@router.get("/extracted-items/matches", tags=["extraction"])
async def get_items_with_matches(
    limit: int = Query(default=20, ge=1, le=100),
    min_match_score: float = Query(default=0.7, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get extracted items that have been matched to store products.
    Useful for displaying similar products on the frontend.
    """
    try:
        item_repo = ExtractedItemRepository(db)
        items = await item_repo.get_items_with_matches(limit=limit, min_match_score=min_match_score)
        
        item_schemas = [ExtractedItemSchema(**item.to_dict()) for item in items]
        
        return {
            "success": True,
            "message": f"Found {len(items)} items with store matches",
            "items": item_schemas,
            "total": len(items)
        }
    
    except Exception as e:
        logger.error(f"Error getting items with matches: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving items: {str(e)}"
        )


@router.delete("/extracted-items/post/{post_id}", tags=["extraction"])
async def delete_extracted_items_for_post(
    post_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete all extracted items for a specific Instagram post.
    """
    try:
        item_repo = ExtractedItemRepository(db)
        deleted_count = await item_repo.delete_items_by_post_id(post_id)
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} extracted items for post {post_id}",
            "post_id": post_id,
            "deleted_count": deleted_count
        }
    
    except Exception as e:
        logger.error(f"Error deleting items for post: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting items: {str(e)}"
        )

