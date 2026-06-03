import base64
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image, ImageOps
from ultralytics import YOLO

from app.config import settings
from app.labels import display_label, label_color


router = APIRouter(prefix="/test", tags=["test"])
_model = None
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".wmv", ".mpeg", ".mpg", ".3gp"}


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
    return annotated, detections


def _iou(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - inter_area
    return inter_area / union if union else 0


def _intersection_over_min_area(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    min_area = min(area_a, area_b)
    return inter_area / min_area if min_area else 0


def _same_object(box_a, box_b):
    return _iou(box_a, box_b) > 0.20 or _intersection_over_min_area(box_a, box_b) > 0.45


def _dedupe_detections(detections):
    ordered = sorted(detections, key=lambda item: item["confidence"], reverse=True)
    kept = []
    for detection in ordered:
        duplicate = any(
            detection["label"] == item["label"] and _same_object(detection["box"], item["box"])
            for item in kept
        )
        if not duplicate:
            kept.append(detection)
    return kept


def _draw_detections(frame, detections):
    annotated = frame.copy()
    for detection in detections:
        label = detection["label"]
        confidence = detection["confidence"]
        x1, y1, x2, y2 = detection["box"]
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


def _results_to_detections(results):
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
    return detections


def _predict_fast(frame):
    model = _get_model()
    results = model.predict(
        frame,
        conf=max(settings.test_detection_confidence, 0.08),
        iou=0.55,
        imgsz=min(settings.test_detection_imgsz, 960),
        max_det=settings.detection_max_det,
        agnostic_nms=False,
        augment=False,
        verbose=False,
    )
    return _dedupe_detections(_results_to_detections(results))


def _predict_test(frame, fast: bool = False):
    if fast:
        return _predict_fast(frame)

    model = _get_model()

    general_results = model.predict(
        frame,
        conf=settings.test_detection_confidence,
        iou=0.55,
        imgsz=settings.test_detection_imgsz,
        max_det=settings.detection_max_det,
        agnostic_nms=False,
        augment=False,
        verbose=False,
    )
    return _dedupe_detections(_results_to_detections(general_results))


def _read_image(data: bytes):
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if image is not None:
        return image

    try:
        from io import BytesIO

        with Image.open(BytesIO(data)) as pil_image:
            pil_image = ImageOps.exif_transpose(pil_image).convert("RGB")
            return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    except Exception:
        return None


def _convert_video_to_mp4(source_path: Path) -> Path | None:
    converted = source_path.with_suffix(".converted.mp4")
    try:
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(source_path),
                "-an",
                "-vf",
                "scale=1280:-2",
                "-vcodec",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(converted),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=120,
        )
        return converted if converted.exists() and converted.stat().st_size > 0 else None
    except Exception:
        converted.unlink(missing_ok=True)
        return None


@router.post("/model/image")
async def test_image(file: UploadFile = File(...), fast: bool = Form(False)):
    data = await file.read()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix and suffix not in IMAGE_SUFFIXES:
        raise HTTPException(status_code=415, detail=f"Formato de imagen no soportado: {suffix}")

    image = _read_image(data)
    if image is None:
        raise HTTPException(status_code=422, detail="No se pudo leer la imagen. Usa JPG, PNG, WEBP, BMP o TIFF.")

    detections = _predict_test(image, fast=fast)
    annotated = _draw_detections(image, detections)
    ok, encoded = cv2.imencode(".jpg", annotated)
    if not ok:
        raise HTTPException(status_code=500, detail="No se pudo generar la imagen anotada")

    counts = Counter(item["label"] for item in detections)
    return {
        "type": "image",
        "file_name": file.filename,
        "detections": detections,
        "summary": [{"label": label, "count": count} for label, count in counts.items()],
        "annotated_image": f"data:image/jpeg;base64,{base64.b64encode(encoded.tobytes()).decode('ascii')}",
    }


@router.post("/model/video")
async def test_video(file: UploadFile = File(...)):
    suffix = Path(file.filename or "video.mp4").suffix.lower() or ".mp4"
    if suffix not in VIDEO_SUFFIXES:
        raise HTTPException(status_code=415, detail=f"Formato de video no soportado: {suffix}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(await file.read())
        temp_path = Path(temp.name)

    capture = cv2.VideoCapture(str(temp_path))
    if not capture.isOpened():
        converted_path = _convert_video_to_mp4(temp_path)
        if converted_path is None:
            temp_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=422,
                detail="No se pudo leer el video. Prueba MP4 H.264, MOV, AVI, MKV o WEBM con codec compatible.",
            )
        capture = cv2.VideoCapture(str(converted_path))
    else:
        converted_path = None

    if not capture.isOpened():
        temp_path.unlink(missing_ok=True)
        if converted_path:
            converted_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="No se pudo abrir el video convertido.")

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
            detections = _predict_test(frame)
            annotated = _draw_detections(frame, detections)
            if preview is None:
                preview = annotated
            for detection in detections:
                all_detections.append({"frame": frame_index, **detection})
            processed += 1
        frame_index += 1

    capture.release()
    temp_path.unlink(missing_ok=True)
    if converted_path:
        converted_path.unlink(missing_ok=True)

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
