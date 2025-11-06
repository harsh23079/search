# Fashion-Specific YOLO Models Setup

## Overview

The detection service now supports fashion-specific YOLO models for better detection of clothing, shoes, bags, and accessories. The system automatically tries to load the best available model in this order:

1. **Custom local model** (if `YOLO_MODEL_PATH` is set)
2. **HuggingFace fashion model** (if `ultralyticsplus` is installed)
3. **Default COCO model** (fallback)

## Option 1: HuggingFace Fashion Detection Model (Recommended)

### Installation

The HuggingFace model requires `ultralyticsplus`, which has version conflicts with newer `ultralytics`. To use it:

**Option A: Use compatible versions (temporary virtualenv)**
```bash
# Create a separate environment for HuggingFace model
pip install ultralyticsplus==0.0.23 ultralytics==8.0.21
```

**Option B: Use the model directly (recommended)**
The detection service can download and use the model directly from HuggingFace without `ultralyticsplus`:

Update your `.env` or `devenv.nix`:
```bash
YOLO_MODEL_HUGGINGFACE=kesimeg/yolov8n-clothing-detection
```

### Model Features

- **Detects**: shirt, pants, dress, jacket, skirt, shorts, sweater, t-shirt, shoes, sneakers, boots, sandals, bag, handbag, backpack, watch, hat, sunglasses
- **Accuracy**: Much better than default COCO model for fashion items
- **Speed**: Fast inference on CPU/GPU

## Option 2: Custom Trained Model

### Download Fashionpedia Model

1. Download a Fashionpedia-trained YOLOv8 model (or train your own)
2. Place it in `./models/` directory
3. Set environment variable:
   ```bash
   YOLO_MODEL_PATH=./models/yolov8_fashionpedia.pt
   ```

### Training Your Own Model

1. **Prepare dataset** with fashion item annotations
2. **Train YOLOv8**:
   ```bash
   yolo train data=fashion.yaml model=yolov8n.pt epochs=100
   ```
3. **Export best model**:
   ```bash
   yolo export model=runs/detect/train/weights/best.pt format=onnx
   ```
4. **Use the model**:
   ```bash
   YOLO_MODEL_PATH=./models/your_custom_model.pt
   ```

## Option 3: Use Default COCO Model (Limited)

The default COCO model only detects:
- `person` → mapped to `clothing`
- `handbag`, `backpack` → mapped to `bags`
- `tie` → mapped to `accessories`

**Limitations**: Does not detect shoes, most clothing types, or other fashion items.

## Configuration

### Environment Variables

```bash
# Custom model path (highest priority)
YOLO_MODEL_PATH=./models/yolov8_fashion.pt

# HuggingFace model name (if ultralyticsplus available)
YOLO_MODEL_HUGGINGFACE=kesimeg/yolov8n-clothing-detection

# Device
DEVICE=cuda  # or cpu
```

### In devenv.nix

```nix
env = {
  YOLO_MODEL_PATH = "./models/yolov8_fashion.pt";
  YOLO_MODEL_HUGGINGFACE = "kesimeg/yolov8n-clothing-detection";
  DEVICE = "cpu";  # or "cuda"
};
```

## Model Detection

The service automatically detects the model type and uses appropriate class mappings:

- **clothing_detection**: HuggingFace fashion model
- **fashionpedia**: Fashionpedia-trained models
- **coco**: Default COCO model

## Usage

The detection service will automatically use the best available model:

```python
from services import get_detection_service

detection_service = get_detection_service()
items = detection_service.detect_items(image)
```

## Troubleshooting

### Model not loading

1. **Check model path**: Ensure `YOLO_MODEL_PATH` points to valid file
2. **Check HuggingFace access**: Ensure internet connection for HuggingFace models
3. **Check device**: Ensure CUDA available if using GPU

### Low detection accuracy

1. **Use fashion-specific model**: Default COCO model has limited fashion classes
2. **Adjust confidence threshold**: Lower threshold in `detect_items(image, conf_threshold=0.2)`
3. **Train custom model**: For domain-specific items

### Version conflicts

If `ultralyticsplus` conflicts with `ultralytics`:
- Use custom model path instead
- Or use compatible versions in separate environment

## Recommended Setup

For best results:

1. **Use HuggingFace model** (if possible):
   ```bash
   # Install in separate environment or use model directly
   YOLO_MODEL_HUGGINGFACE=kesimeg/yolov8n-clothing-detection
   ```

2. **Or train custom model** on your specific dataset

3. **Fallback to visual similarity**: Even if detection fails, the system uses FashionCLIP for visual similarity search

## Next Steps

- [ ] Download/train fashion-specific model
- [ ] Set `YOLO_MODEL_PATH` or `YOLO_MODEL_HUGGINGFACE`
- [ ] Test detection on sample images
- [ ] Monitor detection accuracy and adjust confidence thresholds

