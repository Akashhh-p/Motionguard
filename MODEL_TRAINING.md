# MotionGuard Model Training

MotionGuard currently uses two detection systems:

- Object detection: YOLOv8, loaded from `YOLO_MODEL_PATH`.
- Motion detection: OpenCV MOG2 background subtraction, tuned with thresholds rather than trained.

## 1. Current Object Detection Dataset

The active training/testing dataset is the uploaded Roboflow YOLO export:

```text
motionguard_datasets/
  train/images, train/labels   # 36,083 images
  valid/images, valid/labels   # 4,112 images
  test/images, test/labels     # 3,474 images
```

It is configured here:

```text
backend/training/datasets/motionguard-person-roboflow.yaml
```

This dataset currently trains one class:

```text
0: person
```

The training and validation scripts use this dataset by default.

## 2. Prepare Additional Object Detection Data

Create this dataset layout:

```text
backend/training/data/motionguard/
  images/
    train/
    val/
    test/
  labels/
    train/
    val/
    test/
```

Each image needs a matching `.txt` label file in YOLO format:

```text
class_id x_center y_center width height
```

Coordinates are normalized from `0` to `1`. The default classes are in:

```text
backend/training/datasets/motionguard.yaml
```

For best results, label real frames from the camera angles and lighting where MotionGuard will run.

## 3. Train YOLO

From the project root:

```powershell
python backend\training\train_yolo.py --epochs 80 --imgsz 640 --batch 8 --device cpu --activate
```

If you have an NVIDIA GPU and CUDA PyTorch is installed, use:

```powershell
python backend\training\train_yolo.py --epochs 100 --imgsz 640 --batch 16 --device 0
```

To copy the best trained checkpoint to the project root:

```powershell
python backend\training\train_yolo.py --epochs 100 --imgsz 640 --batch 16 --device 0 --activate
```

That creates:

```text
motionguard-yolov8-custom.pt
```

Then set this in `.env`:

```env
YOLO_MODEL_PATH=C:\projects\Motionguard\motionguard-yolov8-custom.pt
```

Restart the backend after changing `YOLO_MODEL_PATH`.

For a quick smoke test before a full run, use:

```powershell
python backend\training\train_yolo.py --epochs 1 --imgsz 320 --batch 4 --device cpu --fraction 0.02 --name smoke-person
```

## Open Images CSV Workflow

If you downloaded Open Images CSV files, first convert a manageable subset to YOLO format:

```powershell
python backend\training\prepare_open_images.py `
  --classes-csv C:\Users\akash\Downloads\oidv7-class-descriptions-boxable.csv `
  --train-boxes C:\Users\akash\Downloads\train-annotations-bbox.csv `
  --train-images C:\Users\akash\Downloads\train-images-boxable-with-rotation.csv `
  --val-boxes C:\Users\akash\Downloads\validation-annotations-bbox.csv `
  --val-images C:\Users\akash\Downloads\validation-images-with-rotation.csv `
  --test-boxes C:\Users\akash\Downloads\test-annotations-bbox.csv `
  --test-images C:\Users\akash\Downloads\test-images-with-rotation.csv `
  --max-train 1200 `
  --max-val 300 `
  --max-test 300
```

Then train with the generated YAML:

```powershell
python backend\training\train_yolo.py --data backend\training\datasets\motionguard-openimages.yaml --epochs 80 --imgsz 640 --batch 8 --device cpu --activate
```

The Open Images files named `*-images-*-with-rotation.csv` are image metadata only. You still need `*-annotations-bbox.csv` files for labels.

## 4. Validate YOLO

```powershell
python backend\training\validate_yolo.py --model motionguard-yolov8-custom.pt --device cpu
```

Track these metrics:

- `mAP50`: easier detection quality check.
- `mAP50-95`: stricter overall quality.
- False positives on empty/security-camera scenes.
- Misses on small or partially hidden people.

To evaluate on the held-out test split instead of validation:

```powershell
python backend\training\validate_yolo.py --model motionguard-yolov8-custom.pt --device cpu --split test
```

## 5. Tune Motion Detection

Motion detection is not trained like YOLO. Tune it against your own videos:

```powershell
python backend\training\tune_motion.py --source C:\path\to\camera_video.mp4
```

This writes:

```text
backend/training/runs/motion_tuning.csv
```

Use higher `min_area` to reduce tiny false alerts. Use higher `threshold` to ignore subtle pixel changes. Good starting points:

```powershell
python backend\training\tune_motion.py --source C:\path\to\camera_video.mp4 --thresholds 16,22,28 --min-areas 500,900,1400
```

Then apply the best settings in the MotionGuard Settings page.

## Dataset Tips

- Start with 300-500 labeled frames for a first usable fine-tune.
- Include day, night, glare, shadows, empty rooms, busy rooms, and partial occlusions.
- Add negative images with no objects. They help reduce false positives.
- Keep validation images from different times/videos than training images.
- Do not train only on perfect close-up examples; security footage is usually small, blurry, and angled.
