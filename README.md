# MotionGuard

MotionGuard is a Python computer vision project for image processing, real-time YOLOv8 object detection, and webcam-based motion detection using OpenCV.

## 🎯 Features

- **Image Processing**: Resize images while preserving aspect ratio and convert to grayscale
- **Real-time Detection**: Live object detection using YOLOv8 on webcam feeds
- **Bounding Boxes**: Visual detection results with confidence scores
- **FPS Monitoring**: Real-time performance metrics display
- **Flexible Configuration**: Easily adjustable detection parameters and output options

## 📋 Project Structure

```
motionguard/
├── scripts/
│   ├── image_basics.py          # Image processing and YOLOv8 object detection
│   └── motion_detection.py       # Motion detection and preprocessing experiments
├── images/
│   └── sample.jpg               # Sample image for testing
├── outputs/
│   ├── resized.jpg              # Resized output image
│   ├── grayscale.jpg            # Grayscale output image
│   └── motion/                  # Motion detection preprocessing outputs
├── Ultralytics/
│   └── settings.json            # YOLOv8 configuration
├── yolov8n.pt                   # Pre-downloaded YOLOv8 nano model
├── requirements.txt             # Python dependencies
├── run.sh                        # Convenient run script
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip or conda package manager
- Webcam (for real-time detection mode)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Akashhh-p/motionguard.git
   cd motionguard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Or using the run script (Linux/Mac):
   ```bash
   chmod +x run.sh
   ./run.sh --help
   ```

### Basic Usage

#### Option 1: Process a single image
```bash
python scripts/image_basics.py --image images/sample.jpg
```

With custom output width:
```bash
python scripts/image_basics.py --image images/sample.jpg --width 800
```

Without GUI display:
```bash
python scripts/image_basics.py --image images/sample.jpg --no-display
```

#### Option 2: Run webcam detection
```bash
python scripts/image_basics.py --webcam
```

With specific camera (if multiple cameras available):
```bash
python scripts/image_basics.py --webcam --camera 0
```

With custom confidence threshold:
```bash
python scripts/image_basics.py --webcam --conf 0.5
```

#### Using the run script (Linux/Mac)
```bash
./run.sh --image images/sample.jpg
./run.sh --webcam --camera 0 --conf 0.5
```

## 📊 Command-line Arguments

### Image Processing
- `--image PATH` - Path to image file (default: `images/sample.jpg`)
- `--width WIDTH` - Output width in pixels (default: `640`)
- `--no-display` - Process without opening GUI windows
- `--display` - Show results in windows (default)

### Webcam Detection
- `--webcam` - Enable real-time webcam detection
- `--camera INDEX` - Webcam index to use (default: `0`)
- `--model MODEL` - YOLOv8 model name (default: `yolov8n.pt`)
- `--conf THRESHOLD` - Detection confidence threshold 0-1 (default: `0.35`)

### General
- `--help` - Display help message
- `--width WIDTH` - Output/display width (default: `640`)

## 📁 File Descriptions

### scripts/image_basics.py
Main script for image processing and YOLOv8 object detection.

**Key Functions:**
- `resize_to_width()` - Resize images while preserving aspect ratio
- `draw_label()` - Draw labeled rectangles with text
- `draw_detection()` - Render bounding boxes with confidence scores
- `add_status_overlay()` - Display FPS and detection count
- `process_image()` - Load, process, and save images
- `load_yolo_model()` - Initialize YOLOv8 model
- `run_webcam_detection()` - Execute real-time detection loop
- `parse_args()` - Parse command-line arguments
- `main()` - Application entry point

### scripts/motion_detection.py
Motion detection and image preprocessing experiments using OpenCV.

**Capabilities:**
- Image preprocessing pipeline: grayscale, blur, threshold, Canny edge detection
- Channel decomposition and visualization
- Noise addition and robustness testing
- Real-time webcam motion detection with frame differencing
- Bounding box detection and merging for moving objects
- Configurable sensitivity and filtering parameters

**Key Functions:**
- `create_preprocessing_outputs()` - Generate preprocessing demonstration images
- `preprocess_motion_frame()` - Prepare frames for motion detection
- `detect_motion_regions()` - Find moving objects using frame differencing
- `merge_nearby_boxes()` - Combine overlapping detections
- `run_motion_detection()` - Execute real-time motion detection loop

## 🔧 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| opencv-python | 4.8.1.78 | Image processing and video capture |
| ultralytics | 8.0.212 | YOLOv8 object detection framework |
| torch | 2.1.1 | Deep learning backend |
| torchvision | 0.16.1 | Computer vision utilities |
| numpy | ≥24.0 | Numerical computing |
| pillow | ≥10.0.0 | Image manipulation |

See `requirements.txt` for complete list.

## 📸 Output

### Image Processing
- **resized.jpg**: Image resized to specified width with aspect ratio preserved
- **grayscale.jpg**: Grayscale version of the input image

### Webcam Detection
- Live display with:
  - Bounding boxes around detected objects
  - Confidence scores for each detection
  - Real-time FPS counter
  - Detection count overlay

## 💡 Usage Examples

```bash
# Process sample image with 640px width
python scripts/image_basics.py

