"""Semantic extraction service for analyzing Instagram posts and extracting fashion items."""
import httpx
import re
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import io
from loguru import logger
import uuid
from datetime import datetime

from models.instagram_post import InstagramPost
from models.extracted_fashion_item import ExtractedFashionItem
from services import get_detection_service, get_embedding_service
from services.vector_db_service import VectorDBService
from models.schemas import Category, DetectedItem


class SemanticExtractionService:
    """Service for extracting fashion items from Instagram posts using image and text analysis."""
    
    # Common fashion brands to extract from text
    FASHION_BRANDS = [
        "nike", "adidas", "puma", "reebok", "converse", "vans",
        "gucci", "prada", "versace", "dolce", "gabbana", "armani",
        "zara", "h&m", "forever 21", "uniqlo", "gap",
        "rolex", "omega", "citizen", "seiko", "casio", "g-shock",
        "ray-ban", "oakley", "prada", "versace",
        "louis vuitton", "chanel", "hermes", "dior",
        "calvin klein", "tommy hilfiger", "ralph lauren",
        "yeezy", "jordan", "air max", "stan smith"
    ]
    
    # Fashion keywords for text analysis
    FASHION_KEYWORDS = {
        "watches": ["watch", "timepiece", "chronograph", "automatic", "quartz", "titanium"],
        "shoes": ["sneakers", "shoes", "boots", "sandals", "heels", "flats", "slippers"],
        "clothing": ["shirt", "t-shirt", "pants", "jeans", "dress", "jacket", "hoodie", "sweater"],
        "bags": ["bag", "handbag", "backpack", "purse", "tote", "clutch", "wallet"],
        "accessories": ["sunglasses", "hat", "cap", "belt", "bracelet", "necklace", "ring"]
    }
    
    def __init__(self):
        """Initialize semantic extraction service."""
        self.detection_service = get_detection_service()
        self.embedding_service = get_embedding_service()
        self.vector_db = VectorDBService()
        logger.info("Semantic extraction service initialized")
    
    async def extract_items_from_post(
        self, 
        post: InstagramPost,
        match_to_store: bool = True,
        similarity_threshold: float = 0.7
    ) -> List[ExtractedFashionItem]:
        """
        Extract fashion items from an Instagram post.
        
        Args:
            post: Instagram post to analyze
            match_to_store: Whether to match extracted items to store products
            similarity_threshold: Minimum similarity score for store matching
            
        Returns:
            List of extracted fashion items
        """
        extracted_items = []
        
        try:
            # Get image URL(s) from post
            image_urls = self._get_image_urls(post)
            
            if not image_urls:
                logger.warning(f"No images found for post {post.id}")
                return []
            
            # Process each image
            for idx, image_url in enumerate(image_urls):
                try:
                    # Download and process image
                    image = await self._download_image(image_url)
                    if image is None:
                        continue
                    
                    # Detect items in image
                    detected_items = self.detection_service.detect_items(image)
                    
                    # Analyze text (caption, hashtags, alt text)
                    text_features = self._analyze_text(post)
                    
                    # Combine image detection and text analysis
                    for detected_item in detected_items:
                        extracted_item = await self._create_extracted_item(
                            post=post,
                            detected_item=detected_item,
                            text_features=text_features,
                            image=image,
                            image_index=idx,
                            image_url=image_url  # Pass the image URL
                        )
                        
                        # Match to store products if requested
                        if match_to_store:
                            await self._match_to_store_products(
                                extracted_item,
                                similarity_threshold
                            )
                        
                        extracted_items.append(extracted_item)
                
                except Exception as e:
                    logger.error(f"Error processing image {idx} from post {post.id}: {e}")
                    continue
            
            # If no items detected from images, try text-only extraction
            if not extracted_items:
                extracted_items = await self._extract_from_text_only(
                    post, match_to_store, similarity_threshold
                )
            
            logger.info(f"Extracted {len(extracted_items)} items from post {post.id}")
            return extracted_items
            
        except Exception as e:
            logger.error(f"Error extracting items from post {post.id}: {e}")
            return []
    
    def _get_image_urls(self, post: InstagramPost) -> List[str]:
        """Get all image URLs from a post."""
        urls = []
        
        # Primary display URL
        if post.display_url:
            urls.append(post.display_url)
        
        # Images array
        if post.images:
            if isinstance(post.images, list):
                for img in post.images:
                    if isinstance(img, str):
                        urls.append(img)
                    elif isinstance(img, dict) and "url" in img:
                        urls.append(img["url"])
        
        # Child posts (for carousel)
        if post.child_posts:
            for child in post.child_posts:
                if isinstance(child, dict):
                    if "displayUrl" in child:
                        urls.append(child["displayUrl"])
                    elif "display_url" in child:
                        urls.append(child["display_url"])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url and url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls
    
    async def _download_image(self, url: str) -> Optional[Image.Image]:
        """Download image from URL."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content))
                return image
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return None
    
    def _analyze_text(self, post: InstagramPost) -> Dict[str, Any]:
        """Analyze text content (caption, hashtags, alt) to extract fashion information."""
        text_features = {
            "brand": None,
            "keywords": [],
            "hashtags_related": [],
            "item_name": None,
            "category_hints": []
        }
        
        # Combine all text sources
        text_sources = []
        if post.caption:
            text_sources.append(post.caption)
        if post.alt:
            text_sources.append(post.alt)
        
        combined_text = " ".join(text_sources).lower()
        
        # Extract brand
        for brand in self.FASHION_BRANDS:
            if brand.lower() in combined_text:
                text_features["brand"] = brand.title()
                break
        
        # Extract keywords and category hints
        for category, keywords in self.FASHION_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    text_features["keywords"].append(keyword)
                    if category not in text_features["category_hints"]:
                        text_features["category_hints"].append(category)
        
        # Extract relevant hashtags
        if post.hashtags:
            for hashtag in post.hashtags:
                hashtag_lower = hashtag.lower().replace("#", "")
                # Check if hashtag is fashion-related
                for category, keywords in self.FASHION_KEYWORDS.items():
                    if any(kw in hashtag_lower for kw in keywords):
                        text_features["hashtags_related"].append(hashtag)
                        break
        
        # Try to extract item name (simplified - look for quoted text or specific patterns)
        # This is a basic implementation - could be improved with NLP
        name_patterns = [
            r'"([^"]+)"',  # Quoted text
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Capitalized words
        ]
        for pattern in name_patterns:
            matches = re.findall(pattern, post.caption or "")
            if matches:
                text_features["item_name"] = matches[0]
                break
        
        return text_features
    
    async def _create_extracted_item(
        self,
        post: InstagramPost,
        detected_item: DetectedItem,
        text_features: Dict[str, Any],
        image: Image.Image,
        image_index: int,
        image_url: Optional[str] = None
    ) -> ExtractedFashionItem:
        """Create an ExtractedFashionItem from detected item and text features."""
        item_id = f"{post.id}_{image_index}_{uuid.uuid4().hex[:8]}"
        
        # Combine image detection and text analysis
        category = detected_item.category.value if detected_item.category else text_features.get("category_hints", [None])[0] or "accessories"
        
        # Use text brand if available, otherwise keep detection info
        brand = text_features.get("brand")
        item_name = text_features.get("item_name") or detected_item.subcategory
        
        # Generate embeddings
        image_embedding = None
        text_embedding = None
        
        try:
            image_embedding = self.embedding_service.encode_image(image).tolist()
            
            # Create text for embedding
            text_parts = []
            if item_name:
                text_parts.append(item_name)
            if brand:
                text_parts.append(brand)
            if detected_item.subcategory:
                text_parts.append(detected_item.subcategory)
            if text_features.get("keywords"):
                text_parts.extend(text_features["keywords"][:3])
            
            if text_parts:
                text_for_embedding = " ".join(text_parts)
                text_embedding = self.embedding_service.encode_text(text_for_embedding).tolist()
        except Exception as e:
            logger.warning(f"Error generating embeddings: {e}")
        
        # Calculate overall confidence
        extraction_confidence = detected_item.confidence
        if text_features.get("brand"):
            extraction_confidence = min(1.0, extraction_confidence + 0.1)
        
        extracted_item = ExtractedFashionItem(
            id=item_id,
            instagram_post_id=post.id,
            category=category,
            subcategory=detected_item.subcategory,
            colors=detected_item.colors,
            style_tags=detected_item.style_tags,
            pattern=detected_item.pattern,
            material=detected_item.material,
            bounding_box=detected_item.bounding_box,
            brand=brand,
            item_name=item_name,
            keywords=text_features.get("keywords", []),
            hashtags_related=text_features.get("hashtags_related", []),
            image_embedding=image_embedding,
            text_embedding=text_embedding,
            detection_confidence=detected_item.confidence,
            extraction_confidence=extraction_confidence,
            extraction_method="hybrid",
            extraction_date=datetime.utcnow(),
            image_url=image_url,  # URL of the specific image
            post_display_url=post.display_url,  # Original post display URL
            raw_extraction_data={
                "detected_item": detected_item.model_dump() if hasattr(detected_item, 'model_dump') else detected_item.dict(),
                "text_features": text_features,
                "image_index": image_index
            }
        )
        
        return extracted_item
    
    async def _match_to_store_products(
        self,
        extracted_item: ExtractedFashionItem,
        similarity_threshold: float = 0.7
    ):
        """Match extracted item to store products using vector similarity."""
        try:
            matched_products = []
            
            # Use image embedding if available, otherwise text embedding
            query_embedding = None
            if extracted_item.image_embedding:
                query_embedding = extracted_item.image_embedding
            elif extracted_item.text_embedding:
                query_embedding = extracted_item.text_embedding
            
            if not query_embedding:
                logger.warning(f"No embeddings available for item {extracted_item.id}")
                return
            
            # Convert list to numpy array if needed
            import numpy as np
            if isinstance(query_embedding, list):
                query_embedding = np.array(query_embedding)
            
            # Search for similar products with lower threshold to find more matches
            similar_products = self.vector_db.search_similar(
                query_embedding=query_embedding,
                limit=20,  # Get more candidates
                score_threshold=max(0.3, similarity_threshold - 0.2)  # Lower threshold for initial search
            )
            
            # Filter by threshold and store matches
            for product in similar_products:
                if product.similarity_score >= similarity_threshold:
                    matched_products.append({
                        "product_id": product.product_id,
                        "similarity_score": product.similarity_score,
                        "match_reasoning": product.match_reasoning
                    })
            
            if matched_products:
                # Sort by similarity score
                matched_products.sort(key=lambda x: x["similarity_score"], reverse=True)
                
                extracted_item.matched_store_products = matched_products
                extracted_item.best_match_product_id = matched_products[0]["product_id"]
                extracted_item.best_match_score = matched_products[0]["similarity_score"]
                
                logger.info(f"Matched item {extracted_item.id} to {len(matched_products)} store products")
        
        except Exception as e:
            logger.error(f"Error matching item to store products: {e}")
    
    async def _extract_from_text_only(
        self,
        post: InstagramPost,
        match_to_store: bool,
        similarity_threshold: float
    ) -> List[ExtractedFashionItem]:
        """Extract items from text only when image detection fails."""
        extracted_items = []
        
        try:
            text_features = self._analyze_text(post)
            
            # Only create item if we found significant text features
            if not (text_features.get("keywords") or text_features.get("brand")):
                return []
            
            # Determine category from text hints
            category = text_features.get("category_hints", ["accessories"])[0]
            
            item_id = f"{post.id}_text_{uuid.uuid4().hex[:8]}"
            
            # Generate text embedding
            text_parts = []
            if text_features.get("item_name"):
                text_parts.append(text_features["item_name"])
            if text_features.get("brand"):
                text_parts.append(text_features["brand"])
            if text_features.get("keywords"):
                text_parts.extend(text_features["keywords"][:5])
            
            text_embedding = None
            if text_parts:
                try:
                    text_for_embedding = " ".join(text_parts)
                    text_embedding = self.embedding_service.encode_text(text_for_embedding).tolist()
                except Exception as e:
                    logger.warning(f"Error generating text embedding: {e}")
            
            # Get image URL from post if available
            image_urls = self._get_image_urls(post)
            image_url = image_urls[0] if image_urls else None
            
            extracted_item = ExtractedFashionItem(
                id=item_id,
                instagram_post_id=post.id,
                category=category,
                subcategory=text_features.get("keywords", [None])[0],
                brand=text_features.get("brand"),
                item_name=text_features.get("item_name"),
                keywords=text_features.get("keywords", []),
                hashtags_related=text_features.get("hashtags_related", []),
                text_embedding=text_embedding,
                detection_confidence=0.5,  # Lower confidence for text-only
                extraction_confidence=0.6,
                extraction_method="text_analysis",
                extraction_date=datetime.utcnow(),
                image_url=image_url,
                post_display_url=post.display_url,
                raw_extraction_data={"text_features": text_features}
            )
            
            # Match to store if requested
            if match_to_store and text_embedding:
                await self._match_to_store_products(extracted_item, similarity_threshold)
            
            extracted_items.append(extracted_item)
            
        except Exception as e:
            logger.error(f"Error in text-only extraction: {e}")
        
        return extracted_items

