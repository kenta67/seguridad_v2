import threading
import time
import os
from collections import deque
import cv2
import numpy as np

from app.config import settings

settings.alert_temp_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(settings.alert_temp_dir / "ultralytics"))

from ultralytics import YOLO

from app.alert_service import AlertService, classify_alert
from app.labels import display_label, label_color, normalize_label


class CameraDetector:
    def __init__(self):
        self.capture = None
        self.model = YOLO(str(settings.model_path)) if settings.model_path.exists() else None
        self.lock = threading.Lock()
        self.last_frame = None
        self.last_detections = []
        self.last_boxes = []
        self.last_alert_at = 0.0
        self.frame_index = 0
        self.running = False
        self.frame_buffer = deque(maxlen=max(30, settings.video_seconds * 15))
        self.detection_history = deque(maxlen=12)
        self.alert_service = AlertService()

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
            boxes = self.last_boxes

            should_detect = self.model is not None and self.frame_index % max(1, settings.detection_frame_skip) == 0
            if should_detect:
                results = self.model.predict(
                    frame,
                    conf=settings.detection_confidence,
                    iou=settings.detection_iou,
                    max_det=settings.detection_max_det,
                    agnostic_nms=False,
                    verbose=False,
                )
                detections, boxes = self._parse_results(results)
                self.last_boxes = boxes
                self.detection_history.append(detections)
            else:
                detections = self.last_detections

            annotated = self._draw_boxes(frame, boxes)
            self.frame_buffer.append(annotated.copy())
            alert_detections = self._recent_detections()

            with self.lock:
                self.last_frame = annotated
                self.last_detections = detections

            alert = classify_alert(alert_detections)
            if alert:
                self.alert_service.handle(alert, annotated, list(self.frame_buffer), alert_detections)

            self.frame_index += 1
            time.sleep(0.01)

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

    def _parse_results(self, results):
        detections = []
        boxes = []

        for result in results:
            names = result.names
            for box in result.boxes:
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                label = names.get(class_id, str(class_id))
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append({"label": label, "confidence": confidence})
                boxes.append(
                    {
                        "label": label,
                        "confidence": confidence,
                        "xyxy": (x1, y1, x2, y2),
                    }
                )

        return detections, boxes

    def _recent_detections(self):
        best_by_label = {}
        for detections in self.detection_history:
            for item in detections:
                label = normalize_label(item["label"])
                current = best_by_label.get(label)
                if current is None or item["confidence"] > current["confidence"]:
                    best_by_label[label] = {
                        "label": label,
                        "confidence": item["confidence"],
                    }
        return list(best_by_label.values())

    def _draw_boxes(self, frame, boxes):
        annotated = frame.copy()
        for item in boxes:
            label = item["label"]
            confidence = item["confidence"]
            x1, y1, x2, y2 = item["xyxy"]
            color = label_color(label)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                annotated,
                f"{display_label(label)} {confidence:.2f}",
                (x1, max(25, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2,
                cv2.LINE_AA,
            )
        return annotated

    def stream(self):
        self.start()
        try:
            while True:
                jpeg = self.frame_jpeg()
                if jpeg is None:
                    time.sleep(0.1)
                    continue

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + jpeg
                    + b"\r\n"
                )
                time.sleep(0.12)
        except GeneratorExit:
            return

    def frame_jpeg(self):
        self.start()
        with self.lock:
            frame = None if self.last_frame is None else self.last_frame.copy()

        if frame is None:
            self._set_status_frame("Iniciando camara", "Esperando primer frame...")
            with self.lock:
                frame = self.last_frame.copy()

        ok, encoded = cv2.imencode(".jpg", frame)
        if not ok:
            return None
        return encoded.tobytes()

    def status(self):
        recent_detections = self._recent_detections()
        return {
            "camera_open": self.capture is not None and self.capture.isOpened(),
            "model_loaded": self.model is not None,
            "model_path": str(settings.model_path),
            "storage_enabled": settings.alerts_enabled,
            "detections": self.last_detections,
            "recent_detections": recent_detections,
            "current_alert": classify_alert(recent_detections),
            "alert_status": self.alert_service.last_status,
        }
