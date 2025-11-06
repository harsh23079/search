# Quick Start: Option B - Fashion YOLO Detection (Same Environment)

## Step 1: Install Optional Dependencies

```bash
# Install huggingface_hub for model download (optional but recommended)
uv add huggingface_hub
```

## Step 2: Run Setup Script

```bash
./setup_fashion_yolo.sh
```

This downloads the fashion detection model from HuggingFace (uses your current environment).

## Step 3: Test Installation

```bash
# Run test script (no separate environment needed)
python test_fashion_yolo.py
```

Expected output:
```
✓ ultralytics version: 8.3.225
⚠ ultralyticsplus not available (using standard ultralytics instead)
✓ huggingface_hub available
✓ Fashion detection model loaded successfully
✅ Setup complete! Fashion detection model is ready.
```

## Step 3: Use in Your Project

The detection service will automatically use the fashion model - no separate environment needed!

Just run your app normally:

```bash
devenv up  # or uv run uvicorn main:app
```

The model will be automatically loaded from HuggingFace on first use.

## Step 4: Verify Detection

Test the detection service:

```python
from services import get_detection_service
from PIL import Image

service = get_detection_service()
print(f"Model type: {service.model_type}")  # Should be 'clothing_detection'

# Test on an image
image = Image.open("path/to/shoe_image.jpg")
items = service.detect_items(image)
print(f"Detected {len(items)} fashion items")
```

## What You Get

✅ Fashion-specific detection (shoes, clothing, bags, accessories)
✅ Better accuracy than default COCO model
✅ 18+ fashion categories detected
✅ Automatic integration with detection service

## Troubleshooting

**If setup fails:**
- Ensure `python3-venv` is installed: `sudo apt-get install python3-venv`
- Check Python version: `python3 --version` (needs 3.8+)

**If model doesn't load:**
- Check internet connection (model downloads from HuggingFace)
- Verify environment is activated: `which python`
- Check logs for errors

**For more details:** See `OPTION_B_SETUP.md`

