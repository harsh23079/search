"""Qdrant vector database service for similarity search."""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any, Optional
import numpy as np
from loguru import logger
from config import settings
from models.schemas import ProductInfo, SimilarProduct


class VectorDBService:
    """Service for managing vector database operations."""
    
    def __init__(self):
        """Initialize Qdrant client and collection."""
        try:
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port
            )
            logger.info(f"Connected to Qdrant at {settings.qdrant_host}:{settings.qdrant_port}")
            
            # Ensure collection exists
            self._ensure_collection()
        except Exception as e:
            logger.error(f"Error connecting to Qdrant: {e}")
            raise
    
    def _ensure_collection(self):
        """Ensure the collection exists, create if not."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if settings.qdrant_collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=settings.qdrant_collection_name,
                    vectors_config=VectorParams(
                        size=settings.qdrant_embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {settings.qdrant_collection_name}")
            else:
                logger.info(f"Collection {settings.qdrant_collection_name} already exists")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
    
    def add_product(
        self, 
        product_id: str,
        embedding: np.ndarray,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Add a product to the vector database.
        
        Args:
            product_id: Unique product identifier
            embedding: FashionCLIP embedding vector
            metadata: Product metadata
            
        Returns:
            True if successful
        """
        try:
            point = PointStruct(
                id=product_id,
                vector=embedding.tolist(),
                payload=metadata
            )
            
            self.client.upsert(
                collection_name=settings.qdrant_collection_name,
                points=[point]
            )
            
            logger.info(f"Added product {product_id} to vector database")
            return True
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            return False
    
    def search_similar(
        self,
        query_embedding: np.ndarray,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.5
    ) -> List[SimilarProduct]:
        """
        Search for similar products.
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            filters: Optional filters (category, price_range, etc.)
            score_threshold: Minimum similarity score
            
        Returns:
            List of similar products
        """
        try:
            search_results = self.client.search(
                collection_name=settings.qdrant_collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit,
                score_threshold=score_threshold,
                query_filter=None  # Can add filter support here
            )
            
            similar_products = []
            for result in search_results:
                payload = result.payload
                product_info = ProductInfo(
                    product_id=payload.get("product_id", str(result.id)),
                    name=payload.get("name", "Unknown"),
                    brand=payload.get("brand"),
                    price=payload.get("price") or 0.0,
                    currency=payload.get("currency", "INR"),
                    image_url=payload.get("image_url"),
                    in_stock=payload.get("in_stock", True)
                )
                
                similar_product = SimilarProduct(
                    product_id=product_info.product_id,
                    similarity_score=float(result.score),
                    product_info=product_info,
                    match_reasoning=self._generate_reasoning(payload, result.score),
                    key_similarities=payload.get("key_similarities", [])
                )
                similar_products.append(similar_product)
            
            return similar_products
        except Exception as e:
            logger.error(f"Error searching similar products: {e}")
            return []
    
    def _generate_reasoning(self, payload: Dict[str, Any], score: float) -> str:
        """Generate match reasoning based on metadata and score."""
        category = payload.get("category", "unknown")
        subcategory = payload.get("subcategory", "unknown")
        colors = payload.get("colors", [])
        
        reasoning = f"High visual similarity ({score:.2%})"
        if colors:
            reasoning += f" with matching colors: {', '.join(colors[:2])}"
        if subcategory != "unknown":
            reasoning += f". Same {subcategory} type."
        
        return reasoning
    
    def get_all_products(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all products from the database.
        
        Args:
            limit: Maximum number of products to return
            offset: Number of products to skip
            
        Returns:
            List of product dictionaries with all metadata
        """
        try:
            from qdrant_client.models import ScrollRequest
            
            # Scroll through all points
            scroll_result = self.client.scroll(
                collection_name=settings.qdrant_collection_name,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            products = []
            for point in scroll_result[0]:  # scroll_result is a tuple (points, next_page_offset)
                payload = point.payload or {}
                
                # Extract description from various possible fields
                description = (
                    payload.get("description") or 
                    payload.get("title") or 
                    payload.get("product_description") or
                    ""
                )
                
                # Build product dict with all fields
                product = {
                    "product_id": payload.get("product_id", str(point.id)),
                    "id": str(point.id),
                    "name": payload.get("name", "Unknown"),
                    "description": description,
                    "brand": payload.get("brand"),
                    "price": payload.get("price") or 0.0,  # Default to 0.0 if None, but should be set during ingestion
                    "currency": payload.get("currency", "INR"),
                    "image_url": payload.get("image_url"),
                    "in_stock": payload.get("in_stock", True),
                    "category": payload.get("category"),
                    "subcategory": payload.get("subcategory"),
                    "colors": payload.get("colors", []),
                    "style_tags": payload.get("style_tags", []),
                    # Include all other metadata fields (excluding already extracted fields)
                    "metadata": {k: v for k, v in payload.items() 
                               if k not in ["product_id", "name", "description", "title", 
                                           "product_description", "brand", "price", 
                                           "currency", "image_url", "in_stock", 
                                           "category", "subcategory", "colors", "style_tags"]}
                }
                products.append(product)
            
            return products
        except Exception as e:
            logger.error(f"Error getting all products: {e}")
            return []
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single product by ID.
        
        Args:
            product_id: Product ID to retrieve
            
        Returns:
            Product dictionary or None if not found
        """
        try:
            # Try to retrieve by point ID first
            result = self.client.retrieve(
                collection_name=settings.qdrant_collection_name,
                ids=[product_id],
                with_payload=True,
                with_vectors=False
            )
            
            if not result or len(result) == 0:
                # If not found by ID, try searching by product_id in payload
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                
                scroll_result = self.client.scroll(
                    collection_name=settings.qdrant_collection_name,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="product_id",
                                match=MatchValue(value=product_id)
                            )
                        ]
                    ),
                    limit=1,
                    with_payload=True,
                    with_vectors=False
                )
                
                if scroll_result[0] and len(scroll_result[0]) > 0:
                    result = scroll_result[0]
                else:
                    return None
            
            point = result[0]
            payload = point.payload or {}
            
            # Extract description from various possible fields
            description = (
                payload.get("description") or 
                payload.get("title") or 
                payload.get("product_description") or
                ""
            )
            
            # Build product dict with all fields
            product = {
                "product_id": payload.get("product_id", str(point.id)),
                "id": str(point.id),
                "name": payload.get("name", "Unknown"),
                "description": description,
                "brand": payload.get("brand"),
                "price": payload.get("price", 0.0),
                "currency": payload.get("currency", "INR"),
                "image_url": payload.get("image_url"),
                "in_stock": payload.get("in_stock", True),
                "category": payload.get("category"),
                "subcategory": payload.get("subcategory"),
                "colors": payload.get("colors", []),
                "style_tags": payload.get("style_tags", []),
                # Include all other metadata fields
                "metadata": {k: v for k, v in payload.items() 
                           if k not in ["product_id", "name", "description", "title", 
                                       "product_description", "brand", "price", 
                                       "currency", "image_url", "in_stock", 
                                       "category", "subcategory", "colors", "style_tags"]}
            }
            
            return product
        except Exception as e:
            logger.error(f"Error getting product by ID {product_id}: {e}")
            return None
    
    def get_total_count(self) -> int:
        """Get total number of products in the database."""
        try:
            collection_info = self.client.get_collection(settings.qdrant_collection_name)
            return collection_info.points_count
        except Exception as e:
            logger.error(f"Error getting product count: {e}")
            return 0

