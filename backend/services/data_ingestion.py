"""Data ingestion service for training on custom CSV data."""
import pandas as pd
import requests
from PIL import Image
import io
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger
from tqdm import tqdm
import time

from config import settings
from models.schemas import Category
from services import (
    get_embedding_service,
    get_detection_service,
    VectorDBService
)


class DataIngestionService:
    """Service for ingesting and indexing product data from CSV."""
    
    def __init__(self):
        """Initialize data ingestion service."""
        self.embedding_service = get_embedding_service()
        self.detection_service = get_detection_service()
        self.vector_db = VectorDBService()
        logger.info("Data ingestion service initialized")
    
    def ingest_from_csv(
        self,
        csv_path: str,
        image_url_column: str = "image_url",
        product_name_column: str = "product_name",
        category_column: str = "category",
        validate_categories: bool = True,
        batch_size: int = 10,
        skip_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Ingest products from CSV file.
        
        Args:
            csv_path: Path to CSV file
            image_url_column: Column name for image URLs
            product_name_column: Column name for product names
            category_column: Column name for categories
            validate_categories: Whether to validate/correct categories using detection model
            batch_size: Number of products to process in each batch
            skip_existing: Skip products that already exist in database
            
        Returns:
            Statistics about ingestion process
        """
        try:
            logger.info(f"Loading CSV from {csv_path}")
            df = pd.read_csv(csv_path)
            
            logger.info(f"Loaded {len(df)} products from CSV")
            
            # Validate required columns
            required_columns = [image_url_column, product_name_column]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            stats = {
                "total": len(df),
                "processed": 0,
                "successful": 0,
                "failed": 0,
                "category_corrected": 0,
                "skipped": 0,
                "errors": []
            }
            
            # Process in batches
            for i in tqdm(range(0, len(df), batch_size), desc="Processing batches"):
                batch = df.iloc[i:i+batch_size]
                batch_stats = self._process_batch(
                    batch,
                    image_url_column,
                    product_name_column,
                    category_column,
                    validate_categories,
                    skip_existing
                )
                
                # Update stats
                stats["processed"] += batch_stats["processed"]
                stats["successful"] += batch_stats["successful"]
                stats["failed"] += batch_stats["failed"]
                stats["category_corrected"] += batch_stats["category_corrected"]
                stats["skipped"] += batch_stats["skipped"]
                stats["errors"].extend(batch_stats["errors"])
            
            logger.info(f"Ingestion complete: {stats['successful']}/{stats['total']} successful")
            return stats
            
        except Exception as e:
            logger.error(f"Error ingesting from CSV: {e}")
            raise
    
    def _process_batch(
        self,
        batch: pd.DataFrame,
        image_url_column: str,
        product_name_column: str,
        category_column: str,
        validate_categories: bool,
        skip_existing: bool
    ) -> Dict[str, Any]:
        """Process a batch of products."""
        batch_stats = {
            "processed": len(batch),
            "successful": 0,
            "failed": 0,
            "category_corrected": 0,
            "skipped": 0,
            "errors": []
        }
        
        for _, row in batch.iterrows():
            try:
                # Extract product data
                image_url = row[image_url_column]
                product_name = row[product_name_column]
                csv_category = row.get(category_column, "unknown")
                
                # Generate product ID
                product_id = self._generate_product_id(product_name, image_url)
                
                # Skip if exists
                if skip_existing and self._product_exists(product_id):
                    batch_stats["skipped"] += 1
                    continue
                
                # Download and process image
                image = self._download_image(image_url)
                if image is None:
                    batch_stats["failed"] += 1
                    batch_stats["errors"].append(f"Failed to download image: {image_url}")
                    continue
                
                # Detect and validate category
                category_info = self._detect_and_validate_category(
                    image, csv_category, validate_categories
                )
                
                # Check if category_info is valid
                if not isinstance(category_info, dict) or category_info.get("category") is None:
                    batch_stats["failed"] += 1
                    batch_stats["errors"].append(f"Could not detect category for: {product_name}")
                    continue
                
                # Ensure we have the required fields
                detected_category = category_info.get("detected_category")
                csv_category_val = category_info.get("csv_category", csv_category)
                
                if not detected_category:
                    batch_stats["failed"] += 1
                    batch_stats["errors"].append(f"Could not detect category for: {product_name}")
                    continue
                
                category_corrected = csv_category_val != detected_category
                if category_corrected:
                    batch_stats["category_corrected"] += 1
                    logger.info(
                        f"Category corrected: {product_name} - "
                        f"CSV: {csv_category_val} -> "
                        f"Detected: {detected_category}"
                    )
                
                # Generate embedding
                embedding = self.embedding_service.encode_image(image)
                
                # Get description/title from CSV - build comprehensive description
                description_parts = []
                
                # Add title (product name)
                if product_name:
                    description_parts.append(product_name)
                
                # Add brand if available
                brand = None
                for brand_col in ["brand", "brand_name", "manufacturer"]:
                    if brand_col in row.index and pd.notna(row[brand_col]):
                        brand_val = row[brand_col]
                        if hasattr(brand_val, 'item'):
                            brand_val = brand_val.item()
                        brand = str(brand_val).strip()
                        if brand and brand.lower() not in ["none", "null", ""]:
                            description_parts.append(f"by {brand}")
                            break
                
                # Add subcategory/model if available
                for subcat_col in ["sub_category", "model", "product_type"]:
                    if subcat_col in row.index and pd.notna(row[subcat_col]):
                        subcat_val = row[subcat_col]
                        if hasattr(subcat_val, 'item'):
                            subcat_val = subcat_val.item()
                        subcat_str = str(subcat_val).strip()
                        if subcat_str and subcat_str.lower() not in ["none", "null", ""]:
                            description_parts.append(subcat_str)
                            break
                
                # Add colorways if available
                if "colorways" in row.index and pd.notna(row["colorways"]):
                    colorway_val = row["colorways"]
                    if hasattr(colorway_val, 'item'):
                        colorway_val = colorway_val.item()
                    colorway_str = str(colorway_val).strip()
                    if colorway_str and colorway_str.lower() not in ["none", "null", ""]:
                        description_parts.append(f"in {colorway_str}")
                
                # Build final description
                description = ". ".join(description_parts) if description_parts else product_name
                
                # Extract brand first (needed for price estimation)
                brand = None
                for brand_col in ["brand", "brand_name", "manufacturer"]:
                    if brand_col in row.index and pd.notna(row[brand_col]):
                        brand_val = row[brand_col]
                        if hasattr(brand_val, 'item'):
                            brand_val = brand_val.item()
                        brand = str(brand_val).strip()
                        if brand and brand.lower() not in ["none", "null", ""]:
                            break
                
                # Add price if available (check multiple possible column names with better parsing)
                price = None
                for price_col in ["lowest_price", "price", "cost", "selling_price"]:
                    if price_col in row.index and pd.notna(row[price_col]):
                        try:
                            price_val = row[price_col]
                            # Handle pandas Series/DataFrame values
                            if hasattr(price_val, 'item'):
                                price_val = price_val.item()
                            # Convert to string first to handle any formatting
                            price_str = str(price_val).strip()
                            # Remove any currency symbols or commas
                            price_str = price_str.replace(',', '').replace('₹', '').replace('$', '').replace('€', '').strip()
                            if price_str and price_str.lower() not in ["none", "null", "nan", ""]:
                                price_float = float(price_str)
                                # IMPORTANT: Only use CSV price if it's > 0, otherwise use estimation
                                if price_float > 0:
                                    price = price_float
                                    logger.debug(f"Using CSV price {price} from {price_col} for {product_name}")
                                    break
                                # If CSV has 0, skip it and use estimation later
                        except (ValueError, TypeError) as e:
                            logger.debug(f"Could not parse price from {price_col}: {price_val}, error: {e}")
                            continue
                
                # If price is still None or 0, try to extract from description
                if (price is None or price == 0) and description:
                    import re
                    # Look for price patterns in description (e.g., "₹50,000", "$100", "5000 INR")
                    price_patterns = [
                        r'₹\s*([\d,]+)',  # ₹50,000
                        r'\$\s*([\d,]+)',  # $100
                        r'([\d,]+)\s*(?:INR|USD|EUR|rupees?)',  # 5000 INR
                        r'price[:\s]+([\d,]+)',  # price: 5000
                        r'cost[:\s]+([\d,]+)',  # cost: 5000
                    ]
                    for pattern in price_patterns:
                        match = re.search(pattern, description, re.IGNORECASE)
                        if match:
                            try:
                                price_str = match.group(1).replace(',', '')
                                price = float(price_str)
                                if price > 0:
                                    logger.debug(f"Extracted price {price} from description for {product_name}")
                                    break
                            except (ValueError, IndexError):
                                continue
                
                # If still no price, use category-based default estimates
                if (price is None or price == 0):
                    # Estimate based on category and brand (rough estimates)
                    category_lower = (csv_category or "").lower()
                    brand_lower = (brand or "").lower() if brand else ""
                    
                    # Premium brands
                    if any(b in brand_lower for b in ["tag heuer", "rolex", "omega", "cartier", "patek"]):
                        price = 50000.0  # Default for luxury watches
                    elif any(b in brand_lower for b in ["gucci", "prada", "versace", "balenciaga", "valentino"]):
                        price = 30000.0  # Default for luxury fashion
                    elif any(b in brand_lower for b in ["nike", "adidas", "puma"]):
                        if "footwear" in category_lower or "shoes" in category_lower:
                            price = 8000.0  # Default for sneakers
                        else:
                            price = 5000.0  # Default for sportswear
                    elif "watches" in category_lower:
                        price = 15000.0  # Default for watches
                    elif "footwear" in category_lower or "shoes" in category_lower:
                        price = 5000.0  # Default for shoes
                    elif "bags" in category_lower:
                        price = 10000.0  # Default for bags
                    elif "accessories" in category_lower:
                        price = 3000.0  # Default for accessories
                    else:
                        price = 2000.0  # Default for clothing
                    
                    logger.debug(f"Using estimated price {price} for {product_name} (category: {csv_category}, brand: {brand})")
                
                # Final check: Ensure price is ALWAYS set (use estimated if CSV had 0 or None)
                if price is None or price == 0:
                    # Apply estimation - this should always run if CSV had 0
                    category_lower = (csv_category or "").lower()
                    brand_lower = (brand or "").lower() if brand else ""
                    
                    # Premium brands get higher estimates
                    if any(b in brand_lower for b in ["tag heuer", "rolex", "omega", "cartier", "patek"]):
                        price = 50000.0  # Luxury watches
                        logger.info(f"Estimated price {price} for luxury watch: {product_name}")
                    elif any(b in brand_lower for b in ["gucci", "prada", "versace", "balenciaga", "valentino", "saint laurent"]):
                        price = 30000.0  # Luxury fashion
                    elif any(b in brand_lower for b in ["nike", "adidas", "puma"]):
                        if "footwear" in category_lower or "shoes" in category_lower:
                            price = 8000.0  # Sneakers
                        else:
                            price = 5000.0  # Sportswear
                    elif "watches" in category_lower:
                        price = 15000.0  # Regular watches
                    elif "footwear" in category_lower or "shoes" in category_lower:
                        price = 5000.0  # Shoes
                    elif "bags" in category_lower:
                        price = 10000.0  # Bags
                    elif "accessories" in category_lower:
                        price = 3000.0  # Accessories
                    else:
                        price = 2000.0  # Clothing
                    
                    logger.info(f"Using estimated price {price} for {product_name} (CSV had 0, category: {csv_category}, brand: {brand})")
                
                # Ensure price is never None or 0 at this point
                if price is None or price <= 0:
                    price = 2000.0  # Absolute fallback
                    logger.warning(f"Price was still None/0 for {product_name}, using fallback {price}")
                
                # Prepare metadata
                metadata = {
                    "product_id": product_id,
                    "name": product_name,
                    "description": description,
                    "title": product_name,  # Also store title for backward compatibility
                    "category": detected_category,
                    "subcategory": category_info.get("subcategory", "unknown"),
                    "csv_category": csv_category,  # Keep original for reference
                    "category_corrected": category_corrected,
                    "image_url": image_url,
                    "colors": category_info.get("colors", []),
                    "style_tags": category_info.get("style_tags", []),
                    "confidence": category_info.get("confidence", 0.0),
                    "brand": brand,
                    "price": float(price),  # Always set a price (estimated if CSV had 0)
                }
                
                # Add currency
                currency = "INR"  # Default
                if "currency" in row.index and pd.notna(row["currency"]):
                    currency_val = row["currency"]
                    if hasattr(currency_val, 'item'):
                        currency_val = currency_val.item()
                    currency = str(currency_val)
                metadata["currency"] = currency
                
                # Store all other metadata columns (tags, attributes, etc.)
                excluded_cols = {
                    image_url_column, product_name_column, category_column,
                    "price", "lowest_price", "cost", "brand", "brand_name", 
                    "currency", "image_url", "product_name"
                }
                
                # Add all other columns as metadata
                # Convert row to dict to avoid pandas Series indexing issues
                row_dict = row.to_dict() if hasattr(row, 'to_dict') else dict(row.items())
                for col_name, col_value in row_dict.items():
                    if col_name not in excluded_cols and pd.notna(col_value):
                        try:
                            # Convert pandas values to Python native types
                            if hasattr(col_value, 'item'):
                                try:
                                    col_value = col_value.item()
                                except (ValueError, AttributeError):
                                    col_value = str(col_value)
                            elif isinstance(col_value, (pd.Timestamp, pd.Timedelta)):
                                col_value = str(col_value)
                            elif isinstance(col_value, str):
                                # Already a string, keep as is
                                pass
                            else:
                                # Convert to string for safety
                                col_value = str(col_value)
                            
                            # Skip if value is empty or None
                            if col_value is None or (isinstance(col_value, str) and col_value.strip() == ""):
                                continue
                            
                            # Store nested tags as nested dict
                            if "." in col_name and isinstance(metadata, dict):
                                # Handle tags.visual.color.primary.value format
                                parts = col_name.split(".")
                                current = metadata
                                nested_path_valid = True
                                
                                # Navigate/create nested structure
                                for i, part in enumerate(parts[:-1]):
                                    # Ensure current is always a dict
                                    if not isinstance(current, dict):
                                        nested_path_valid = False
                                        break
                                    
                                    if part not in current:
                                        # Create new dict at this level
                                        current[part] = {}
                                        current = current[part]
                                    elif isinstance(current[part], dict):
                                        # Existing dict, move into it
                                        current = current[part]
                                    else:
                                        # Conflict: key exists but is not a dict
                                        # Store as flat key with original name
                                        nested_path_valid = False
                                        break
                                
                                # Set the final value if path is valid
                                if nested_path_valid and isinstance(current, dict):
                                    current[parts[-1]] = col_value
                                else:
                                    # Fallback: store as flat key
                                    metadata[col_name] = col_value
                            else:
                                metadata[col_name] = col_value
                        except Exception as e:
                            # If anything goes wrong, store as flat key
                            logger.debug(f"Error processing column {col_name}: {e}, storing as flat key")
                            try:
                                metadata[col_name] = str(col_value) if col_value is not None else None
                            except:
                                # Last resort: skip this column
                                pass
                
                # Index in vector database
                success = self.vector_db.add_product(
                    product_id=product_id,
                    embedding=embedding,
                    metadata=metadata
                )
                
                if success:
                    batch_stats["successful"] += 1
                else:
                    batch_stats["failed"] += 1
                    batch_stats["errors"].append(f"Failed to index: {product_name}")
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                batch_stats["failed"] += 1
                error_msg = f"Error processing {product_name}: {str(e)}"
                batch_stats["errors"].append(error_msg)
                logger.error(error_msg)
        
        return batch_stats
    
    def _download_image(self, url: str, timeout: int = 10) -> Optional[Image.Image]:
        """Download image from URL."""
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            image = Image.open(io.BytesIO(response.content))
            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            return image
        except Exception as e:
            logger.warning(f"Failed to download image from {url}: {e}")
            return None
    
    def _detect_and_validate_category(
        self,
        image: Image.Image,
        csv_category: str,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Detect category from image and optionally validate against CSV category.
        
        Returns:
            Dictionary with category information
        """
        try:
            # Run detection
            detected_items = self.detection_service.detect_items(image)
            
            if not detected_items:
                # Fallback: try to map CSV category
                category = self._map_category_from_string(csv_category)
                return {
                    "category": category,
                    "detected_category": category.value if category else None,
                    "csv_category": csv_category,
                    "subcategory": "unknown",
                    "confidence": 0.5,
                    "colors": [],
                    "style_tags": []
                }
            
            # Use the most confident detection
            best_item = max(detected_items, key=lambda x: x.confidence)
            
            detected_category = best_item.category.value
            detected_subcategory = best_item.subcategory
            
            # Validate/correct if needed
            csv_category_mapped = self._map_category_from_string(csv_category)
            csv_category_value = csv_category_mapped.value if csv_category_mapped else None
            
            if validate and csv_category_value and csv_category_value != detected_category:
                # Trust CSV category more - only override if detection confidence is very high (>0.9)
                # and CSV category mapping might be ambiguous
                if best_item.confidence > 0.9 and csv_category_value == "clothing":
                    # Very high confidence detection might be correct even if CSV says clothing
                    # (e.g., CSV might have wrong category)
                    logger.debug(
                        f"Category mismatch: CSV={csv_category_value}, "
                        f"Detected={detected_category} (confidence={best_item.confidence}) - Using detected"
                    )
                    final_category = detected_category
                else:
                    # Trust CSV category - it's usually more accurate for product catalogs
                    logger.debug(
                        f"Category mismatch: CSV={csv_category_value}, "
                        f"Detected={detected_category} (confidence={best_item.confidence}) - Using CSV"
                    )
                    final_category = csv_category_value
            elif csv_category_value:
                # CSV category exists and matches detected, use it
                final_category = csv_category_value
            else:
                # No CSV category, use detected
                final_category = detected_category
            
            return {
                "category": Category(final_category) if final_category else None,
                "detected_category": detected_category,
                "csv_category": csv_category_value or csv_category,
                "subcategory": detected_subcategory,
                "confidence": best_item.confidence,
                "colors": best_item.colors,
                "style_tags": best_item.style_tags
            }
            
        except Exception as e:
            logger.error(f"Error detecting category: {e}")
            # Fallback to CSV category
            category = self._map_category_from_string(csv_category)
            return {
                "category": category,
                "detected_category": category.value if category else None,
                "csv_category": csv_category,
                "subcategory": "unknown",
                "confidence": 0.3,
                "colors": [],
                "style_tags": []
            }
    
    def _map_category_from_string(self, category_str: str) -> Optional[Category]:
        """Map string category to Category enum."""
        if not category_str or pd.isna(category_str):
            return None
        
        category_lower = str(category_str).lower().strip()
        
        # Direct mapping
        category_mapping = {
            "clothing": Category.CLOTHING,
            "apparel": Category.CLOTHING,
            "tops": Category.CLOTHING,
            "bottoms": Category.CLOTHING,
            "outerwear": Category.CLOTHING,
            "shoes": Category.SHOES,
            "footwear": Category.SHOES,
            "casual footwear": Category.SHOES,
            "formal footwear": Category.SHOES,
            "sneakers": Category.SHOES,
            "sandals": Category.SHOES,
            "sandals & open-toe footwear": Category.SHOES,
            "boots": Category.SHOES,
            "bags": Category.BAGS,
            "handbags": Category.BAGS,
            "luggage": Category.BAGS,
            "accessories": Category.ACCESSORIES,
            "accessory": Category.ACCESSORIES,
            "watches": Category.ACCESSORIES,
            "watch": Category.ACCESSORIES,
            "makeup & cosmetics": Category.ACCESSORIES,
        }
        
        if category_lower in category_mapping:
            return category_mapping[category_lower]
        
        # Try partial matching (check if any key is in the category string)
        for key, value in category_mapping.items():
            if key in category_lower or category_lower in key:
                return value
        
        # Check for "footwear" anywhere in the string (handles "casual footwear", etc.)
        if "footwear" in category_lower:
            return Category.SHOES
        
        # Check for watch-related terms
        if "watch" in category_lower:
            return Category.ACCESSORIES
        
        # Check for bag-related terms
        if "bag" in category_lower or "luggage" in category_lower:
            return Category.BAGS
        
        return None
    
    def _generate_product_id(self, product_name: str, image_url: str) -> str:
        """Generate unique product ID as UUID (Qdrant requires UUID or integer)."""
        import uuid
        # Use UUID v5 (deterministic) based on product name and image URL
        # This ensures same product always gets same ID
        namespace = uuid.NAMESPACE_URL
        id_string = f"{product_name}_{image_url}"
        product_uuid = uuid.uuid5(namespace, id_string)
        return str(product_uuid)
    
    def _product_exists(self, product_id: str) -> bool:
        """Check if product already exists in database."""
        try:
            # Try to retrieve product
            result = self.vector_db.client.retrieve(
                collection_name=settings.qdrant_collection_name,
                ids=[product_id]
            )
            return len(result) > 0
        except:
            return False