# Process custom image
python scripts/image_basics.py --image path/to/your/image.jpg

# Process at 1280px width
python scripts/image_basics.py --image path/to/image.jpg --width 1280

# Run live detection without display
python scripts/image_basics.py --webcam --no-display

# Run detection with 50% confidence threshold
python scripts/image_basics.py --webcam --conf 0.5

# Using run script
./run.sh --webcam --camera 0 --conf 0.4
```

### Motion Detection

The project includes a frame-differencing motion detection script and preprocessing experiments:

#### Image Preprocessing Demo
Generate learning materials showing image transformations:
```bash
# Process image and save preprocessing outputs
python scripts/motion_detection.py --image images/sample.jpg

# Process without GUI display
python scripts/motion_detection.py --image images/sample.jpg --no-display
```

Outputs saved to `outputs/motion/` include:
- Grayscale conversion
- Gaussian blur effects
- Binary threshold
- Adaptive threshold
- Canny edge detection
- Color channel decomposition
- Noise robustness testing
- Lighting variation effects

#### Real-time Motion Detection
```bash
# Run live webcam motion detection
python scripts/motion_detection.py --webcam

# Tune for specific environment
python scripts/motion_detection.py --webcam --threshold 35 --min-area 1500

# Adjust background learning rate (lower = more stable in changing lighting)
python scripts/motion_detection.py --webcam --learning-rate 0.02
```

**Motion Detection Parameters:**
- `--threshold VALUE` - Motion sensitivity threshold (default: 28)
- `--min-area PIXELS` - Minimum object area to detect (default: 900)
- `--learning-rate RATE` - Background update speed 0-1 (default: 0.03)
- `--blur-kernel SIZE` - Gaussian blur kernel (default: 21, must be odd)
- `--dilate ITERATIONS` - Dilation iterations for mask (default: 2)
- `--hold-frames COUNT` - Frames to stabilize boxes (default: 3)

## 🔄 Workflow

### Image Processing Workflow
1. Load image from disk
2. Create output directory if not exists
3. Resize image to target width
4. Convert to grayscale
5. Save outputs to `outputs/` folder
6. Display results (if not `--no-display`)

### Webcam Detection Workflow
1. Load YOLOv8 model
2. Initialize webcam capture
3. For each frame:
   - Run YOLO inference
   - Extract bounding boxes and confidence scores
   - Draw detections on frame
   - Calculate FPS metrics
   - Display with overlay
4. Exit on 'q' key press

## ⚙️ Configuration

### Ultralytics Settings
Configuration stored in `Ultralytics/settings.json`. This is set up automatically by the ultralytics package.

### YOLOv8 Models
Available models (auto-downloaded on first use):
- `yolov8n.pt` - Nano (fastest)
- `yolov8s.pt` - Small
- `yolov8m.pt` - Medium
- `yolov8l.pt` - Large
- `yolov8x.pt` - Extra Large (most accurate)

## 📝 Performance Tips

- Use `yolov8n.pt` (nano) for real-time webcam detection on CPU
- Reduce `--width` for faster processing on low-end hardware
- Increase `--conf` threshold to reduce false positives
- Use GPU if available for significantly faster inference

## 🐛 Troubleshooting

### Webcam not detected
- Check if camera index is correct: `--camera 0`, `--camera 1`, etc.
- Ensure webcam is not in use by another application
- Try running with verbose output

### Out of memory errors
- Reduce image width: `--width 480`
- Use smaller model: `--model yolov8n.pt`
- Process images without display: `--no-display`

### Slow performance
- Use GPU acceleration (if available)
- Use nano model: `yolov8n.pt`
- Reduce frame width
- Increase confidence threshold: `--conf 0.5`

### Missing dependencies
- Run: `pip install -r requirements.txt`
- Or: `pip install --upgrade pip setuptools`

## 📄 License

This project is provided as-is for educational and research purposes.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 📧 Support

For issues, questions, or suggestions, please open an issue on the GitHub repository.

---

**Last Updated**: 2026  
**Python Version**: 3.8+  
**Status**: Active Development
