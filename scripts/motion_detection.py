"""
OpenCV image experiments and real-time motion detection.

This script supports two learning/demo paths:
- Image preprocessing experiments: channels, grayscale, crop, blur, threshold, Canny.
- Webcam motion detection: frame differencing with filtering and bounding boxes.

Examples:
    python scripts/motion_detection.py --image images/sample.jpg --no-display
    python scripts/motion_detection.py --webcam
    python scripts/motion_detection.py --webcam --min-area 1200 --learning-rate 0.04
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np

try:
    import torch
except ImportError:  # Torch is useful for the lesson, but motion detection does not require it.
    torch = None


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = ROOT_DIR / "images" / "sample.jpg"
OUTPUT_DIR = ROOT_DIR / "outputs" / "motion"


def resize_to_width(image: np.ndarray, width: int) -> np.ndarray:
    height, current_width = image.shape[:2]
    scale = width / current_width
    return cv2.resize(image, (width, int(height * scale)), interpolation=cv2.INTER_AREA)


def put_hud(frame: np.ndarray, lines: list[str]) -> None:
    if not lines:
        return

    line_height = 24
    pad = 10
    width = 430
    height = pad * 2 + line_height * len(lines)
    cv2.rectangle(frame, (8, 8), (width, height), (0, 0, 0), cv2.FILLED)
    for index, line in enumerate(lines):
        y = 8 + pad + 18 + index * line_height
        cv2.putText(
            frame,
            line,
            (18, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )


def torch_tensor_summary(image: np.ndarray) -> str:
    if torch is None:
        return "PyTorch not installed; skipped tensor conversion."

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    tensor = torch.from_numpy(rgb).permute(2, 0, 1).float() / 255.0
    return (
        f"PyTorch tensor: shape={tuple(tensor.shape)}, "
        f"dtype={tensor.dtype}, min={tensor.min():.3f}, max={tensor.max():.3f}"
    )


def create_preprocessing_outputs(image_path: Path, width: int, display: bool) -> None:
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    image = resize_to_width(image, width)
    height, frame_width = image.shape[:2]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    _, threshold = cv2.threshold(blurred, 120, 255, cv2.THRESH_BINARY)
    adaptive = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        21,
        5,
    )
    edges = cv2.Canny(blurred, 50, 150)

    crop = image[height // 4 : height * 3 // 4, frame_width // 4 : frame_width * 3 // 4]
    blue, green, red = cv2.split(image)
    channel_stack = np.hstack(
        [
            cv2.cvtColor(blue, cv2.COLOR_GRAY2BGR),
            cv2.cvtColor(green, cv2.COLOR_GRAY2BGR),
            cv2.cvtColor(red, cv2.COLOR_GRAY2BGR),
        ]
    )

    noisy = add_salt_pepper_noise(image, amount=0.02)
    noisy_edges = cv2.Canny(cv2.cvtColor(noisy, cv2.COLOR_BGR2GRAY), 50, 150)
    dark = cv2.convertScaleAbs(image, alpha=0.55, beta=-20)
    bright = cv2.convertScaleAbs(image, alpha=1.25, beta=35)

    outputs = {
        "01_original.jpg": image,
        "02_grayscale.jpg": gray,
        "03_crop_center.jpg": crop,
        "04_blur.jpg": blurred,
        "05_threshold_fixed.jpg": threshold,
        "06_threshold_adaptive.jpg": adaptive,
        "07_canny_edges.jpg": edges,
        "08_bgr_channels.jpg": channel_stack,
        "09_noisy_input.jpg": noisy,
        "10_noisy_canny_edges.jpg": noisy_edges,
        "11_dark_lighting.jpg": dark,
        "12_bright_lighting.jpg": bright,
    }

    for filename, output in outputs.items():
        cv2.imwrite(str(OUTPUT_DIR / filename), output)

    print(f"Image loaded: {image_path}")
    print(f"OpenCV image array shape: {image.shape} (height, width, BGR channels)")
    print(f"Grayscale shape: {gray.shape} (single intensity channel)")
    print(torch_tensor_summary(image))
    print(f"Saved preprocessing outputs to: {OUTPUT_DIR}")

    if display:
        show_grid(
            [
                ("Original", image),
                ("Gray", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)),
                ("Blur", cv2.cvtColor(blurred, cv2.COLOR_GRAY2BGR)),
                ("Threshold", cv2.cvtColor(threshold, cv2.COLOR_GRAY2BGR)),
                ("Canny", cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)),
                ("Noisy Canny", cv2.cvtColor(noisy_edges, cv2.COLOR_GRAY2BGR)),
            ]
        )


def add_salt_pepper_noise(image: np.ndarray, amount: float) -> np.ndarray:
    noisy = image.copy()
    total_pixels = image.shape[0] * image.shape[1]
    count = int(total_pixels * amount)

    ys = np.random.randint(0, image.shape[0], count)
    xs = np.random.randint(0, image.shape[1], count)
    noisy[ys, xs] = 255

    ys = np.random.randint(0, image.shape[0], count)
    xs = np.random.randint(0, image.shape[1], count)
    noisy[ys, xs] = 0
    return noisy


def show_grid(images: list[tuple[str, np.ndarray]]) -> None:
    resized = []
    for title, image in images:
        thumb = resize_to_width(image, 320)
        cv2.putText(thumb, title, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2)
        resized.append(thumb)

    row_one = np.hstack(resized[:3])
    row_two = np.hstack(resized[3:])
    grid = np.vstack([row_one, row_two])
    cv2.imshow("Preprocessing experiments", grid)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def preprocess_motion_frame(frame: np.ndarray, width: int, blur_kernel: int) -> tuple[np.ndarray, np.ndarray]:
    frame = resize_to_width(frame, width)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)
    return frame, gray


def boxes_are_near(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
    padding: int = 18,
) -> bool:
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    return not (
        ax + aw + padding < bx
        or bx + bw + padding < ax
        or ay + ah + padding < by
        or by + bh + padding < ay
    )


def union_box(first: tuple[int, int, int, int], second: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    x1 = min(ax, bx)
    y1 = min(ay, by)
    x2 = max(ax + aw, bx + bw)
    y2 = max(ay + ah, by + bh)
    return x1, y1, x2 - x1, y2 - y1


def merge_nearby_boxes(boxes: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    if not boxes:
        return []

    merged: list[tuple[int, int, int, int]] = []
    for box in boxes:
        matched = False
        for index, existing in enumerate(merged):
            if boxes_are_near(existing, box):
                merged[index] = union_box(existing, box)
                matched = True
                break
        if not matched:
            merged.append(box)

    return merged


def detect_motion_regions(
    gray: np.ndarray,
    background: np.ndarray,
    threshold_value: int,
    min_area: int,
    dilate_iterations: int,
) -> tuple[list[tuple[int, int, int, int]], np.ndarray]:
    delta = cv2.absdiff(background.astype("uint8"), gray)
    _, mask = cv2.threshold(delta, threshold_value, 255, cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=dilate_iterations)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        boxes.append(cv2.boundingRect(contour))

    return merge_nearby_boxes(boxes), mask


def run_motion_detection(
    camera: int,
    width: int,
    threshold_value: int,
    min_area: int,
    learning_rate: float,
    blur_kernel: int,
    dilate_iterations: int,
    hold_frames: int,
    fullscreen: bool = False,
) -> None:
    capture = cv2.VideoCapture(camera)
    if not capture.isOpened():
        raise RuntimeError(f"Could not open webcam index {camera}")

    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    background = None
    previous_time = time.perf_counter()
    recent_counts: deque[int] = deque(maxlen=max(1, hold_frames))
    last_boxes: list[tuple[int, int, int, int]] = []

    window_name = "Motion Detection"
    cv2.namedWindow(window_name)
    if fullscreen:
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print("Motion detection started. Press 'q' to quit, 'r' to reset background.")

    while True:
        ok, frame = capture.read()
        if not ok:
            print("Could not read frame from webcam.")
            break

        frame, gray = preprocess_motion_frame(frame, width, blur_kernel)
        if background is None:
            background = gray.astype("float")
            continue

        boxes, mask = detect_motion_regions(
            gray,
            background,
            threshold_value=threshold_value,
            min_area=min_area,
            dilate_iterations=dilate_iterations,
        )
        cv2.accumulateWeighted(gray, background, learning_rate)

        recent_counts.append(len(boxes))
        if boxes:
            last_boxes = boxes
        elif sum(recent_counts) == 0:
            last_boxes = []

        for x, y, w, h in last_boxes:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 200, 255), 2)
            cv2.putText(
                frame,
                "motion",
                (x, max(20, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 200, 255),
                2,
                cv2.LINE_AA,
            )

        now = time.perf_counter()
        fps = 1.0 / max(now - previous_time, 1e-6)
        previous_time = now
        put_hud(
            frame,
            [
                f"FPS: {fps:.1f} | boxes: {len(last_boxes)}",
                f"threshold: {threshold_value} | min area: {min_area}",
                "q: quit | r: reset background",
            ],
        )

        cv2.imshow(window_name, frame)
        # cv2.imshow("Motion Mask", mask)  # Commented out - debug mask not needed
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("r"):
            background = gray.astype("float")
            last_boxes = []
            recent_counts.clear()

    capture.release()
    cv2.destroyAllWindows()


def odd_kernel(value: int) -> int:
    value = max(3, value)
    return value if value % 2 == 1 else value + 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Image preprocessing experiments and webcam motion detection."
    )
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE, help="Image for preprocessing.")
    parser.add_argument("--webcam", action="store_true", help="Run webcam motion detection.")
    parser.add_argument("--camera", type=int, default=0, help="Webcam index.")
    parser.add_argument("--width", type=int, default=1280, help="Processing/display width.")
    parser.add_argument("--threshold", type=int, default=28, help="Motion mask threshold.")
    parser.add_argument("--min-area", type=int, default=900, help="Smallest motion contour area.")
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.03,
        help="Background update speed. Lower values resist lighting flicker.",
    )
    parser.add_argument("--blur-kernel", type=int, default=21, help="Gaussian blur kernel size.")
    parser.add_argument("--dilate", type=int, default=2, help="Motion mask dilation iterations.")
    parser.add_argument("--hold-frames", type=int, default=3, help="Frames to keep boxes stable.")
    parser.add_argument("--fullscreen", action="store_true", help="Display in fullscreen mode.")
    parser.add_argument("--no-display", action="store_true", help="Save outputs without GUI windows.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if args.webcam:
            run_motion_detection(
                camera=args.camera,
                width=args.width,
                threshold_value=args.threshold,
                min_area=args.min_area,
                learning_rate=args.learning_rate,
                blur_kernel=odd_kernel(args.blur_kernel),
                dilate_iterations=args.dilate,
                hold_frames=args.hold_frames,
                fullscreen=args.fullscreen,
            )
        else:
            create_preprocessing_outputs(args.image, args.width, display=not args.no_display)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
