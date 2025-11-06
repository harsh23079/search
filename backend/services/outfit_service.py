"""Outfit recommendation service with compatibility scoring."""
from typing import List, Dict, Any, Optional
from loguru import logger
from models.schemas import (
    Category, OutfitRecommendation, OutfitItem, 
    CompatibilityResponse, CompatibilityBreakdown
)


class OutfitService:
    """Service for generating outfit recommendations."""
    
    def __init__(self):
        """Initialize outfit service."""
        logger.info("Outfit service initialized")
    
    def generate_outfit(
        self,
        anchor_product: Dict[str, Any],
        occasion: str = "casual",
        season: str = "all-season",
        gender: str = "unisex",
        budget_range: str = "mid-range"
    ) -> OutfitRecommendation:
        """
        Generate complete outfit recommendation.
        
        Args:
            anchor_product: Anchor product details
            occasion: Target occasion
            season: Season
            gender: Gender preference
            budget_range: Budget range
            
        Returns:
            Complete outfit recommendation
        """
        try:
            category = anchor_product.get("category")
            subcategory = anchor_product.get("subcategory")
            colors = anchor_product.get("colors", [])
            style_tags = anchor_product.get("style_tags", [])
            
            # Generate outfit items based on anchor
            outfit_items = self._generate_outfit_items(
                category, subcategory, colors, style_tags, occasion
            )
            
            # Calculate compatibility score
            compatibility_score = self._calculate_outfit_compatibility(
                anchor_product, outfit_items
            )
            
            # Generate styling tips
            styling_tips = self._generate_styling_tips(occasion, season)
            
            # Determine occasion suitability
            occasion_suitability = self._calculate_occasion_suitability(
                outfit_items, occasion
            )
            
            outfit = OutfitRecommendation(
                outfit_id=f"OUTFIT-{hash(str(anchor_product)) % 100000}",
                theme=self._generate_theme(occasion, style_tags),
                style_description=self._generate_style_description(
                    style_tags, occasion
                ),
                overall_compatibility_score=compatibility_score,
                items=outfit_items,
                total_outfit_price=self._calculate_total_price(outfit_items),
                styling_tips=styling_tips,
                occasion_suitability=occasion_suitability
            )
            
            return outfit
        except Exception as e:
            logger.error(f"Error generating outfit: {e}")
            raise
    
    def _generate_outfit_items(
        self,
        anchor_category: Category,
        anchor_subcategory: str,
        anchor_colors: List[str],
        style_tags: List[str],
        occasion: str
    ) -> Dict[str, Any]:
        """Generate outfit items based on anchor product."""
        items = {}
        
        # Generate recommendations for each slot
        if anchor_category != Category.CLOTHING or "top" not in anchor_subcategory:
            items["top"] = self._recommend_top(anchor_colors, style_tags, occasion)
        
        if anchor_category != Category.CLOTHING or "bottom" not in anchor_subcategory:
            items["bottom"] = self._recommend_bottom(anchor_colors, style_tags, occasion)
        
        if anchor_category != Category.SHOES:
            items["shoes"] = self._recommend_shoes(anchor_colors, style_tags, occasion)
        
        items["accessories"] = self._recommend_accessories(
            anchor_colors, style_tags, occasion
        )
        
        return items
    
    def _recommend_top(
        self, colors: List[str], style_tags: List[str], occasion: str
    ) -> Dict[str, Any]:
        """Recommend top item."""
        if "formal" in style_tags or occasion in ["business", "formal"]:
            top_type = "button-down shirt"
            top_color = "light blue" if "blue" in colors else "white"
        else:
            top_type = "t-shirt"
            top_color = "white"
        
        return {
            "type": top_type,
            "color": top_color,
            "style": "slim fit",
            "reasoning": f"{top_color} {top_type} complements the color palette",
            "search_keywords": [top_type, top_color, "slim fit"]
        }
    
    def _recommend_bottom(
        self, colors: List[str], style_tags: List[str], occasion: str
    ) -> Dict[str, Any]:
        """Recommend bottom item."""
        if "formal" in style_tags or occasion in ["business", "formal"]:
            bottom_type = "chino pants"
            bottom_color = "navy"
        else:
            bottom_type = "jeans"
            bottom_color = "dark blue"
        
        return {
            "type": bottom_type,
            "color": bottom_color,
            "style": "straight fit",
            "reasoning": f"{bottom_color} {bottom_type} provides classic pairing",
            "search_keywords": [bottom_type, bottom_color]
        }
    
    def _recommend_shoes(
        self, colors: List[str], style_tags: List[str], occasion: str
    ) -> Dict[str, Any]:
        """Recommend shoes."""
        if "formal" in style_tags or occasion in ["business", "formal"]:
            shoe_type = "oxford shoes"
            shoe_color = "brown"
        else:
            shoe_type = "sneakers"
            shoe_color = "white"
        
        return {
            "type": shoe_type,
            "color": shoe_color,
            "style": "classic",
            "reasoning": f"{shoe_color} {shoe_type} match the occasion",
            "search_keywords": [shoe_type, shoe_color]
        }
    
    def _recommend_accessories(
        self, colors: List[str], style_tags: List[str], occasion: str
    ) -> List[Dict[str, Any]]:
        """Recommend accessories."""
        accessories = []
        
        if occasion in ["business", "formal"]:
            accessories.append({
                "type": "leather watch",
                "color": "brown",
                "reasoning": "Adds sophistication"
            })
        
        accessories.append({
            "type": "belt",
            "color": "brown",
            "reasoning": "Completes the outfit"
        })
        
        return accessories
    
    def _calculate_outfit_compatibility(
        self, anchor: Dict[str, Any], items: Dict[str, Any]
    ) -> float:
        """Calculate overall outfit compatibility score."""
        # Simplified scoring (0-10 scale)
        base_score = 7.0
        
        # Check color harmony
        colors = [anchor.get("colors", [])] + [
            item.get("color") for item in items.values() 
            if isinstance(item, dict) and "color" in item
        ]
        if self._check_color_harmony(colors):
            base_score += 1.0
        
        # Check style consistency
        if self._check_style_consistency(items):
            base_score += 1.0
        
        return min(10.0, base_score)
    
    def _check_color_harmony(self, colors: List[Any]) -> bool:
        """Check if colors are harmonious."""
        # Simplified check
        return True
    
    def _check_style_consistency(self, items: Dict[str, Any]) -> bool:
        """Check if styles are consistent."""
        # Simplified check
        return True
    
    def _generate_styling_tips(self, occasion: str, season: str) -> List[str]:
        """Generate styling tips."""
        tips = []
        
        if occasion == "business":
            tips.append("Roll sleeves to elbow for smart-casual vibe")
            tips.append("Add a leather belt to match shoes")
        
        if season in ["spring", "fall"]:
            tips.append("Consider adding a light jacket or cardigan")
        
        return tips
    
    def _calculate_occasion_suitability(
        self, items: Dict[str, Any], occasion: str
    ) -> Dict[str, float]:
        """Calculate suitability for different occasions."""
        base_score = 8.0 if occasion == "casual" else 7.0
        
        return {
            "casual": 9.0,
            "business_casual": 8.0,
            "formal": 5.0,
            "party": 6.0
        }
    
    def _generate_theme(self, occasion: str, style_tags: List[str]) -> str:
        """Generate outfit theme."""
        if "formal" in style_tags:
            return "Professional and polished"
        elif "casual" in style_tags:
            return "Relaxed and comfortable"
        else:
            return "Versatile and stylish"
    
    def _generate_style_description(
        self, style_tags: List[str], occasion: str
    ) -> str:
        """Generate style description."""
        return f"Clean, {occasion} aesthetic with {', '.join(style_tags[:2])} elements"
    
    def _calculate_total_price(self, items: Dict[str, Any]) -> Optional[float]:
        """Calculate total outfit price."""
        # Would need actual product prices
        return None
    
    def analyze_compatibility(
        self, items: List[Dict[str, Any]]
    ) -> CompatibilityResponse:
        """Analyze compatibility between multiple items."""
        # Calculate compatibility scores
        color_score = self._score_color_compatibility(items)
        style_score = self._score_style_coherence(items)
        proportion_score = 8.0  # Simplified
        pattern_score = 8.0  # Simplified
        occasion_score = 8.0  # Simplified
        
        overall = (color_score + style_score + proportion_score + 
                  pattern_score + occasion_score) / 5
        
        breakdown = {
            "color_compatibility": CompatibilityBreakdown(
                score=color_score,
                analysis="Colors work well together"
            ),
            "style_coherence": CompatibilityBreakdown(
                score=style_score,
                analysis="Styles are consistent"
            ),
            "proportions": CompatibilityBreakdown(
                score=proportion_score,
                analysis="Proportions are balanced"
            ),
            "pattern_texture": CompatibilityBreakdown(
                score=pattern_score,
                analysis="Patterns complement each other"
            ),
            "occasion": CompatibilityBreakdown(
                score=occasion_score,
                analysis="Appropriate for the occasion"
            )
        }
        
        verdict = "HIGHLY COMPATIBLE" if overall >= 8 else "COMPATIBLE"
        
        return CompatibilityResponse(
            overall_compatibility_score=overall,
            breakdown=breakdown,
            strengths=["Classic color combination", "Consistent style"],
            potential_improvements=["Add a statement accessory"],
            verdict=verdict,
            confidence=0.85
        )
    
    def _score_color_compatibility(self, items: List[Dict[str, Any]]) -> float:
        """Score color compatibility."""
        return 8.5
    
    def _score_style_coherence(self, items: List[Dict[str, Any]]) -> float:
        """Score style coherence."""
        return 8.0

