"""Application configuration settings."""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    
    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "fashion_products"
    qdrant_embedding_dim: int = 512
    
    # Model Configuration
    fashionclip_model_name: str = "patrickjohncyh/fashion-clip"
    yolo_model_path: Optional[str] = None  # Path to custom model, or None for auto-detect
    yolo_model_huggingface: str = "kesimeg/yolov8n-clothing-detection"  # HuggingFace model name
    device: str = "cuda"  # or cpu
    
    # Application Settings
    max_image_size_mb: int = 10
    supported_image_formats: List[str] = ["jpg", "jpeg", "png", "webp"]
    max_search_results: int = 100
    default_search_results: int = 10
    
    # Paths
    upload_dir: str = "./uploads"
    models_dir: str = "./models"
    log_dir: str = "./logs"
    
    # Apify Configuration (for scraping)
    apify_token: Optional[str] = None
    apify_instagram_actor_id: str = "apify/instagram-scraper"
    apify_pinterest_actor_id: str = "epctex/pinterest-scraper"
    min_delay_between_requests: int = 2  # seconds
    max_posts_per_request: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.models_dir, exist_ok=True)
os.makedirs(settings.log_dir, exist_ok=True)

