"""Color harmony analysis service."""
from typing import List, Dict, Any
from loguru import logger
from models.schemas import ColorHarmonyResponse


class ColorService:
    """Service for color harmony analysis."""
    
    def __init__(self):
        """Initialize color service."""
        logger.info("Color service initialized")
    
    def analyze_harmony(
        self,
        base_colors: List[str],
        occasion: str = "casual",
        season: str = "all-season"
    ) -> ColorHarmonyResponse:
        """
        Analyze color combinations and provide harmony recommendations.
        
        Args:
            base_colors: List of base colors
            occasion: Target occasion
            season: Season
            
        Returns:
            Color harmony analysis
        """
        try:
            color_analysis = {}
            for color in base_colors:
                color_analysis[color] = self._analyze_color(color)
            
            harmony_recommendations = self._generate_harmony_recommendations(
                base_colors, occasion
            )
            
            avoid_colors = self._identify_avoid_colors(base_colors)
            
            styling_tips = self._generate_color_tips(base_colors, occasion)
            
            return ColorHarmonyResponse(
                base_colors=base_colors,
                color_analysis=color_analysis,
                harmony_recommendations=harmony_recommendations,
                avoid_colors=avoid_colors,
                styling_tips=styling_tips
            )
        except Exception as e:
            logger.error(f"Error analyzing color harmony: {e}")
            raise
    
    def _analyze_color(self, color: str) -> Dict[str, Any]:
        """Analyze individual color properties."""
        color_lower = color.lower()
        
        # Determine color family
        if color_lower in ["black", "white", "gray", "beige", "navy"]:
            family = "neutral"
            palette_type = "neutral"
            versatility = "high"
        elif color_lower in ["blue", "green", "purple"]:
            family = "cool"
            palette_type = "cool"
            versatility = "medium"
        else:
            family = "warm"
            palette_type = "warm"
            versatility = "medium"
        
        return {
            "classification": f"{family}, {palette_type}",
            "color_family": family,
            "palette_type": palette_type,
            "versatility": versatility
        }
    
    def _generate_harmony_recommendations(
        self, base_colors: List[str], occasion: str
    ) -> Dict[str, Dict[str, Any]]:
        """Generate harmony recommendations."""
        recommendations = {
            "complementary_palette": {
                "colors": ["rust orange", "burnt sienna"],
                "reasoning": "Warm oranges provide high contrast",
                "best_for": ["casual", "autumn styling"]
            },
            "analogous_palette": {
                "colors": ["light blue", "gray-blue", "teal"],
                "reasoning": "Creates cohesive, sophisticated look",
                "best_for": ["formal", "professional"]
            },
            "accent_palette": {
                "colors": ["burgundy", "forest green"],
                "reasoning": "Deep jewel tones add richness",
                "best_for": ["accessories", "small pops of color"]
            },
            "safe_additions": {
                "colors": ["gray", "beige", "black", "cream"],
                "reasoning": "Neutrals that work universally"
            }
        }
        
        return recommendations
    
    def _identify_avoid_colors(self, base_colors: List[str]) -> List[Dict[str, str]]:
        """Identify colors to avoid."""
        avoid = []
        
        if "navy" in [c.lower() for c in base_colors]:
            avoid.append({
                "color": "bright yellow",
                "reason": "Too high contrast without harmony"
            })
        
        return avoid
    
    def _generate_color_tips(
        self, base_colors: List[str], occasion: str
    ) -> List[str]:
        """Generate color styling tips."""
        tips = [
            "Use 60-30-10 rule: 60% base, 30% secondary, 10% accent",
            "Maintain color consistency across outfit"
        ]
        
        if occasion == "formal":
            tips.append("Keep third color in same cool/warm family")
        
        return tips

