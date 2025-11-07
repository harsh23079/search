"""Simple file-based storage for scraped posts."""
import json
import os
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from loguru import logger
from config import settings


class PostStorage:
    """Simple file-based storage for scraped posts."""
    
    def __init__(self, storage_file: str = "./data/scraped_posts.json"):
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_storage_file()
    
    def _ensure_storage_file(self):
        """Ensure storage file exists."""
        if not self.storage_file.exists():
            with open(self.storage_file, 'w') as f:
                json.dump({"posts": []}, f)
    
    def _serialize_datetime(self, obj: Any) -> Any:
        """Recursively convert datetime objects to ISO format strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._serialize_datetime(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime(item) for item in obj]
        else:
            return obj
    
    def save_posts(self, posts: List[Dict], source_url: str, platform: str) -> int:
        """Save scraped posts to storage."""
        try:
            logger.info(f"Attempting to save {len(posts)} posts to {self.storage_file}")
            
            # Load existing posts
            if not self.storage_file.exists():
                logger.warning(f"Storage file does not exist, creating: {self.storage_file}")
                self._ensure_storage_file()
            
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
            
            existing_posts = data.get("posts", [])
            logger.info(f"Found {len(existing_posts)} existing posts in storage")
            
            # Add new posts with metadata
            saved_count = 0
            for post in posts:
                # Serialize datetime objects in the post data
                serialized_post = self._serialize_datetime(post)
                
                # Generate unique ID using post ID if available, otherwise use UUID
                post_id = serialized_post.get('structured_data', {}).get('id') or serialized_post.get('raw_data', {}).get('id')
                if post_id:
                    unique_id = f"{platform}_{post_id}_{uuid.uuid4().hex[:8]}"
                else:
                    unique_id = f"{platform}_{uuid.uuid4().hex}"
                
                post_entry = {
                    "id": unique_id,
                    "platform": platform,
                    "source_url": source_url,
                    "scraped_at": datetime.now().isoformat(),
                    "post_data": serialized_post,
                }
                existing_posts.append(post_entry)
                saved_count += 1
            
            # Save back to file
            data["posts"] = existing_posts
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Successfully saved {saved_count} posts to storage at {self.storage_file}. Total posts now: {len(existing_posts)}")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error saving posts to {self.storage_file}: {e}", exc_info=True)
            return 0
    
    def get_posts(self, limit: int = 50, offset: int = 0, platform: Optional[str] = None) -> tuple[List[Dict], int]:
        """Get saved posts with pagination."""
        try:
            logger.info(f"Reading posts from {self.storage_file}")
            if not self.storage_file.exists():
                logger.warning(f"Storage file does not exist: {self.storage_file}")
                return [], 0
            
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
            
            posts = data.get("posts", [])
            logger.info(f"Found {len(posts)} total posts in storage file")
            
            # Filter by platform if specified
            if platform:
                posts = [p for p in posts if p.get("platform") == platform]
                logger.info(f"Filtered to {len(posts)} posts for platform: {platform}")
            
            # Sort by scraped_at (newest first)
            posts.sort(key=lambda x: x.get("scraped_at", ""), reverse=True)
            
            total = len(posts)
            paginated_posts = posts[offset:offset + limit]
            logger.info(f"Returning {len(paginated_posts)} posts (offset={offset}, limit={limit}, total={total})")
            
            return paginated_posts, total
            
        except Exception as e:
            logger.error(f"Error getting posts from {self.storage_file}: {e}", exc_info=True)
            return [], 0
    
    def get_post_by_id(self, post_id: str) -> Optional[Dict]:
        """Get a single post by ID."""
        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
            
            posts = data.get("posts", [])
            for post in posts:
                if post.get("id") == post_id:
                    return post
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting post by ID: {e}")
            return None
    
    def clear_all(self) -> int:
        """Clear all saved posts."""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump({"posts": []}, f)
            
            # Count how many were deleted
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
            count = len(data.get("posts", []))
            
            logger.info(f"Cleared all posts from storage")
            return count
            
        except Exception as e:
            logger.error(f"Error clearing posts: {e}")
            return 0


# Global instance
_post_storage: Optional[PostStorage] = None


def get_post_storage() -> PostStorage:
    """Get or create post storage instance."""
    global _post_storage
    if _post_storage is None:
        storage_file = getattr(settings, 'scraped_posts_storage_file', './data/scraped_posts.json')
        # Convert to absolute path to ensure consistency
        if not os.path.isabs(storage_file):
            # Make path relative to backend directory
            backend_dir = Path(__file__).parent.parent
            # Strip leading ./ if present
            storage_file_clean = storage_file.lstrip('./')
            storage_file = str(backend_dir / storage_file_clean)
        logger.info(f"PostStorage initialized with file: {storage_file}")
        _post_storage = PostStorage(storage_file=storage_file)
    return _post_storage

