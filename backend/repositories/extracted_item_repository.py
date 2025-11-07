"""Repository for extracted fashion item database operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc, desc, and_
from typing import List, Optional, Tuple
from loguru import logger
from models.extracted_fashion_item import ExtractedFashionItem


class ExtractedItemRepository:
    """Repository for extracted fashion item operations."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def save_item(self, item: ExtractedFashionItem) -> ExtractedFashionItem:
        """Save an extracted fashion item."""
        try:
            self.db.add(item)
            await self.db.commit()
            await self.db.refresh(item)
            logger.info(f"Saved extracted item: {item.id}")
            return item
        except Exception as e:
            logger.error(f"Error saving extracted item: {e}")
            await self.db.rollback()
            raise
    
    async def save_batch_items(self, items: List[ExtractedFashionItem]) -> int:
        """Save multiple extracted items in batch."""
        saved_count = 0
        for item in items:
            try:
                await self.save_item(item)
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving item in batch: {e}")
                continue
        return saved_count
    
    async def get_item_by_id(self, item_id: str) -> Optional[ExtractedFashionItem]:
        """Get an extracted item by ID."""
        try:
            result = await self.db.execute(
                select(ExtractedFashionItem).where(ExtractedFashionItem.id == item_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting item by ID: {e}")
            return None
    
    async def get_items_by_post_id(self, post_id: str) -> List[ExtractedFashionItem]:
        """Get all extracted items for a specific Instagram post."""
        try:
            result = await self.db.execute(
                select(ExtractedFashionItem)
                .where(ExtractedFashionItem.instagram_post_id == post_id)
                .order_by(desc(ExtractedFashionItem.extraction_confidence))
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting items by post ID: {e}")
            return []
    
    async def get_items_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        has_match: Optional[bool] = None,
        sort_by: str = "extraction_date",
        sort_order: str = "desc"
    ) -> Tuple[List[ExtractedFashionItem], int]:
        """Get paginated extracted items with optional filtering."""
        try:
            # Build query
            query = select(ExtractedFashionItem)
            
            # Apply filters
            conditions = []
            if category:
                conditions.append(ExtractedFashionItem.category == category)
            if brand:
                conditions.append(ExtractedFashionItem.brand == brand)
            if has_match is not None:
                if has_match:
                    conditions.append(ExtractedFashionItem.best_match_product_id.isnot(None))
                else:
                    conditions.append(ExtractedFashionItem.best_match_product_id.is_(None))
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Get total count
            count_query = select(func.count()).select_from(ExtractedFashionItem)
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            total_result = await self.db.execute(count_query)
            total_count = total_result.scalar() or 0
            
            # Apply sorting
            if sort_by == "confidence":
                sort_column = ExtractedFashionItem.extraction_confidence
            elif sort_by == "match_score":
                sort_column = ExtractedFashionItem.best_match_score
            else:  # default to extraction_date
                sort_column = ExtractedFashionItem.extraction_date
            
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
            
            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            result = await self.db.execute(query)
            items = result.scalars().all()
            
            return list(items), total_count
        except Exception as e:
            logger.error(f"Error getting paginated items: {e}")
            return [], 0
    
    async def get_items_with_matches(
        self,
        limit: int = 20,
        min_match_score: float = 0.7
    ) -> List[ExtractedFashionItem]:
        """Get extracted items that have store product matches above threshold."""
        try:
            result = await self.db.execute(
                select(ExtractedFashionItem)
                .where(
                    and_(
                        ExtractedFashionItem.best_match_product_id.isnot(None),
                        ExtractedFashionItem.best_match_score >= min_match_score
                    )
                )
                .order_by(desc(ExtractedFashionItem.best_match_score))
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting items with matches: {e}")
            return []
    
    async def delete_items_by_post_id(self, post_id: str) -> int:
        """Delete all extracted items for a specific post."""
        try:
            result = await self.db.execute(
                select(ExtractedFashionItem).where(
                    ExtractedFashionItem.instagram_post_id == post_id
                )
            )
            items = result.scalars().all()
            count = len(items)
            
            for item in items:
                await self.db.delete(item)
            
            await self.db.commit()
            logger.info(f"Deleted {count} extracted items for post {post_id}")
            return count
        except Exception as e:
            logger.error(f"Error deleting items by post ID: {e}")
            await self.db.rollback()
            return 0

