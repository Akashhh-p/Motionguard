from __future__ import annotations

import argparse
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TRAINING_DIR = Path(__file__).resolve().parent
DEFAULT_DATA = TRAINING_DIR / "datasets" / "motionguard-person-roboflow.yaml"
DEFAULT_YOLO_CONFIG_DIR = ROOT / "Ultralytics"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a YOLO checkpoint on the MotionGuard dataset.")
    parser.add_argument("--data", default=str(DEFAULT_DATA))
    parser.add_argument("--model", default=str(ROOT / "motionguard-yolov8-custom.pt"))
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--split", choices=("val", "test"), default="val")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ.setdefault("YOLO_CONFIG_DIR", str(DEFAULT_YOLO_CONFIG_DIR))

    try:
        from ultralytics import YOLO
    except ImportError:
        print("ERROR: ultralytics is not installed. Run: pip install -r backend/requirements.txt")
        return 2

    model_path = Path(args.model).resolve()
    data_path = Path(args.data).resolve()
    if not model_path.exists():
        print(f"ERROR: model checkpoint not found: {model_path}")
        return 3
    if not data_path.exists():
        print(f"ERROR: dataset YAML not found: {data_path}")
        return 4

    metrics = YOLO(str(model_path)).val(
        data=str(data_path),
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        split=args.split,
    )
    print(f"{args.split.capitalize()} validation complete.")
    print(f"mAP50-95: {metrics.box.map:.4f}")
    print(f"mAP50:    {metrics.box.map50:.4f}")
    print(f"mAP75:    {metrics.box.map75:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
