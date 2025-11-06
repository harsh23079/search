---
datasets:
- detection-datasets/fashionpedia_4_categories
language:
- en
base_model:
- Ultralytics/YOLOv8
pipeline_tag: object-detection
---


This model is a finetuned version of YOLO-v8n on clothing detection.

### Object categories

- Clothing
- Shoes
- Bags
- Accessories

You can get more information (and code 🎉) on how to train or use the model on my [github].

[github]: https://github.com/kesimeg/YOLO-Clothing-Detection

# How to use the model?

- Install [ultralyticsplus](https://github.com/fcakyon/ultralyticsplus):

```bash
pip install ultralyticsplus==0.0.23 ultralytics==8.0.21
```


- Load model and perform prediction:

```python
from ultralyticsplus import YOLO, render_result

# load model
model = YOLO('kesimeg/yolov8n-clothing-detection')

# set image
image = 'some_image.jpg'

# perform inference
results = model.predict(image)

# observe results
print(results[0].boxes)
render = render_result(model=model, image=image, result=results[0])
render.show()
```

<div align="center">
  <img width="640" alt="kesimeg/yolov8n-clothing-detection" src="https://huggingface.co/kesimeg/yolov8n-clothing-detection/resolve/main/sample_output.png">
</div>