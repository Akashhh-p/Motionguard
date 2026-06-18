import threading
import time
import cv2
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Detection, User
from .settings_service import get_or_create_settings, settings_classes
from .yolo_service import detect_frame, draw_detections, resize_to_width


class WebcamManager:
    def __init__(self) -> None:
        self.running: dict[int, bool] = {}
        self.latest_frame: dict[int, bytes] = {}
        self.status: dict[int, dict] = {}

    def start(self, user: User, camera_index: int = 0) -> dict:
        if self.running.get(user.id):
            return self.status.get(user.id, {"running": True})
        self.running[user.id] = True
        self.status[user.id] = {"running": True, "fps": 0, "detections": 0, "camera_index": camera_index, "message": "Starting camera"}
        thread = threading.Thread(target=self._loop, args=(user.id, camera_index), daemon=True)
        thread.start()
        return self.status[user.id]

    def stop(self, user_id: int) -> dict:
        self.running[user_id] = False
        self.status[user_id] = {**self.status.get(user_id, {}), "running": False, "message": "Stopped"}
        return self.status[user_id]

    def _loop(self, user_id: int, camera_index: int) -> None:
        db: Session = SessionLocal()
        capture = cv2.VideoCapture(camera_index)
        if not capture.isOpened():
            self.status[user_id] = {"running": False, "message": "Webcam not found", "fps": 0, "detections": 0}
            self.running[user_id] = False
            db.close()
            return
        settings = get_or_create_settings(db, db.get(User, user_id))
        allowed = settings_classes(settings)
        previous = time.perf_counter()
        frame_index = 0
        try:
            while self.running.get(user_id):
                ok, frame = capture.read()
                if not ok:
                    self.status[user_id]["message"] = "Could not read frame"
                    break
                frame_index += 1
                frame = resize_to_width(frame, 960)
                detections = []
                if frame_index % max(1, settings.frame_skip) == 0:
                    detections = detect_frame(frame, settings.confidence_threshold, allowed)
                    for detection in detections:
                        db.add(Detection(user_id=user_id, object_class=detection["object_class"], confidence=detection["confidence"], source_type="webcam", bbox=",".join(str(round(v, 2)) for v in detection["bbox"])))
                    db.commit()
                now = time.perf_counter()
                fps = 1.0 / max(now - previous, 1e-6)
                previous = now
                rendered = draw_detections(frame, detections)
                ok, encoded = cv2.imencode(".jpg", rendered)
                if ok:
                    self.latest_frame[user_id] = encoded.tobytes()
                self.status[user_id] = {"running": True, "fps": round(fps, 1), "detections": len(detections), "camera_index": camera_index, "message": "Monitoring"}
        finally:
            capture.release()
            db.close()
            self.running[user_id] = False

    def stream(self, user_id: int):
        while self.running.get(user_id):
            frame = self.latest_frame.get(user_id)
            if frame:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            time.sleep(0.08)


webcam_manager = WebcamManager()

