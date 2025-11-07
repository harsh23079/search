"""Application configuration settings."""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path
from loguru import logger


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
    image_cache_dir: str = "./cache/images"
    
    # Image Cache Settings
    image_cache_ttl_seconds: int = 300  # 5 minutes default
    
    # Apify Configuration (for scraping)
    apify_token: Optional[str] = None
    apify_instagram_actor_id: str = "apify/instagram-scraper"
    apify_pinterest_actor_id: str = "epctex/pinterest-scraper"
    min_delay_between_requests: int = 2  # seconds
    max_posts_per_request: int = 1000
    
    # Post Storage
    scraped_posts_storage_file: str = "./data/scraped_posts.json"
    
    # Database Configuration
    database_url: Optional[str] = None  # e.g., postgresql+asyncpg://user:pass@localhost/dbname
    # If not set, will use SQLite as fallback
    
    class Config:
        # Use absolute path to .env file in backend directory
        env_file = str(Path(__file__).parent.parent / ".env")
        case_sensitive = False


# Create settings instance
settings = Settings()

# Debug: Log if Apify token is loaded (without exposing the full token)
if settings.apify_token:
    logger.info(f"Apify token loaded: {settings.apify_token[:10]}...{settings.apify_token[-4:] if len(settings.apify_token) > 14 else '***'}")
else:
    logger.warning("Apify token not found in environment. Instagram scraping will not work.")

# Ensure directories exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.models_dir, exist_ok=True)
os.makedirs(settings.log_dir, exist_ok=True)
os.makedirs(settings.image_cache_dir, exist_ok=True)
# Ensure data directory exists for scraped posts storage
data_dir = os.path.dirname(settings.scraped_posts_storage_file)
if data_dir:  # Only create if there's a directory path
    os.makedirs(data_dir, exist_ok=True)

