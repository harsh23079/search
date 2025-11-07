"""Simple file-based storage for scraped posts."""
import json
import os
import uuid
from pathlib import Path
from typing import List, Dict, Optional
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
    
    def save_posts(self, posts: List[Dict], source_url: str, platform: str) -> int:
        """Save scraped posts to storage."""
        try:
            # Load existing posts
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
            
            existing_posts = data.get("posts", [])
            
            # Add new posts with metadata
            saved_count = 0
            for post in posts:
                # Generate unique ID using post ID if available, otherwise use UUID
                post_id = post.get('structured_data', {}).get('id') or post.get('raw_data', {}).get('id')
                if post_id:
                    unique_id = f"{platform}_{post_id}_{uuid.uuid4().hex[:8]}"
                else:
                    unique_id = f"{platform}_{uuid.uuid4().hex}"
                
                post_entry = {
                    "id": unique_id,
                    "platform": platform,
                    "source_url": source_url,
                    "scraped_at": datetime.now().isoformat(),
                    "post_data": post,
                }
                existing_posts.append(post_entry)
                saved_count += 1
            
            # Save back to file
            data["posts"] = existing_posts
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {saved_count} posts to storage")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error saving posts: {e}")
            return 0
    
    def get_posts(self, limit: int = 50, offset: int = 0, platform: Optional[str] = None) -> tuple[List[Dict], int]:
        """Get saved posts with pagination."""
        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
            
            posts = data.get("posts", [])
            
            # Filter by platform if specified
            if platform:
                posts = [p for p in posts if p.get("platform") == platform]
            
            # Sort by scraped_at (newest first)
            posts.sort(key=lambda x: x.get("scraped_at", ""), reverse=True)
            
            total = len(posts)
            paginated_posts = posts[offset:offset + limit]
            
            return paginated_posts, total
            
        except Exception as e:
            logger.error(f"Error getting posts: {e}")
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
        _post_storage = PostStorage(storage_file=storage_file)
    return _post_storage

