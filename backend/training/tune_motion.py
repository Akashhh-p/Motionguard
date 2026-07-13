from __future__ import annotations

import argparse
import csv
from itertools import product
from pathlib import Path
import sys

import cv2


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.motion_service import detect_motion_regions, reset_motion_state  # noqa: E402


def parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare MotionGuard motion detection settings on a video.")
    parser.add_argument("--source", required=True, help="Video path or webcam index.")
    parser.add_argument("--output", default=str(Path(__file__).resolve().parent / "runs" / "motion_tuning.csv"))
    parser.add_argument("--frames", type=int, default=500)
    parser.add_argument("--thresholds", default="12,16,22,28")
    parser.add_argument("--min-areas", default="300,500,900,1400")
    parser.add_argument("--resize-width", type=int, default=640)
    return parser.parse_args()


def source_value(value: str):
    return int(value) if value.isdigit() else value


def evaluate(source: str, frames: int, threshold: int, min_area: int, resize_width: int) -> dict:
    capture = cv2.VideoCapture(source_value(source))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open source: {source}")

    state_id = abs(hash((source, threshold, min_area))) % 1_000_000_000
    reset_motion_state(state_id)

    processed = 0
    motion_frames = 0
    total_boxes = 0
    total_area = 0

    while processed < frames:
        ok, frame = capture.read()
        if not ok or frame is None:
            break
        result = detect_motion_regions(
            state_id,
            frame,
            threshold=threshold,
            min_area=min_area,
            resize_width=resize_width,
        )
        processed += 1
        if result["motion_detected"]:
            motion_frames += 1
        total_boxes += result["motion_count"]
        total_area += result["motion_area_total"]

    capture.release()
    reset_motion_state(state_id)

    return {
        "threshold": threshold,
        "min_area": min_area,
        "frames": processed,
        "motion_frames": motion_frames,
        "motion_frame_rate": round(motion_frames / max(processed, 1), 4),
        "avg_boxes_per_frame": round(total_boxes / max(processed, 1), 4),
        "avg_motion_area": round(total_area / max(processed, 1), 2),
    }


def main() -> int:
    args = parse_args()
    thresholds = parse_int_list(args.thresholds)
    min_areas = parse_int_list(args.min_areas)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for threshold, min_area in product(thresholds, min_areas):
        row = evaluate(args.source, args.frames, threshold, min_area, args.resize_width)
        rows.append(row)
        print(row)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved tuning report: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
