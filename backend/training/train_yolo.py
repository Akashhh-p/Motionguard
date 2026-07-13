from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TRAINING_DIR = Path(__file__).resolve().parent
DEFAULT_DATA = TRAINING_DIR / "datasets" / "motionguard-person-roboflow.yaml"
DEFAULT_PROJECT = TRAINING_DIR / "runs"
DEFAULT_ACTIVATED_MODEL = ROOT / "motionguard-yolov8-custom.pt"
DEFAULT_YOLO_CONFIG_DIR = ROOT / "Ultralytics"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a custom YOLO model for MotionGuard.")
    parser.add_argument("--data", default=str(DEFAULT_DATA), help="Path to YOLO dataset YAML.")
    parser.add_argument("--model", default=str(ROOT / "yolov8n.pt"), help="Base model or checkpoint to fine tune.")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="cpu", help="Use 'cpu', '0', '0,1', etc.")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--name", default="motionguard-yolov8")
    parser.add_argument("--project", default=str(DEFAULT_PROJECT))
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--fraction", type=float, default=1.0, help="Fraction of training data to use, from 0.0 to 1.0.")
    parser.add_argument("--activate", action="store_true", help="Copy best.pt to the project root after training.")
    parser.add_argument("--activate-path", default=str(DEFAULT_ACTIVATED_MODEL))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ.setdefault("YOLO_CONFIG_DIR", str(DEFAULT_YOLO_CONFIG_DIR))

    try:
        from ultralytics import YOLO
    except ImportError:
        print("ERROR: ultralytics is not installed. Run: pip install -r backend/requirements.txt")
        return 2

    data_path = Path(args.data).resolve()
    model_path = Path(args.model).resolve()
    if not data_path.exists():
        print(f"ERROR: dataset YAML not found: {data_path}")
        return 3
    if not model_path.exists() and not args.model.endswith(".yaml"):
        print(f"ERROR: base model not found: {model_path}")
        return 4

    model = YOLO(str(model_path if model_path.exists() else args.model))
    result = model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        project=str(Path(args.project).resolve()),
        name=args.name,
        patience=args.patience,
        fraction=args.fraction,
        exist_ok=True,
    )

    save_dir = Path(getattr(result, "save_dir", Path(args.project) / args.name))
    best_model = save_dir / "weights" / "best.pt"
    print(f"Training run: {save_dir}")
    print(f"Best model: {best_model}")

    if args.activate:
        if not best_model.exists():
            print("ERROR: best.pt was not found, so the model was not activated.")
            return 5
        destination = Path(args.activate_path).resolve()
        shutil.copy2(best_model, destination)
        print(f"Activated model copied to: {destination}")
        print(f"Set YOLO_MODEL_PATH={destination}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
