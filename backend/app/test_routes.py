import base64
import tempfile
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from ultralytics import YOLO

from app.config import settings


router = APIRouter(prefix="/test", tags=["test"])
_model = None


def _get_model():
    global _model
    if _model is None:
        if not settings.model_path.exists():
            raise HTTPException(status_code=404, detail=f"Modelo no encontrado: {settings.model_path}")
        _model = YOLO(str(settings.model_path))
    return _model


def _parse_results(frame, results):
    annotated = frame.copy()
    detections = []
    for result in results:
        names = result.names
        for box in result.boxes:
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            label = names.get(class_id, str(class_id))
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            detections.append(
                {
                    "label": label,
                    "confidence": round(confidence, 4),
                    "box": [x1, y1, x2, y2],
                }
            )
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


@router.post("/model/image")
async def test_image(file: UploadFile = File(...)):
    data = await file.read()
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=422, detail="No se pudo leer la imagen")

    results = _get_model().predict(image, conf=settings.detection_confidence, verbose=False)
    annotated, detections = _parse_results(image, results)
    ok, encoded = cv2.imencode(".jpg", annotated)
    if not ok:
        raise HTTPException(status_code=500, detail="No se pudo generar la imagen anotada")

    return {
        "type": "image",
        "file_name": file.filename,
        "detections": detections,
        "annotated_image": f"data:image/jpeg;base64,{base64.b64encode(encoded.tobytes()).decode('ascii')}",
    }


@router.post("/model/video")
async def test_video(file: UploadFile = File(...)):
    suffix = Path(file.filename or "video.mp4").suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(await file.read())
        temp_path = Path(temp.name)

    capture = cv2.VideoCapture(str(temp_path))
    if not capture.isOpened():
        temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="No se pudo leer el video")

    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    step = max(1, frame_count // 40) if frame_count else 15
    frame_index = 0
    processed = 0
    all_detections = []
    preview = None

    while processed < 40:
        ok, frame = capture.read()
        if not ok:
            break
        if frame_index % step == 0:
            results = _get_model().predict(frame, conf=settings.detection_confidence, verbose=False)
            annotated, detections = _parse_results(frame, results)
            if preview is None:
                preview = annotated
            for detection in detections:
                all_detections.append({"frame": frame_index, **detection})
            processed += 1
        frame_index += 1

    capture.release()
    temp_path.unlink(missing_ok=True)

    preview_image = None
    if preview is not None:
        ok, encoded = cv2.imencode(".jpg", preview)
        if ok:
            preview_image = f"data:image/jpeg;base64,{base64.b64encode(encoded.tobytes()).decode('ascii')}"

    counts = Counter(item["label"] for item in all_detections)
    return {
        "type": "video",
        "file_name": file.filename,
        "frames_processed": processed,
        "detections": all_detections[:200],
        "summary": [{"label": label, "count": count} for label, count in counts.items()],
        "preview_image": preview_image,
    }
