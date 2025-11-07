"""Image caching service for temporary storage of scraped images."""
import hashlib
import os
import time
from pathlib import Path
from typing import Optional
from loguru import logger
from config import settings


class ImageCache:
    """Service for caching images temporarily (4-5 minutes)."""
    
    def __init__(self, cache_dir: str = "./cache/images", ttl_seconds: int = 300):
        """
        Initialize image cache.
        
        Args:
            cache_dir: Directory to store cached images
            ttl_seconds: Time to live in seconds (default 5 minutes = 300 seconds)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Image cache initialized at {self.cache_dir} with TTL {ttl_seconds}s")
        
        # Clean up expired images on startup
        self.cleanup_expired()
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL using hash."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_cache_path(self, url: str) -> Path:
        """Get file path for cached image."""
        cache_key = self._get_cache_key(url)
        return self.cache_dir / f"{cache_key}.jpg"
    
    def _get_metadata_path(self, url: str) -> Path:
        """Get path for metadata file (stores content type and timestamp)."""
        cache_key = self._get_cache_key(url)
        return self.cache_dir / f"{cache_key}.meta"
    
    def get(self, url: str) -> Optional[tuple[bytes, str]]:
        """
        Get cached image if available and not expired.
        
        Returns:
            Tuple of (image_bytes, content_type) or None if not cached/expired
        """
        cache_path = self._get_cache_path(url)
        metadata_path = self._get_metadata_path(url)
        
        if not cache_path.exists() or not metadata_path.exists():
            return None
        
        try:
            # Check if expired
            with open(metadata_path, 'r') as f:
                timestamp = float(f.read().strip())
            
            age = time.time() - timestamp
            if age > self.ttl_seconds:
                logger.debug(f"Cache expired for {url[:50]}... (age: {age:.1f}s)")
                # Delete expired files
                cache_path.unlink(missing_ok=True)
                metadata_path.unlink(missing_ok=True)
                return None
            
            # Read cached image
            with open(cache_path, 'rb') as f:
                image_bytes = f.read()
            
            # Read content type from metadata (first line is timestamp, second is content_type)
            with open(metadata_path, 'r') as f:
                lines = f.readlines()
                content_type = lines[1].strip() if len(lines) > 1 else "image/jpeg"
            
            logger.debug(f"Cache hit for {url[:50]}... (age: {age:.1f}s)")
            return image_bytes, content_type
            
        except Exception as e:
            logger.error(f"Error reading cache for {url[:50]}...: {e}")
            # Clean up corrupted cache files
            cache_path.unlink(missing_ok=True)
            metadata_path.unlink(missing_ok=True)
            return None
    
    def set(self, url: str, image_bytes: bytes, content_type: str = "image/jpeg") -> bool:
        """
        Cache image with current timestamp.
        
        Returns:
            True if successful
        """
        try:
            cache_path = self._get_cache_path(url)
            metadata_path = self._get_metadata_path(url)
            
            # Write image
            with open(cache_path, 'wb') as f:
                f.write(image_bytes)
            
            # Write metadata (timestamp and content_type)
            with open(metadata_path, 'w') as f:
                f.write(f"{time.time()}\n{content_type}\n")
            
            logger.debug(f"Cached image for {url[:50]}... ({len(image_bytes)} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Error caching image for {url[:50]}...: {e}")
            return False
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired cache files.
        
        Returns:
            Number of files deleted
        """
        deleted = 0
        current_time = time.time()
        
        try:
            for file_path in self.cache_dir.glob("*.meta"):
                try:
                    with open(file_path, 'r') as f:
                        timestamp = float(f.read().strip().split('\n')[0])
                    
                    age = current_time - timestamp
                    if age > self.ttl_seconds:
                        # Delete both metadata and image files
                        file_path.unlink()
                        image_path = file_path.with_suffix('.jpg')
                        if image_path.exists():
                            image_path.unlink()
                        deleted += 1
                except Exception as e:
                    logger.warning(f"Error checking cache file {file_path}: {e}")
                    # Delete corrupted metadata file
                    file_path.unlink(missing_ok=True)
            
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} expired cache files")
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
        
        return deleted
    
    def clear_all(self) -> int:
        """Clear all cached images. Returns number of files deleted."""
        deleted = 0
        try:
            for file_path in self.cache_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
                    deleted += 1
            logger.info(f"Cleared all cache files ({deleted} files)")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
        return deleted


# Global instance
_image_cache: Optional[ImageCache] = None


def get_image_cache() -> ImageCache:
    """Get or create image cache instance."""
    global _image_cache
    if _image_cache is None:
        cache_dir = getattr(settings, 'image_cache_dir', './cache/images')
        ttl = getattr(settings, 'image_cache_ttl_seconds', 300)  # 5 minutes default
        _image_cache = ImageCache(cache_dir=cache_dir, ttl_seconds=ttl)
    return _image_cache

