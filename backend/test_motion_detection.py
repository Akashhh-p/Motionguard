from pathlib import Path
import argparse
import sys
import time

import cv2

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.motion_service import detect_motion_regions, reset_motion_state  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description="Standalone MotionGuard OpenCV MOG2 motion test.")
    parser.add_argument("--source", default="0", help="Webcam index or video path. Default: 0")
    parser.add_argument("--output", default=str(Path(__file__).resolve().parent / "sample_images" / "motion_debug_output.mp4"))
    parser.add_argument("--min-area", type=int, default=500)
    parser.add_argument("--frames", type=int, default=600)
    return parser.parse_args()


def source_value(value: str):
    return int(value) if value.isdigit() else value


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(source_value(args.source))
    if not capture.isOpened():
        print(f"ERROR: Could not open source: {args.source}")
        return 2

    reset_motion_state(999999)
    writer = None
    last = time.perf_counter()
    frames = 0
    print("Running MOG2 motion detection. Press q in the preview window to stop.")

    while frames < args.frames:
        ok, frame = capture.read()
        if not ok or frame is None:
            break
        started = time.perf_counter()
        result = detect_motion_regions(999999, frame, threshold=16, min_area=args.min_area, resize_width=640)
        fps = 1.0 / max(time.perf_counter() - started, 1e-6)

        for box in result["motion_boxes"]:
            x1, y1, x2, y2 = box["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 153, 255), 2)
            cv2.putText(frame, f"motion {box['area']}", (x1, max(22, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 153, 255), 2)
        cv2.putText(frame, f"FPS {fps:.1f} boxes {len(result['motion_boxes'])}", (16, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (5, 150, 105), 2)

        if writer is None:
            height, width = frame.shape[:2]
            writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), 20, (width, height))
        writer.write(frame)
        cv2.imshow("MotionGuard motion debug", frame)
        frames += 1
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        last = time.perf_counter()

    capture.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()
    print(f"Processed frames: {frames}")
    print(f"Saved debug video: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
