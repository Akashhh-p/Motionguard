from pathlib import Path
import sys

import cv2

ROOT = Path(__file__).resolve().parent.parent
BACKEND = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import get_settings  # noqa: E402
from backend.app.services.yolo_service import detect_frame, get_yolo_model  # noqa: E402


def main() -> int:
    settings = get_settings()
    model_path = Path(settings.yolo_model_path)
    image_path = BACKEND / "sample_images" / "test.jpg"
    output_path = BACKEND / "sample_images" / "test_output.jpg"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"YOLO model path: {model_path}")
    print(f"YOLO model exists: {model_path.exists()}")
    if not model_path.exists():
        print("ERROR: yolov8n.pt is missing. Set YOLO_MODEL_PATH or place yolov8n.pt at the project root.")
        return 2

    model = get_yolo_model()
    print(f"Model loaded: {model.__class__.__name__}")
    print(f"Test image path: {image_path}")
    if not image_path.exists():
        print("ERROR: sample_images/test.jpg is missing. Add a real test image, then rerun this script.")
        return 3

    frame = cv2.imread(str(image_path))
    if frame is None:
        print("ERROR: OpenCV could not decode sample_images/test.jpg")
        return 4

    detections = detect_frame(frame, confidence=0.25, allowed_classes=None)
    print(f"Detections count: {len(detections)}")
    for item in detections:
        box = [round(value, 2) for value in item["bbox"]]
        print(f"{item['class_name']} conf={item['confidence']:.3f} bbox={box}")
        x1, y1, x2, y2 = [int(value) for value in item["bbox"]]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (99, 102, 241), 2)
        cv2.putText(frame, f"{item['class_name']} {item['confidence']:.2f}", (x1, max(22, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (99, 102, 241), 2)

    cv2.imwrite(str(output_path), frame)
    print(f"Saved output image: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
