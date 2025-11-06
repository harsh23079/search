"""YOLOv8 fashion detection service with support for fashion-specific models."""
import os
from ultralytics import YOLO
from PIL import Image
import numpy as np
from typing import List, Dict, Any, Optional
from loguru import logger
from config import settings
from models.schemas import DetectedItem, Category

# Try to import ultralyticsplus for HuggingFace models
# Note: Requires separate environment due to version conflicts (see OPTION_B_SETUP.md)
ULTRALYTICSPLUS_AVAILABLE = False
YOLOPlus = None

try:
    from ultralyticsplus import YOLO as YOLOPlus
    ULTRALYTICSPLUS_AVAILABLE = True
except ImportError:
    # ultralyticsplus not available - see OPTION_B_SETUP.md for installation
    pass


class FashionDetectionService:
    """Service for detecting fashion items in images using YOLOv8."""
    
    # Fashion-specific class mappings for different models
    FASHION_CLASS_MAPPINGS = {
        # HuggingFace clothing detection model (kesimeg/yolov8n-clothing-detection)
        # Note: This model uses high-level categories: accessories, bags, clothing, shoes
        "clothing_detection": {
            # High-level categories (direct mapping)
            "accessories": (Category.ACCESSORIES, "accessories"),
            "bags": (Category.BAGS, "bags"),
            "clothing": (Category.CLOTHING, "clothing"),
            "shoes": (Category.SHOES, "shoes"),
            # Specific subcategories (if model supports them)
            "shirt": (Category.CLOTHING, "shirt"),
            "pants": (Category.CLOTHING, "pants"),
            "dress": (Category.CLOTHING, "dress"),
            "jacket": (Category.CLOTHING, "jacket"),
            "skirt": (Category.CLOTHING, "skirt"),
            "shorts": (Category.CLOTHING, "shorts"),
            "sweater": (Category.CLOTHING, "sweater"),
            "t-shirt": (Category.CLOTHING, "t-shirt"),
            "sneakers": (Category.SHOES, "sneakers"),
            "boots": (Category.SHOES, "boots"),
            "sandals": (Category.SHOES, "sandals"),
            "bag": (Category.BAGS, "bag"),
            "handbag": (Category.BAGS, "handbag"),
            "backpack": (Category.BAGS, "backpack"),
            "watch": (Category.ACCESSORIES, "watch"),
            "hat": (Category.ACCESSORIES, "hat"),
            "sunglasses": (Category.ACCESSORIES, "sunglasses"),
        },
        # COCO classes (default YOLOv8)
        "coco": {
            "person": (Category.CLOTHING, "clothing"),
            "handbag": (Category.BAGS, "handbag"),
            "backpack": (Category.BAGS, "backpack"),
            "tie": (Category.ACCESSORIES, "tie"),
            "suitcase": (Category.BAGS, "suitcase"),
        },
        # Fashionpedia mapping (if using Fashionpedia model)
        "fashionpedia": {
            "shirt": (Category.CLOTHING, "shirt"),
            "dress": (Category.CLOTHING, "dress"),
            "outerwear": (Category.CLOTHING, "outerwear"),
            "pants": (Category.CLOTHING, "pants"),
            "skirt": (Category.CLOTHING, "skirt"),
            "shorts": (Category.CLOTHING, "shorts"),
            "sweater": (Category.CLOTHING, "sweater"),
            "shoes": (Category.SHOES, "shoes"),
            "sneakers": (Category.SHOES, "sneakers"),
            "boots": (Category.SHOES, "boots"),
            "bag": (Category.BAGS, "bag"),
            "belt": (Category.ACCESSORIES, "belt"),
            "hat": (Category.ACCESSORIES, "hat"),
        }
    }
    
    def __init__(self):
        """Initialize YOLOv8 model with fashion-specific support."""
        self.device = settings.device if settings.device != "cuda" or self._check_cuda() else "cpu"
        logger.info(f"Loading YOLOv8 model on {self.device}")
        
        self.model = None
        self.model_type = "default"  # default, clothing_detection, fashionpedia, coco
        self.use_huggingface = False
        
        try:
            # Priority 1: Custom local model path
            if settings.yolo_model_path and os.path.exists(settings.yolo_model_path):
                logger.info(f"Loading custom model from {settings.yolo_model_path}")
                self.model = YOLO(settings.yolo_model_path)
                self.model_type = self._detect_model_type()
                logger.info(f"Custom model loaded: {self.model_type}")
            
            # Priority 2: HuggingFace fashion model
            # Try to load from HuggingFace using standard ultralytics
            else:
                try:
                    logger.info(f"Attempting to load HuggingFace fashion detection model: {settings.yolo_model_huggingface}")
                    logger.info("This will download the model on first use (~6MB)")
                    
                    if ULTRALYTICSPLUS_AVAILABLE:
                        # Use ultralyticsplus if available (preferred)
                        logger.info("Using ultralyticsplus for HuggingFace model")
                        self.model = YOLOPlus(settings.yolo_model_huggingface)
                    else:
                        # Try standard ultralytics with HuggingFace model
                        # First, download model from HuggingFace, then load it
                        logger.info("Using standard ultralytics for HuggingFace model")
                        try:
                            # Download model from HuggingFace first
                            from huggingface_hub import hf_hub_download, snapshot_download
                            
                            logger.info("Downloading model from HuggingFace...")
                            
                            # Try to find the model file (could be best.pt, model.pt, or yolov8n.pt)
                            model_files = ["best.pt", "model.pt", "yolov8n.pt", "weights/best.pt"]
                            model_path = None
                            
                            for filename in model_files:
                                try:
                                    model_path = hf_hub_download(
                                        repo_id=settings.yolo_model_huggingface,
                                        filename=filename,
                                        local_dir=f"./models/{settings.yolo_model_huggingface.replace('/', '_')}"
                                    )
                                    if os.path.exists(model_path):
                                        logger.info(f"Found model file: {filename}")
                                        break
                                except Exception:
                                    continue
                            
                            # If individual file download failed, try snapshot download
                            if not model_path or not os.path.exists(model_path):
                                logger.info("Trying snapshot download...")
                                local_dir = snapshot_download(
                                    repo_id=settings.yolo_model_huggingface,
                                    local_dir=f"./models/{settings.yolo_model_huggingface.replace('/', '_')}"
                                )
                                
                                # Find .pt file in downloaded directory
                                for root, dirs, files in os.walk(local_dir):
                                    for file in files:
                                        if file.endswith('.pt'):
                                            model_path = os.path.join(root, file)
                                            logger.info(f"Found model file: {model_path}")
                                            break
                                    if model_path:
                                        break
                            
                            if model_path and os.path.exists(model_path):
                                self.model = YOLO(model_path)
                                logger.info(f"Model loaded from downloaded file: {model_path}")
                            else:
                                raise Exception("Could not find model file after download")
                                
                        except ImportError:
                            logger.warning("huggingface_hub not available. Install with: uv add huggingface_hub")
                            logger.info("Falling back to default COCO model")
                            raise
                        except Exception as e2:
                            logger.warning(f"Model download/load failed: {e2}")
                            raise e2
                    
                    self.model_type = "clothing_detection"
                    self.use_huggingface = True
                    logger.info("✅ HuggingFace fashion detection model loaded successfully")
                except Exception as e:
                    logger.warning(f"Failed to load HuggingFace model: {e}")
                    logger.info("Falling back to default COCO model.")
                    logger.info("To use fashion detection:")
                    logger.info("  1. Run: ./setup_fashion_yolo.sh (downloads model)")
                    logger.info("  2. Or install: uv add huggingface_hub (for model download)")
                    logger.info("  3. Or set YOLO_MODEL_PATH to a local fashion model file")
                    # Fallback to default
                    self._load_default_model()
            
            if self.model is None:
                raise RuntimeError("Failed to load any YOLO model")
                
            logger.info(f"YOLOv8 model loaded successfully (type: {self.model_type})")
            
        except Exception as e:
            logger.error(f"Error loading YOLOv8 model: {e}")
            raise
    
    def _load_default_model(self):
        """Load default YOLOv8 COCO model."""
        logger.warning("Using default YOLOv8 COCO model. Consider using a fashion-specific model.")
        logger.info("To use fashion detection, set YOLO_MODEL_PATH or install ultralyticsplus")
        self.model = YOLO("yolov8n.pt")
        self.model_type = "coco"
    
    def _detect_model_type(self) -> str:
        """Detect model type from class names."""
        if self.model is None:
            return "default"
        
        try:
            # Get class names from model
            if hasattr(self.model, 'names'):
                class_names = self.model.names
                class_names_lower = {k: v.lower() for k, v in class_names.items()}
                
                # Check for fashion-specific classes
                fashion_classes = ["shirt", "pants", "dress", "shoes", "sneakers", "bag"]
                if any(cls in str(class_names_lower.values()).lower() for cls in fashion_classes):
                    return "clothing_detection"
                
                # Check for Fashionpedia classes
                fashionpedia_classes = ["outerwear", "belt", "skirt", "shorts"]
                if any(cls in str(class_names_lower.values()).lower() for cls in fashionpedia_classes):
                    return "fashionpedia"
            
            return "coco"
        except:
            return "default"
    
    def _check_cuda(self) -> bool:
        """Check if CUDA is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
    
    def detect_items(self, image: Image.Image, conf_threshold: float = 0.25) -> List[DetectedItem]:
        """
        Detect fashion items in an image.
        
        Args:
            image: PIL Image
            conf_threshold: Confidence threshold for detection
            
        Returns:
            List of detected fashion items
        """
        try:
            # Run detection
            results = self.model(image, conf=conf_threshold)
            
            detected_items = []
            for idx, result in enumerate(results):
                boxes = result.boxes
                if boxes is None or len(boxes) == 0:
                    continue
                
                # Get class names
                class_names = result.names if hasattr(result, 'names') else {}
                
                for box in boxes:
                    # Extract bounding box
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    # Get class and confidence
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # Map class to fashion category
                    category, subcategory = self._map_class_to_fashion(cls, class_names)
                    
                    if category:
                        # Extract colors from the bounding box region
                        colors = self._extract_colors(image, [x1, y1, x2, y2])
                        
                        # Determine style tags and patterns
                        style_tags, pattern, material = self._analyze_item(
                            image, [x1, y1, x2, y2], category, subcategory
                        )
                        
                        detected_item = DetectedItem(
                            item_id=f"item_{idx}_{len(detected_items)}",
                            category=category,
                            subcategory=subcategory,
                            colors=colors,
                            style_tags=style_tags,
                            pattern=pattern,
                            material=material,
                            confidence=conf,
                            bounding_box=[float(x1), float(y1), float(x2), float(y2)]
                        )
                        detected_items.append(detected_item)
            
            return detected_items
        except Exception as e:
            logger.error(f"Error detecting items: {e}")
            # Return empty list instead of raising to allow visual similarity search
            return []
    
    def _map_class_to_fashion(self, class_id: int, class_names: Dict) -> tuple[Optional[Category], str]:
        """Map class IDs to fashion categories based on model type."""
        # Get class name
        class_name = class_names.get(class_id, "").lower()
        
        if not class_name:
            return (None, "")
        
        # Get appropriate mapping based on model type
        mapping = self.FASHION_CLASS_MAPPINGS.get(self.model_type, {})
        
        # Try direct match
        if class_name in mapping:
            return mapping[class_name]
        
        # Try partial match (e.g., "t-shirt" matches "shirt")
        for key, value in mapping.items():
            if key in class_name or class_name in key:
                return value
        
        # Special handling for common variations
        if "shoe" in class_name or "sneaker" in class_name or "boot" in class_name:
            return (Category.SHOES, class_name)
        
        if "bag" in class_name or "handbag" in class_name or "backpack" in class_name:
            return (Category.BAGS, class_name)
        
        if "shirt" in class_name or "dress" in class_name or "pants" in class_name:
            return (Category.CLOTHING, class_name)
        
        # For COCO model, only map known fashion items
        if self.model_type == "coco":
            if "person" in class_name:
                return (Category.CLOTHING, "clothing")
            if "handbag" in class_name or "backpack" in class_name:
                return (Category.BAGS, class_name)
        
        # Default: no match
        return (None, "")
    
    def _extract_colors(self, image: Image.Image, bbox: List[float]) -> List[str]:
        """Extract dominant colors from bounding box region."""
        try:
            x1, y1, x2, y2 = map(int, bbox)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(image.width, x2), min(image.height, y2)
            
            if x2 <= x1 or y2 <= y1:
                return ["unknown"]
            
            crop = image.crop((x1, y1, x2, y2))
            crop_array = np.array(crop)
            
            # Simple color extraction using k-means
            try:
                from sklearn.cluster import KMeans
                
                # Reshape for k-means
                pixels = crop_array.reshape(-1, 3)
                
                # Sample pixels for faster computation
                if len(pixels) > 10000:
                    indices = np.random.choice(len(pixels), 10000, replace=False)
                    pixels = pixels[indices]
                
                # Get dominant colors
                kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
                kmeans.fit(pixels)
                
                # Convert RGB to color names (simplified)
                colors = []
                for center in kmeans.cluster_centers_:
                    r, g, b = center.astype(int)
                    color_name = self._rgb_to_color_name(r, g, b)
                    colors.append(color_name)
                
                return colors[:3] if colors else ["unknown"]
            except ImportError:
                # Fallback: simple color extraction
                return self._simple_color_extraction(crop_array)
        except Exception as e:
            logger.debug(f"Color extraction error: {e}")
            return ["unknown"]
    
    def _simple_color_extraction(self, image_array: np.ndarray) -> List[str]:
        """Simple color extraction without sklearn."""
        # Get average color
        avg_color = np.mean(image_array.reshape(-1, 3), axis=0)
        r, g, b = avg_color.astype(int)
        
        # Simple color name mapping
        color_name = self._rgb_to_color_name(r, g, b)
        return [color_name]
    
    def _rgb_to_color_name(self, r: int, g: int, b: int) -> str:
        """Convert RGB to color name."""
        # Simple color name mapping
        if r > 200 and g > 200 and b > 200:
            return "white"
        elif r < 50 and g < 50 and b < 50:
            return "black"
        elif r > g and r > b:
            return "red"
        elif g > r and g > b:
            return "green"
        elif b > r and b > g:
            return "blue"
        elif abs(r - g) < 30 and abs(g - b) < 30:
            return "gray"
        elif r > 150 and g > 150 and b < 100:
            return "yellow"
        else:
            return "unknown"
    
    def _analyze_item(
        self, image: Image.Image, bbox: List[float], 
        category: Category, subcategory: str
    ) -> tuple:
        """Analyze item for style, pattern, and material."""
        # Simplified analysis - would need ML models for accurate detection
        style_tags = ["casual"]  # Default
        
        # Category-based style tags
        if category == Category.SHOES:
            if "sneaker" in subcategory.lower() or "sneakers" in subcategory.lower():
                style_tags = ["casual", "athletic"]
            elif "boot" in subcategory.lower():
                style_tags = ["casual", "outdoor"]
        
        pattern = "solid"
        material = None
        
        return style_tags, pattern, material


# Global instance
_detection_service: Optional[FashionDetectionService] = None


def get_detection_service() -> FashionDetectionService:
    """Get or create detection service instance."""
    global _detection_service
    if _detection_service is None:
        _detection_service = FashionDetectionService()
    return _detection_service
