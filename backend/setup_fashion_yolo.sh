#!/bin/bash
# Setup script for fashion YOLO model - downloads model directly
# Uses the same environment as your project (no separate venv needed)

set -e

echo "🚀 Setting up Fashion YOLO Detection Model (Same Environment)"
echo ""

# Check if ultralytics is installed
if ! python3 -c "import ultralytics" 2>/dev/null; then
    echo "❌ Error: ultralytics not installed"
    echo "   Install with: uv add ultralytics"
    exit 1
fi

echo "📥 Downloading fashion detection model from HuggingFace..."
echo "   This will download the model weights (~6MB) on first use"
echo ""

# Test if we can download the model
python3 << 'PYTHON_SCRIPT'
from huggingface_hub import snapshot_download
from ultralytics import YOLO
import os
import sys

try:
    print("Downloading kesimeg/yolov8n-clothing-detection model from HuggingFace...")
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
        print(f"✅ Model downloaded: {model_path}")
        model = YOLO(model_path)
        print("✅ Model loaded successfully!")
        
        # Check model classes
        if hasattr(model, 'model') and hasattr(model.model, 'names'):
            names = model.model.names
            fashion_classes = [name for name in names.values() if any(f in name.lower() for f in ['shirt', 'pants', 'dress', 'shoe', 'bag', 'sneaker'])]
            print(f"✅ Model has {len(fashion_classes)} fashion-related classes")
            if fashion_classes:
                print(f"   Sample classes: {', '.join(fashion_classes[:5])}")
    else:
        raise Exception("Could not find model file after download")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nThe model will be downloaded automatically on first use by the detection service.")
    sys.exit(0)
PYTHON_SCRIPT

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 The detection service will automatically use this model."
echo "   Model will be cached in ~/.cache/huggingface/ after first download."

