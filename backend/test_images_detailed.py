#!/usr/bin/env python3
"""Detailed test script for image similarity search."""
import requests
import json
from pathlib import Path
import sys

API_URL = "http://localhost:8000/api/v1/search/similar"
LIMIT = 5

# Test images
IMAGES = [
    "examples/NEED_MONEY_FOR_PORSCHE_2 (1).webp",
    "examples/IMG_6894.webp",
    "examples/02-04-2025-202143-dulopa_photo1.webp",
    "examples/896849_01.jpg.webp",
]

def test_image(image_path: str):
    """Test a single image."""
    print(f"\n{'='*60}")
    print(f"📸 Testing: {Path(image_path).name}")
    print(f"{'='*60}")
    
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (Path(image_path).name, f, 'image/webp' if image_path.endswith('.webp') else 'image/jpeg')}
            response = requests.post(
                f"{API_URL}?limit={LIMIT}",
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            data = response.json()
            
            query_info = data.get('query_info', {})
            results = data.get('results', [])
            
            print(f"✅ Success!")
            print(f"   Query type: {query_info.get('query_type', 'N/A')}")
            print(f"   Detected items: {query_info.get('detected_items', 0)}")
            print(f"   Processing time: {query_info.get('processing_time_ms', 0):.1f}ms")
            
            if results:
                result = results[0]
                query_item = result.get('query_item', {})
                similar_products = result.get('similar_products', [])
                
                print(f"\n   Query Item:")
                print(f"     Category: {query_item.get('category', 'N/A')}")
                print(f"     Subcategory: {query_item.get('subcategory', 'N/A')}")
                
                detected_features = query_item.get('detected_features', {})
                colors = detected_features.get('colors', [])
                if colors:
                    print(f"     Colors: {', '.join(colors)}")
                
                print(f"\n   Similar Products: {len(similar_products)}")
                
                for i, product in enumerate(similar_products[:3], 1):
                    product_info = product.get('product_info', {})
                    print(f"\n   {i}. {product_info.get('name', 'Unknown')}")
                    print(f"      Brand: {product_info.get('brand', 'N/A')}")
                    print(f"      Category: {product_info.get('category', 'N/A')}")
                    print(f"      Price: {product_info.get('price', 0):.2f} {product_info.get('currency', 'INR')}")
                    print(f"      Similarity: {product.get('similarity_score', 0):.2%}")
                    print(f"      Reasoning: {product.get('match_reasoning', 'N/A')}")
            else:
                print("\n   ⚠️  No similar products found")
        else:
            print(f"❌ Error {response.status_code}:")
            try:
                error_data = response.json()
                print(f"   {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   {response.text[:200]}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Is the server running?")
        print("   Start with: devenv up")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing Image Similarity Search API")
    print("="*60)
    
    for img in IMAGES:
        test_image(img)
    
    print(f"\n{'='*60}")
    print("✅ Testing complete!")
    print("="*60)

