import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
from ultralytics import YOLO

from app.config import BASE_DIR, settings
from app.supabase_client import insert_event, upload_file


class CameraDetector:
    def __init__(self):
        self.capture = None
        self.model = YOLO(str(settings.model_path)) if settings.model_path.exists() else None
        self.lock = threading.Lock()
        self.last_frame = None
        self.last_detections = []
        self.last_alert_at = 0.0
        self.running = False
        self.buffer = deque(maxlen=max(90, settings.video_seconds * 30))
        self.evidence_dir = BASE_DIR / "evidence"
        self.evidence_dir.mkdir(exist_ok=True)

    def start(self):
        if self.running:
            return
        self._open_camera()
        self.running = True
        thread = threading.Thread(target=self._loop, daemon=True)
        thread.start()

    def stop(self):
        self.running = False
        if self.capture is not None and self.capture.isOpened():
            self.capture.release()
        self.capture = None

    def _loop(self):
        while self.running:
            if self.capture is None or not self.capture.isOpened():
                self._open_camera()
                self._set_status_frame("Camara no disponible", "Reintentando conexion...")
                time.sleep(1)
                continue

            ok, frame = self.capture.read()
            if not ok:
                self._set_status_frame("Sin imagen de camara", "Verifica permisos o si otra app la usa")
                time.sleep(0.2)
                continue

            detections = []
            annotated = frame.copy()

            if self.model is not None:
                results = self.model.predict(
                    frame,
                    conf=settings.detection_confidence,
                    verbose=False,
                )
                annotated, detections = self._parse_results(frame, results)

            self.buffer.append(frame.copy())

            with self.lock:
                self.last_frame = annotated
                self.last_detections = detections

            suspicious = [item for item in detections if item["label"].lower() in settings.suspicious_labels]
            if suspicious and self._can_send_alert():
                self.last_alert_at = time.time()
                threading.Thread(
                    target=self._save_evidence,
                    args=(annotated.copy(), list(self.buffer), suspicious[0]),
                    daemon=True,
                ).start()

            time.sleep(0.03)

    def _open_camera(self):
        if self.capture is not None and self.capture.isOpened():
            return

        self.capture = cv2.VideoCapture(settings.camera_index, cv2.CAP_DSHOW)
        if self.capture.isOpened():
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    def _set_status_frame(self, title, detail):
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.putText(frame, title, (60, 320), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(frame, detail, (60, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (180, 180, 180), 2, cv2.LINE_AA)
        with self.lock:
            self.last_frame = frame

    def _parse_results(self, frame, results):
        annotated = frame.copy()
        detections = []

        for result in results:
            names = result.names
            for box in result.boxes:
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                label = names.get(class_id, str(class_id))
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append({"label": label, "confidence": confidence})

                color = (0, 0, 255) if label.lower() in settings.suspicious_labels else (0, 180, 0)
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    annotated,
                    f"{label} {confidence:.2f}",
                    (x1, max(25, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2,
                    cv2.LINE_AA,
                )

        return annotated, detections

    def _can_send_alert(self):
        return time.time() - self.last_alert_at >= settings.alert_cooldown_seconds

    def _save_evidence(self, frame, frames, detection):
        event_id = uuid4()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{timestamp}_{event_id}"
        image_path = self.evidence_dir / f"{base_name}.jpg"
        video_path = self.evidence_dir / f"{base_name}.mp4"

        cv2.imwrite(str(image_path), frame)
        self._write_video(video_path, frames)

        storage_image = f"eventos/{base_name}.jpg"
        storage_video = f"eventos/{base_name}.mp4"

        uploaded_image = upload_file(image_path, storage_image, "image/jpeg")
        uploaded_video = upload_file(video_path, storage_video, "video/mp4")

        label = detection["label"]
        confidence = detection["confidence"]
        risk = "ALTO" if label.lower() != "person" else "MEDIO"

        insert_event(
            tipo_evento=label,
            descripcion=f"Deteccion sospechosa: {label}",
            confianza=confidence,
            nivel_riesgo=risk,
            imagen_path=uploaded_image,
            video_path=uploaded_video,
        )

    def _write_video(self, video_path: Path, frames):
        if not frames:
            return

        height, width = frames[0].shape[:2]
        writer = cv2.VideoWriter(
            str(video_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            12,
            (width, height),
        )
        for frame in frames:
            writer.write(frame)
        writer.release()

    def stream(self):
        self.start()
        while True:
            with self.lock:
                frame = None if self.last_frame is None else self.last_frame.copy()

            if frame is None:
                time.sleep(0.1)
                continue

            ok, encoded = cv2.imencode(".jpg", frame)
            if not ok:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + encoded.tobytes()
                + b"\r\n"
            )

    def status(self):
        return {
            "camera_open": self.capture is not None and self.capture.isOpened(),
            "model_loaded": self.model is not None,
            "model_path": str(settings.model_path),
            "detections": self.last_detections,
        }
