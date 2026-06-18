import cv2
import numpy as np


class MotionState:
    def __init__(self) -> None:
        self.previous_gray = None
        self.last_event_at = 0.0
        self.subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)
        self.held_boxes: list[dict] = []
        self.hold_frames = 0


_states: dict[int, MotionState] = {}


def preprocess_frame(frame: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(gray, (21, 21), 0)


def merge_motion_boxes(boxes: list[list[int]], padding: int = 18) -> list[list[int]]:
    merged: list[list[int]] = []
    for box in boxes:
        x1, y1, x2, y2 = box
        matched = False
        for index, existing in enumerate(merged):
            ex1, ey1, ex2, ey2 = existing
            if not (x2 + padding < ex1 or ex2 + padding < x1 or y2 + padding < ey1 or ey2 + padding < y1):
                merged[index] = [min(x1, ex1), min(y1, ey1), max(x2, ex2), max(y2, ey2)]
                matched = True
                break
        if not matched:
            merged.append(box)
    return merged


def reset_motion_state(user_id: int) -> None:
    _states.pop(user_id, None)


def resize_frame(frame: np.ndarray, resize_width: int) -> tuple[np.ndarray, float]:
    height, width = frame.shape[:2]
    if resize_width <= 0 or width <= resize_width:
        return frame, 1.0
    scale = resize_width / width
    resized = cv2.resize(frame, (resize_width, int(height * scale)), interpolation=cv2.INTER_AREA)
    return resized, 1 / scale


def scale_box(box: list[int], scale_back: float) -> list[int]:
    return [int(round(value * scale_back)) for value in box]


def detect_motion_regions(
    user_id: int,
    frame: np.ndarray,
    threshold: int = 16,
    min_area: int = 500,
    learning_rate: float = -1,
    blur_kernel: int = 5,
    morph_iterations: int = 2,
    resize_width: int = 640,
) -> dict:
    state = _states.setdefault(user_id, MotionState())
    resized, scale_back = resize_frame(frame, resize_width)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    kernel = max(3, blur_kernel if blur_kernel % 2 == 1 else blur_kernel + 1)
    gray = cv2.GaussianBlur(gray, (kernel, kernel), 0)
    mask = state.subtractor.apply(gray, learningRate=learning_rate)
    _, mask = cv2.threshold(mask, threshold, 255, cv2.THRESH_BINARY)
    foreground_pixels = int(cv2.countNonZero(mask))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=max(1, morph_iterations))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=1)
    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=max(1, morph_iterations))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes: list[dict] = []
    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        boxes.append({"bbox": scale_box([int(x), int(y), int(x + w), int(y + h)], scale_back), "area": int(area * scale_back * scale_back)})
    merged = merge_motion_box_objects(boxes)
    if merged:
        state.held_boxes = merged
        state.hold_frames = 3
    elif state.hold_frames > 0:
        state.hold_frames -= 1
        merged = state.held_boxes
    else:
        state.held_boxes = []
    return {
        "motion_detected": bool(merged),
        "motion_boxes": merged,
        "motion_count": len(merged),
        "estimated_moving_subjects": len(merged),
        "motion_area_total": int(sum(item["area"] for item in merged)),
        "debug": {
            "input_shape": list(frame.shape),
            "resized_shape": list(resized.shape),
            "foreground_pixels": foreground_pixels,
            "contours_found": len(contours),
            "boxes_after_filter": len(boxes),
            "boxes_after_merge": len(merged),
            "min_area": min_area,
            "threshold": threshold,
        },
    }


def merge_motion_box_objects(boxes: list[dict], padding: int = 18) -> list[dict]:
    merged: list[dict] = []
    for item in boxes:
        box = item["bbox"]
        x1, y1, x2, y2 = box
        matched = False
        for existing in merged:
            ex1, ey1, ex2, ey2 = existing["bbox"]
            if not (x2 + padding < ex1 or ex2 + padding < x1 or y2 + padding < ey1 or ey2 + padding < y1):
                existing["bbox"] = [min(x1, ex1), min(y1, ey1), max(x2, ex2), max(y2, ey2)]
                existing["area"] += item["area"]
                matched = True
                break
        if not matched:
            merged.append({"bbox": box, "area": item["area"]})
    return merged


def motion_box_center(box: dict) -> tuple[float, float]:
    x1, y1, x2, y2 = box["bbox"]
    return ((x1 + x2) / 2, (y1 + y2) / 2)
