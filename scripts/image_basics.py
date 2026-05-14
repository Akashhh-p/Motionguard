"""
OpenCV Image Processing and YOLOv8 Real-time Detection Module

This module provides functionality for:
- Image processing (resizing, grayscale conversion)
- Real-time object detection using YOLOv8 on webcam feeds
- Visualization with bounding boxes and confidence scores

Usage:
    Process an image:
        python image_basics.py --image path/to/image.jpg
    
    Run webcam detection:
        python image_basics.py --webcam
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import cv2

# Project root directory path
ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = ROOT_DIR / "images" / "sample.jpg"
OUTPUT_DIR = ROOT_DIR / "outputs"


def resize_to_width(image, width: int):
    """
    Resize image to specified width while preserving aspect ratio.
    
    Args:
        image: Input image as numpy array (OpenCV format BGR)
        width: Target width in pixels
        
    Returns:
        Resized image maintaining original aspect ratio
    """
    height, current_width = image.shape[:2]
    scale = width / current_width
    return cv2.resize(image, (width, int(height * scale)), interpolation=cv2.INTER_AREA)


def draw_label(frame, text: str, x: int, y: int, color=(0, 180, 255)) -> None:
    """
    Draw a labeled rectangle with text on the frame.
    
    Args:
        frame: Target frame to draw on (OpenCV image)
        text: Text to display in the label
        x, y: Top-left coordinates for label placement
        color: BGR color tuple (default: orange for labels)
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    thickness = 2
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    y = max(y, text_h + baseline + 6)

    cv2.rectangle(
        frame,
        (x, y - text_h - baseline - 6),
        (x + text_w + 8, y + baseline - 2),
        color,
        cv2.FILLED,
    )
    cv2.putText(frame, text, (x + 4, y - 6), font, font_scale, (20, 20, 20), thickness, cv2.LINE_AA)


def draw_detection(frame, box, label: str, confidence: float) -> None:
    """
    Draw a bounding box with label and confidence score on the frame.
    
    Args:
        frame: Target frame to draw on
        box: Bounding box coordinates [x1, y1, x2, y2]
        label: Object class label
        confidence: Detection confidence score (0-1)
    """
    x1, y1, x2, y2 = [int(value) for value in box]
    color = (0, 180, 255)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    draw_label(frame, f"{label} {confidence:.2f}", x1, y1, color)


def add_status_overlay(frame, fps: float | None = None, detections: int | None = None) -> None:
    """
    Add FPS and detection count overlay to the frame.
    
    Args:
        frame: Target frame for overlay
        fps: Frames per second (optional)
        detections: Number of detected objects (optional)
    """
    parts = []
    if fps is not None:
        parts.append(f"FPS: {fps:.1f}")
    if detections is not None:
        parts.append(f"Objects: {detections}")
    if not parts:
        return

    cv2.rectangle(frame, (8, 8), (210, 42), (0, 0, 0), cv2.FILLED)
    cv2.putText(
        frame,
        " | ".join(parts),
        (16, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def process_image(image_path: Path, width: int, display: bool) -> None:
    """
    Load, process, and save image with resizing and grayscale conversion.
    
    Args:
        image_path: Path to the input image file
        width: Target output width in pixels
        display: Whether to display results in GUI windows
        
    Raises:
        FileNotFoundError: If image file cannot be loaded
    """
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Process image: resize and convert to grayscale
    resized = resize_to_width(image, width)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray_display = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    # Save processed images
    cv2.imwrite(str(OUTPUT_DIR / "resized.jpg"), resized)
    cv2.imwrite(str(OUTPUT_DIR / "grayscale.jpg"), gray)

    print(f"Image loaded: {image_path}")
    print(f"Original shape: {image.shape}")
    print(f"Resized shape: {resized.shape}")
    print(f"Saved: {OUTPUT_DIR / 'resized.jpg'}")
    print(f"Saved: {OUTPUT_DIR / 'grayscale.jpg'}")

    if display:
        cv2.imshow("Original", image)
        cv2.imshow("Resized", resized)
        cv2.imshow("Grayscale", gray_display)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def load_yolo_model(model_name: str):
    """
    Load YOLOv8 model with Ultralytics configuration.
    
    Args:
        model_name: Model identifier (e.g., 'yolov8n.pt') or local path
        
    Returns:
        Loaded YOLO model instance
        
    Raises:
        RuntimeError: If ultralytics package is not installed
    """
    # Set config directory for Ultralytics
    os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT_DIR / "Ultralytics"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            "YOLOv8 is not installed. Install it with: python -m pip install ultralytics"
        ) from exc

    return YOLO(model_name)


def run_webcam_detection(camera: int, model_name: str, width: int, confidence: float) -> None:
    """
    Run real-time YOLOv8 object detection on webcam feed.
    
    Args:
        camera: Webcam index (default 0 for primary camera)
        model_name: YOLOv8 model identifier
        width: Target frame width
        confidence: Detection confidence threshold (0-1)
        
    Raises:
        RuntimeError: If webcam cannot be opened
    """
    model = load_yolo_model(model_name)
    capture = cv2.VideoCapture(camera)

    if not capture.isOpened():
        raise RuntimeError(f"Could not open webcam index {camera}")

    # Set webcam properties for optimal performance
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    previous_time = time.perf_counter()
    print("Webcam detection started. Press 'q' to quit.")

    while True:
        ok, frame = capture.read()
        if not ok:
            print("Could not read frame from webcam.")
            break

        # Run YOLO inference on current frame
        results = model.predict(frame, conf=confidence, verbose=False)
        detections = 0

        # Draw bounding boxes for all detected objects
        for result in results:
            for detection in result.boxes:
                detections += 1
                class_id = int(detection.cls[0])
                label = model.names[class_id]
                score = float(detection.conf[0])
                box = detection.xyxy[0].tolist()
                draw_detection(frame, box, label, score)

        # Calculate and display FPS
        now = time.perf_counter()
        fps = 1.0 / max(now - previous_time, 1e-6)
        previous_time = now
        add_status_overlay(frame, fps=fps, detections=detections)

        cv2.imshow("YOLOv8 Webcam Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    capture.release()
    cv2.destroyAllWindows()


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="OpenCV image processing and YOLOv8 real-time object detection."
    )
    parser.add_argument(
        "--image",
        type=Path,
        default=DEFAULT_IMAGE,
        help="Image path to load and process.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=640,
        help="Output/display width while preserving aspect ratio.",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Process and save outputs without opening GUI windows.",
    )
    parser.add_argument(
        "--webcam",
        action="store_true",
        help="Run real-time YOLOv8 detection from webcam.",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Webcam index.",
    )
    parser.add_argument(
        "--model",
        default="yolov8n.pt",
        help="YOLOv8 model name or local .pt path.",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.35,
        help="YOLO confidence threshold.",
    )
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for the application.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    args = parse_args()

    try:
        if args.webcam:
            # Run real-time webcam detection
            run_webcam_detection(args.camera, args.model, args.width, args.conf)
        else:
            # Process single image
            process_image(args.image, args.width, display=not args.no_display)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
