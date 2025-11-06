# Option B: Installing ultralyticsplus for Fashion YOLO Detection

This guide shows how to install `ultralyticsplus` in a separate environment to use the HuggingFace fashion detection model.

## Why Separate Environment?

`ultralyticsplus` requires `ultralytics<8.1.0`, but our project uses `ultralytics>=8.3.225`. To avoid conflicts, we use a separate Python environment.

## Quick Setup (Automated)

Run the setup script:

```bash
chmod +x setup_fashion_yolo.sh
./setup_fashion_yolo.sh
```

This will:
1. Create a separate virtual environment (`venv_fashion_yolo`)
2. Install compatible versions of `ultralyticsplus` and `ultralytics`
3. Provide instructions for activation

## Manual Setup

### Step 1: Create Separate Environment

```bash
# Create virtual environment
python3 -m venv venv_fashion_yolo

# Activate it
source venv_fashion_yolo/bin/activate  # Linux/Mac
# OR
venv_fashion_yolo\Scripts\activate  # Windows
```

### Step 2: Install Compatible Versions

```bash
pip install --upgrade pip
pip install ultralyticsplus==0.0.23 ultralytics==8.0.21
```

### Step 3: Verify Installation

```bash
python -c "from ultralyticsplus import YOLO; print('✓ ultralyticsplus installed successfully')"
```

## Integration with Detection Service

The detection service will automatically detect and use `ultralyticsplus` if it's available in the Python path.

### Option 1: Use the Environment for Detection Only

Keep your main project with `ultralytics>=8.3.225`, but use the separate environment when you need fashion detection:

```bash
# In your main project
source venv_fashion_yolo/bin/activate
python -c "from services import get_detection_service; service = get_detection_service()"
```

### Option 2: Modify PYTHONPATH (Advanced)

Add the ultralyticsplus environment to your Python path:

```bash
export PYTHONPATH="${PYTHONPATH}:./venv_fashion_yolo/lib/python3.*/site-packages"
```

### Option 3: Use in Separate Process

Create a wrapper script that uses the fashion YOLO environment:

```python
#!/usr/bin/env python3
# fashion_detection_wrapper.py
import sys
import os

# Add ultralyticsplus environment to path
fashion_env = "./venv_fashion_yolo/lib/python3.*/site-packages"
if os.path.exists(fashion_env.replace('*', '')):
    sys.path.insert(0, fashion_env)

from services import get_detection_service

# Now use the service
service = get_detection_service()
```

## Using with Devenv

Update your `devenv.nix` to include the fashion YOLO environment:

```nix
# In devenv.nix
env = {
  # ... other env vars ...
  ULTRALYTICSPLUS_ENV = "./venv_fashion_yolo";
};

# Add script to activate both environments
shellHooks = ''
  if [ -d "./venv_fashion_yolo" ]; then
    export PYTHONPATH="${PYTHONPATH}:$(find ./venv_fashion_yolo/lib -name site-packages -type d | head -1)"
  fi
'';
```

## Testing the Fashion Model

Once installed, test the model:

```python
from ultralyticsplus import YOLO

# Load the fashion detection model
model = YOLO('kesimeg/yolov8n-clothing-detection')

# Test on an image
results = model.predict('path/to/image.jpg', conf=0.25)

# Check detected classes
for result in results:
    print(result.names)  # Should show fashion classes like 'shirt', 'pants', 'shoes', etc.
```

## Expected Fashion Classes

The `kesimeg/yolov8n-clothing-detection` model detects:

- **Clothing**: shirt, pants, dress, jacket, skirt, shorts, sweater, t-shirt
- **Shoes**: shoes, sneakers, boots, sandals
- **Bags**: bag, handbag, backpack
- **Accessories**: watch, hat, sunglasses

## Troubleshooting

### Import Error: No module named 'ultralyticsplus'

**Solution**: Make sure the environment is activated and ultralyticsplus is installed:
```bash
source venv_fashion_yolo/bin/activate
pip list | grep ultralyticsplus
```

### Version Conflict Still Occurs

**Solution**: Ensure you're using the separate environment:
```bash
which python  # Should point to venv_fashion_yolo/bin/python
```

### Model Download Fails

**Solution**: Check internet connection and HuggingFace access:
```bash
# Test HuggingFace connection
python -c "from huggingface_hub import hf_hub_download; print('✓ HuggingFace accessible')"
```

### Detection Service Still Uses COCO Model

**Solution**: Check logs to see why fashion model isn't loading:
```python
from services import get_detection_service
service = get_detection_service()
print(f"Model type: {service.model_type}")  # Should be 'clothing_detection'
```

## Alternative: Use Model Directly

If ultralyticsplus setup is problematic, you can download the model weights manually:

1. Download from HuggingFace: `kesimeg/yolov8n-clothing-detection`
2. Extract the `.pt` file
3. Set `YOLO_MODEL_PATH` to the downloaded file

## Performance Notes

- **First load**: Model downloads from HuggingFace (~6MB) - takes ~30 seconds
- **Subsequent loads**: Model loads from cache - takes ~2-5 seconds
- **Inference**: Fast on GPU, moderate on CPU (~100-500ms per image)

## Next Steps

1. ✅ Run setup script or manual installation
2. ✅ Test model loading
3. ✅ Verify detection service uses fashion model
4. ✅ Test on sample images
5. ✅ Monitor detection accuracy

## Summary

Option B provides the best fashion detection accuracy by using a specialized model trained on fashion datasets. The separate environment approach avoids version conflicts while maintaining compatibility with your main project dependencies.

