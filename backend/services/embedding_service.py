"""FashionCLIP embedding service for generating fashion item embeddings."""
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np
from typing import List, Union, Optional
from loguru import logger
from config import settings


class FashionCLIPService:
    """Service for generating FashionCLIP embeddings."""
    
    def __init__(self):
        """Initialize FashionCLIP model."""
        self.device = torch.device(settings.device if torch.cuda.is_available() else "cpu")
        logger.info(f"Loading FashionCLIP model on {self.device}")
        
        try:
            self.model = CLIPModel.from_pretrained(settings.fashionclip_model_name)
            self.processor = CLIPProcessor.from_pretrained(settings.fashionclip_model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info("FashionCLIP model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading FashionCLIP model: {e}")
            raise
    
    def encode_image(self, image: Union[Image.Image, np.ndarray]) -> np.ndarray:
        """Generate embedding for an image."""
        try:
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten()
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            raise
    
    def encode_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """Generate embedding for text description."""
        try:
            if isinstance(text, str):
                text = [text]
            
            inputs = self.processor(text=text, return_tensors="pt", padding=True, truncation=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                text_features = self.model.get_text_features(**inputs)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            if len(text) == 1:
                return text_features.cpu().numpy().flatten()
            return text_features.cpu().numpy()
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            raise


# Global instance
_embedding_service: Optional[FashionCLIPService] = None


def get_embedding_service() -> FashionCLIPService:
    """Get or create FashionCLIP service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = FashionCLIPService()
    return _embedding_service

