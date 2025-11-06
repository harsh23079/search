#!/usr/bin/env python3
"""Test script to verify fashion YOLO model setup (same environment)."""
import sys
import os

print("Testing Fashion YOLO Model Setup (Same Environment)")
print("=" * 60)

# Check ultralytics
try:
    import ultralytics
    print(f"✓ ultralytics version: {ultralytics.__version__}")
except ImportError:
    print("✗ ultralytics not available")
    print("  Install with: uv add ultralytics")
    sys.exit(1)

# Check ultralyticsplus (optional)
ULTRALYTICSPLUS_AVAILABLE = False
try:
    from ultralyticsplus import YOLO as YOLOPlus
    print("✓ ultralyticsplus available (optional)")
    ULTRALYTICSPLUS_AVAILABLE = True
except ImportError:
    print("⚠ ultralyticsplus not available (using standard ultralytics instead)")

# Check huggingface_hub (for model download)
HUGGINGFACE_HUB_AVAILABLE = False
try:
    import huggingface_hub
    print("✓ huggingface_hub available")
    HUGGINGFACE_HUB_AVAILABLE = True
except ImportError:
    print("⚠ huggingface_hub not available (model will download via ultralytics)")

# Test model loading
from ultralytics import YOLO

try:
    print("\nLoading fashion detection model from HuggingFace...")
    print("   This will download the model on first use (~6MB)")
    
    if ULTRALYTICSPLUS_AVAILABLE:
        model = YOLOPlus('kesimeg/yolov8n-clothing-detection')
    else:
        # Download model from HuggingFace first, then load
        from huggingface_hub import snapshot_download
        import os
        
        print("   Downloading model from HuggingFace...")
        local_dir = snapshot_download(
            repo_id='kesimeg/yolov8n-clothing-detection',
            local_dir='./models/kesimeg_yolov8n-clothing-detection'
        )
        
        # Find .pt file
        model_path = None
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                if file.endswith('.pt'):
                    model_path = os.path.join(root, file)
                    break
            if model_path:
                break
        
        if model_path:
            print(f"   Found model: {model_path}")
            model = YOLO(model_path)
        else:
            raise Exception("Could not find model file after download")
    
    print("✓ Fashion detection model loaded successfully")
    
    # Check model classes
    if hasattr(model, 'model') and hasattr(model.model, 'names'):
        names = model.model.names
        fashion_classes = [name for name in names.values() if any(f in name.lower() for f in ['shirt', 'pants', 'dress', 'shoe', 'bag', 'sneaker'])]
        print(f"✓ Model has {len(fashion_classes)} fashion-related classes")
        if fashion_classes:
            print(f"  Sample classes: {', '.join(fashion_classes[:5])}")
    else:
        # Try alternative method
        if hasattr(model, 'names'):
            names = model.names
            fashion_classes = [name for name in names.values() if any(f in name.lower() for f in ['shirt', 'pants', 'dress', 'shoe', 'bag'])]
            if fashion_classes:
                print(f"✓ Model has {len(fashion_classes)} fashion-related classes")
                print(f"  Sample classes: {', '.join(fashion_classes[:5])}")
    
    print("\n✅ Setup complete! Fashion detection model is ready.")
    print("   The detection service will automatically use this model.")
    
except Exception as e:
    print(f"\n✗ Failed to load model: {e}")
    print("\nTroubleshooting:")
    print("  1. Check internet connection (model downloads from HuggingFace)")
    print("  2. Try: uv add huggingface_hub")
    print("  3. Or download model manually and set YOLO_MODEL_PATH")
    sys.exit(1)
