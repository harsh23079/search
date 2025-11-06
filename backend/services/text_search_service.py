"""Hybrid text search service using BM25 + Sentence-Transformers."""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from loguru import logger
import re
from qdrant_client import QdrantClient

from config import settings
from models.schemas import ProductInfo, SimilarProduct
from services.vector_db_service import VectorDBService


class TextSearchService:
    """Hybrid text search combining BM25 (keyword) and Sentence-Transformers (semantic)."""
    
    def __init__(self):
        """Initialize text search service with BM25 and Sentence-Transformers."""
        try:
            # Initialize Sentence-Transformer model for semantic search
            logger.info("Loading Sentence-Transformer model for semantic search...")
            self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence-Transformer model loaded successfully")
            
            # Initialize vector DB service
            self.vector_db = VectorDBService()
            
            # BM25 index will be built dynamically from product data
            self.bm25_index: Optional[BM25Okapi] = None
            self.product_corpus: List[Dict[str, Any]] = []
            self.product_texts: List[str] = []
            
            # Build initial index (lazy load on first search if needed)
            try:
                self._build_indices()
            except Exception as e:
                logger.warning(f"Could not build indices on initialization: {e}. Will build on first search.")
                self.bm25_index = None
                self.product_corpus = []
                self.product_texts = []
            
        except Exception as e:
            logger.error(f"Error initializing text search service: {e}")
            raise
    
    def _build_indices(self):
        """Build BM25 index from all products in database."""
        try:
            logger.info("Building BM25 index from product database...")
            
            # Fetch all products from Qdrant
            points, _ = self.vector_db.client.scroll(
                collection_name=settings.qdrant_collection_name,
                limit=10000  # Adjust based on your dataset size
            )
            
            self.product_corpus = []
            self.product_texts = []
            
            for point in points:
                payload = point.payload
                
                # Build searchable text from product metadata
                searchable_text = self._build_searchable_text(payload)
                
                self.product_corpus.append({
                    "product_id": str(point.id),
                    "payload": payload,
                    "text": searchable_text
                })
                self.product_texts.append(searchable_text)
            
            # Tokenize texts for BM25
            tokenized_corpus = [self._tokenize(text) for text in self.product_texts]
            
            # Build BM25 index
            if tokenized_corpus:
                self.bm25_index = BM25Okapi(tokenized_corpus)
                logger.info(f"Built BM25 index with {len(tokenized_corpus)} products")
            else:
                logger.warning("No products found to build BM25 index")
                self.bm25_index = None
                
        except Exception as e:
            logger.error(f"Error building indices: {e}")
            self.bm25_index = None
    
    def _build_searchable_text(self, payload: Dict[str, Any]) -> str:
        """Build searchable text from product metadata."""
        parts = []
        
        # Add product name
        if payload.get("name"):
            parts.append(str(payload.get("name")))
        
        # Add brand
        if payload.get("brand"):
            parts.append(str(payload.get("brand")))
        
        # Add category and subcategory
        if payload.get("category"):
            parts.append(str(payload.get("category")))
        if payload.get("subcategory"):
            parts.append(str(payload.get("subcategory")))
        
        # Add colors
        if payload.get("colors"):
            colors = payload.get("colors", [])
            if isinstance(colors, list):
                parts.extend([str(c) for c in colors if c])
        
        # Add style tags
        if payload.get("style_tags"):
            tags = payload.get("style_tags", [])
            if isinstance(tags, list):
                parts.extend([str(t) for t in tags if t])
        
        # Add description if available
        if payload.get("description"):
            parts.append(str(payload.get("description")))
        
        # Add other metadata fields that might be searchable
        for key in ["model", "colorways", "product_type", "gender"]:
            if payload.get(key):
                parts.append(str(payload.get(key)))
        
        return " ".join(parts).lower()
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25."""
        # Simple tokenization: split by whitespace and remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.lower().split()
        return [t for t in tokens if len(t) > 1]  # Filter out single characters
    
    def search(
        self,
        query: str,
        limit: int = 10,
        bm25_weight: float = 0.4,
        semantic_weight: float = 0.6,
        category: Optional[str] = None,
        min_score: float = 0.3
    ) -> List[SimilarProduct]:
        """
        Hybrid search combining BM25 (keyword) and Sentence-Transformers (semantic).
        
        Args:
            query: Search query text
            limit: Maximum number of results
            bm25_weight: Weight for BM25 scores (default: 0.4)
            semantic_weight: Weight for semantic scores (default: 0.6)
            category: Optional category filter
            min_score: Minimum combined score threshold
            
        Returns:
            List of similar products with hybrid scores
        """
        if not query or not query.strip():
            return []
        
        try:
            # Ensure indices are built
            if not self.bm25_index or not self.product_corpus:
                logger.info("Building text search indices on first search...")
                self._build_indices()
            
            # Get BM25 scores
            bm25_scores = self._get_bm25_scores(query)
            
            # Get semantic scores
            semantic_scores = self._get_semantic_scores(query)
            
            # Combine scores
            combined_results = self._combine_scores(
                bm25_scores,
                semantic_scores,
                bm25_weight,
                semantic_weight
            )
            
            # Filter and sort
            filtered_results = [
                (idx, score) for idx, score in combined_results.items()
                if score >= min_score
            ]
            filtered_results.sort(key=lambda x: x[1], reverse=True)
            
            # Apply category filter if specified
            if category:
                filtered_results = [
                    (idx, score) for idx, score in filtered_results
                    if self.product_corpus[idx]["payload"].get("category") == category
                ]
            
            # Limit results
            results = filtered_results[:limit]
            
            # Convert to SimilarProduct objects
            similar_products = []
            for idx, score in results:
                product_data = self.product_corpus[idx]
                payload = product_data["payload"]
                
                product_info = ProductInfo(
                    product_id=payload.get("product_id", product_data["product_id"]),
                    name=payload.get("name", "Unknown"),
                    brand=payload.get("brand"),
                    price=payload.get("price", 0.0),
                    currency=payload.get("currency", "INR"),
                    image_url=payload.get("image_url"),
                    in_stock=payload.get("in_stock", True)
                )
                
                similar_product = SimilarProduct(
                    product_id=product_info.product_id,
                    similarity_score=float(score),
                    product_info=product_info,
                    match_reasoning=self._generate_reasoning(payload, query, score),
                    key_similarities=self._extract_key_similarities(query, payload)
                )
                similar_products.append(similar_product)
            
            return similar_products
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
    
    def _get_bm25_scores(self, query: str) -> Dict[int, float]:
        """Get BM25 scores for query."""
        if not self.bm25_index:
            return {}
        
        try:
            # Tokenize query
            query_tokens = self._tokenize(query)
            
            if not query_tokens:
                return {}
            
            # Get BM25 scores
            scores = self.bm25_index.get_scores(query_tokens)
            
            # Normalize scores to [0, 1] range
            if len(scores) > 0:
                max_score = max(scores) if max(scores) > 0 else 1.0
                normalized_scores = {i: float(score / max_score) for i, score in enumerate(scores)}
            else:
                normalized_scores = {}
            
            return normalized_scores
            
        except Exception as e:
            logger.error(f"Error computing BM25 scores: {e}")
            return {}
    
    def _get_semantic_scores(self, query: str) -> Dict[int, float]:
        """Get semantic similarity scores using Sentence-Transformers."""
        try:
            # Encode query
            query_embedding = self.semantic_model.encode(query, convert_to_numpy=True)
            
            # Get embeddings for all products
            if not self.product_texts:
                return {}
            
            # Encode all product texts
            corpus_embeddings = self.semantic_model.encode(
                self.product_texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # Compute cosine similarity
            # Normalize embeddings
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            corpus_norms = corpus_embeddings / np.linalg.norm(corpus_embeddings, axis=1, keepdims=True)
            
            # Compute similarities
            similarities = np.dot(corpus_norms, query_norm)
            
            # Convert to dict and normalize to [0, 1]
            # Cosine similarity is already in [-1, 1], map to [0, 1]
            semantic_scores = {
                i: float((similarity + 1) / 2)
                for i, similarity in enumerate(similarities)
            }
            
            return semantic_scores
            
        except Exception as e:
            logger.error(f"Error computing semantic scores: {e}")
            return {}
    
    def _combine_scores(
        self,
        bm25_scores: Dict[int, float],
        semantic_scores: Dict[int, float],
        bm25_weight: float,
        semantic_weight: float
    ) -> Dict[int, float]:
        """Combine BM25 and semantic scores."""
        # Normalize weights
        total_weight = bm25_weight + semantic_weight
        if total_weight > 0:
            bm25_weight = bm25_weight / total_weight
            semantic_weight = semantic_weight / total_weight
        
        # Get all product indices
        all_indices = set(bm25_scores.keys()) | set(semantic_scores.keys())
        
        combined = {}
        for idx in all_indices:
            bm25_score = bm25_scores.get(idx, 0.0)
            semantic_score = semantic_scores.get(idx, 0.0)
            
            # Weighted combination
            combined_score = (bm25_weight * bm25_score) + (semantic_weight * semantic_score)
            combined[idx] = combined_score
        
        return combined
    
    def _generate_reasoning(self, payload: Dict[str, Any], query: str, score: float) -> str:
        """Generate match reasoning for product."""
        reasons = []
        
        # Check if query matches product name
        product_name = payload.get("name", "").lower()
        query_lower = query.lower()
        if any(word in product_name for word in query_lower.split()):
            reasons.append("product name match")
        
        # Check brand match
        brand = payload.get("brand", "").lower()
        if brand and brand in query_lower:
            reasons.append("brand match")
        
        # Check category match
        category = payload.get("category", "").lower()
        if category and category in query_lower:
            reasons.append("category match")
        
        # Score-based reasoning
        if score >= 0.8:
            reasons.append("high semantic similarity")
        elif score >= 0.6:
            reasons.append("good semantic similarity")
        
        if not reasons:
            reasons.append("moderate similarity")
        
        return f"Matched by: {', '.join(reasons)} (score: {score:.2%})"
    
    def _extract_key_similarities(self, query: str, payload: Dict[str, Any]) -> List[str]:
        """Extract key similarities between query and product."""
        similarities = []
        query_lower = query.lower()
        
        # Check name similarity
        name = payload.get("name", "").lower()
        if name and any(word in name for word in query_lower.split()):
            similarities.append(f"Name: {payload.get('name')}")
        
        # Check brand
        brand = payload.get("brand", "")
        if brand and brand.lower() in query_lower:
            similarities.append(f"Brand: {brand}")
        
        # Check category
        category = payload.get("category", "")
        if category and category.lower() in query_lower:
            similarities.append(f"Category: {category}")
        
        return similarities
    
    def refresh_indices(self):
        """Rebuild indices (call after new products are added)."""
        logger.info("Refreshing text search indices...")
        self._build_indices()
        logger.info("Indices refreshed successfully")


# Global instance
_text_search_service: Optional[TextSearchService] = None


def get_text_search_service() -> TextSearchService:
    """Get or create text search service instance."""
    global _text_search_service
    if _text_search_service is None:
        _text_search_service = TextSearchService()
    return _text_search_service

