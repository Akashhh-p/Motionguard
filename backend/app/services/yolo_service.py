import importlib
import logging
import os
from functools import lru_cache
from pathlib import Path
import cv2
from fastapi import HTTPException
from ..config import get_settings

logger = logging.getLogger(__name__)


def resize_to_width(frame, width: int):
    height, current_width = frame.shape[:2]
    if current_width <= width:
        return frame
    scale = width / current_width
    return cv2.resize(frame, (width, int(height * scale)), interpolation=cv2.INTER_AREA)


@lru_cache(maxsize=1)
def get_yolo_model():
    settings = get_settings()
    os.environ.setdefault("YOLO_CONFIG_DIR", settings.yolo_config_dir)
    model_path = Path(settings.yolo_model_path)
    if not model_path.exists():
        raise HTTPException(status_code=500, detail=f"YOLO model file is missing at: {model_path}")
    try:
        ultralytics = importlib.import_module("ultralytics")
        model = ultralytics.YOLO(str(model_path))
        logger.info("YOLO model loaded successfully from: %s", model_path)
        return model
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="Ultralytics is not installed.") from exc
    except Exception as exc:
        logger.exception("YOLO model failed to load from %s", model_path)
        raise HTTPException(status_code=500, detail=f"YOLO model failed to load from {model_path}: {exc}") from exc


def detect_frame(frame, confidence: float, allowed_classes: set[str] | None = None) -> list[dict]:
    if frame is None or getattr(frame, "size", 0) == 0:
        raise HTTPException(status_code=400, detail="YOLO input frame is empty.")
    model = get_yolo_model()
    results = model.predict(frame, conf=confidence, verbose=False)
    detections: list[dict] = []
    for result in results:
        if result.boxes is None:
            continue
        for item in result.boxes:
            cls_id = int(item.cls[0])
            label = model.names[cls_id]
            if allowed_classes and label not in allowed_classes:
                continue
            score = float(item.conf[0])
            box = [float(v) for v in item.xyxy[0].tolist()]
            detections.append({"object_class": label, "class_name": label, "confidence": score, "bbox": box})
    return detections


def draw_detections(frame, detections: list[dict], alerts: list[str] | None = None):
    for detection in detections:
        x1, y1, x2, y2 = [int(value) for value in detection["bbox"]]
        color = (37, 99, 235)
        if detection.get("alert"):
            color = (68, 68, 239)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"{detection['object_class']} {detection['confidence']:.2f}"
        cv2.putText(frame, label, (x1, max(22, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    if alerts:
        cv2.rectangle(frame, (12, 12), (520, 54), (239, 68, 68), cv2.FILLED)
        cv2.putText(frame, " | ".join(alerts[:2]), (22, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)
    return frame
