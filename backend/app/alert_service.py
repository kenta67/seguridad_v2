import tempfile
import threading
import time
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import cv2
import imageio_ffmpeg
from storage3.exceptions import StorageApiError
import logging

from app.config import settings
from app.labels import display_label, normalize_label, risk_level
from app.supabase_client import (
    create_signed_url,
    get_family_recipients,
    insert_event,
    is_event_attended,
    storage_public_url,
    upload_file,
)
from app.whatsapp_client import send_image, send_template, send_text, send_video, status as whatsapp_status


RED_OBJECTS = {"arma_de_fuego", "arma_blanca"}
YELLOW_OBJECTS = {"casco", "mascarilla", "pasamontana"}
logger = logging.getLogger("seguridad.alerts")


def classify_alert(detections: list[dict]) -> dict | None:
    labels = {normalize_label(item["label"]) for item in detections}
    has_person = "persona" in labels

    # Armas rojas → alerta roja inmediata (persona + arma, o solo arma si el
    # modelo no etiqueta a la persona por separado en ese frame)
    red_matches = sorted(labels & RED_OBJECTS)
    if red_matches and (has_person or red_matches):
        return {
            "level": "roja",
            "risk": "CRITICO",
            "objects": red_matches,
            "folder": "alerta_roja",
        }

    # Objetos amarillos → solo si hay persona detectada
    if not has_person:
        return None

    yellow_matches = sorted(labels & YELLOW_OBJECTS)
    if yellow_matches:
        highest_risk = "ALTO" if "pasamontana" in yellow_matches else "MEDIO"
        return {
            "level": "amarilla",
            "risk": highest_risk,
            "objects": yellow_matches,
            "folder": "alerta_amarilla",
        }

    return None


def _write_video(path: Path, frames: list, fps: int = 10) -> bool:
    if not frames:
        return False
    normalized_frames = []
    for frame in frames:
        height, width = frame.shape[:2]
        even_width = width - (width % 2)
        even_height = height - (height % 2)
        normalized_frames.append(frame[:even_height, :even_width])

    raw_path = path.with_suffix(".raw.avi")
    height, width = normalized_frames[0].shape[:2]
    writer = cv2.VideoWriter(
        str(raw_path),
        cv2.VideoWriter_fourcc(*"MJPG"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        return False

    for frame in normalized_frames:
        writer.write(frame)
    writer.release()

    if not raw_path.exists() or raw_path.stat().st_size == 0:
        _safe_unlink(raw_path)
        return False

    try:
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(raw_path),
                "-an",
                "-vcodec",
                "libx264",
                "-preset",
                "veryfast",
                "-movflags",
                "+faststart",
                "-pix_fmt",
                "yuv420p",
                str(path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=60,
        )
    except Exception:
        logger.exception("No se pudo convertir el clip de alerta a MP4 H.264")
        path.unlink(missing_ok=True)
    finally:
        _safe_unlink(raw_path)

    return path.exists() and path.stat().st_size > 0


def _safe_unlink(path: Path) -> None:
    for _ in range(5):
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError:
            time.sleep(0.1)


def _fallback_frames(frames: list, annotated_frame) -> list:
    if frames:
        return frames
    return [annotated_frame.copy() for _ in range(12)]


def _short_error_detail() -> str:
    last_error = whatsapp_status().get("last_error")
    if not last_error:
        return "Error desconocido enviando WhatsApp"
    detail = str(last_error.get("detail") or last_error)
    return detail[:500]


class AlertService:
    def __init__(self):
        self.last_alert_at = 0.0
        self.last_status = {
            "state": "idle",
            "message": "Sin alertas procesadas",
            "event_id": None,
            "level": None,
        }

    def can_emit(self) -> bool:
        return time.time() - self.last_alert_at >= settings.alert_cooldown_seconds

    def handle(self, alert: dict, annotated_frame, frames: list, detections: list[dict]) -> None:
        if not settings.alerts_enabled or not self.can_emit():
            return
        self.last_alert_at = time.time()
        self.last_status = {
            "state": "queued",
            "message": f"Procesando alerta {alert['level']}",
            "event_id": None,
            "level": alert["level"],
        }
        thread = threading.Thread(
            target=self._process_alert_safely,
            args=(alert, annotated_frame.copy(), list(frames), list(detections)),
            daemon=True,
        )
        thread.start()

    def _process_alert_safely(self, alert: dict, annotated_frame, frames: list, detections: list[dict]) -> None:
        try:
            self._process_alert(alert, annotated_frame, frames, detections)
        except Exception:
            logger.exception("No se pudo procesar la alerta")
            self.last_status = {
                "state": "error",
                "message": "Error procesando alerta; revisa el log del backend",
                "event_id": None,
                "level": alert.get("level"),
            }

    def _process_alert(self, alert: dict, annotated_frame, frames: list, detections: list[dict]) -> None:
        event_uuid = uuid4()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{timestamp}_{event_uuid}"
        folder = alert["folder"]

        uploaded_image = None
        uploaded_video = None
        try:
            settings.alert_temp_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(
                prefix="seguridad_alerta_",
                dir=settings.alert_temp_dir,
                ignore_cleanup_errors=True,
            ) as temp_dir:
                temp_path = Path(temp_dir)
                image_path = temp_path / f"{base_name}.jpg"
                video_path = temp_path / f"{base_name}.mp4"
                image_ok = cv2.imwrite(str(image_path), annotated_frame)
                clip_frames = _fallback_frames(
                    frames[-max(1, settings.video_seconds * 10):],
                    annotated_frame,
                )
                video_ok = _write_video(video_path, clip_frames)
                if not image_ok or not image_path.exists():
                    raise RuntimeError(f"No se pudo escribir la imagen temporal: {image_path}")

                storage_image = f"{folder}/{base_name}.jpg"
                storage_video = f"{folder}/{base_name}.mp4"
                uploaded_image = upload_file(image_path, storage_image, "image/jpeg")
                if video_ok:
                    uploaded_video = upload_file(video_path, storage_video, "video/mp4")
                else:
                    logger.warning("No se subio video para la alerta porque el MP4 no se genero correctamente")
        except StorageApiError:
            logger.exception("No se pudo subir evidencia a Supabase Storage")

        public_image_url = storage_public_url(uploaded_image)
        public_video_url = storage_public_url(uploaded_video)
        event_id = insert_event(
            tipo_evento=",".join(alert["objects"]),
            descripcion=self._description(alert, detections),
            confianza=max((item["confidence"] for item in detections), default=0),
            nivel_riesgo=alert["risk"],
            imagen_url=public_image_url,
            video_url=public_video_url,
        )
        logger.info("Evento generado: id=%s nivel=%s imagen=%s video=%s", event_id, alert["level"], public_image_url, public_video_url)

        image_url = create_signed_url(uploaded_image, 3600) or public_image_url
        video_url = create_signed_url(uploaded_video, 3600) or public_video_url
        recipients = get_family_recipients()
        message = self._message(alert, event_id)
        notify_result = self._notify_once_v2(recipients, message, image_url, video_url, alert_level=alert["level"])
        self.last_status = {
            "state": "sent",
            "message": (
                f"Alerta {alert['level']} registrada. "
                f"WhatsApp enviados: {notify_result['sent']}, fallidos: {notify_result['failed']}"
            ),
            "event_id": event_id,
            "level": alert["level"],
            "image_path": uploaded_image,
            "video_path": uploaded_video,
            "recipients": len(recipients),
            "whatsapp": notify_result,
            "whatsapp_last_error": whatsapp_status().get("last_error"),
        }

        if alert["level"] == "roja" and event_id and notify_result["sent"] > 0:
            self._repeat_until_attended(event_id, recipients, message, image_url, video_url)

    def _notify_once_v2(
        self,
        recipients: list[dict],
        message: str,
        image_url: str | None,
        video_url: str | None,
        alert_level: str = "",
    ) -> dict:
        result = {"sent": 0, "failed": 0, "errors": []}
        is_red = alert_level == "roja"
        img_caption = (
            "Foto de la alerta ROJA - posible amenaza critica"
            if is_red
            else "Foto de la alerta amarilla - actividad sospechosa"
        )
        vid_caption = (
            "Video del evento ROJO - revisa de inmediato"
            if is_red
            else "Video del evento amarillo - actividad detectada"
        )
        for recipient in recipients:
            number = recipient.get("numero")
            if not number:
                continue
            try:
                sent_any = False
                if settings.whatsapp_send_template_first:
                    template_params = [message] if settings.whatsapp_template_body_params else None
                    sent_any = send_template(number, body_parameters=template_params)
                try:
                    sent_any = send_text(number, message) or sent_any
                except Exception:
                    logger.exception("No se pudo enviar texto libre por WhatsApp al usuario %s", recipient.get("id"))
                if image_url:
                    try:
                        sent_any = send_image(number, image_url, img_caption) or sent_any
                    except Exception:
                        logger.exception("No se pudo enviar imagen por WhatsApp al usuario %s", recipient.get("id"))
                if video_url:
                    try:
                        sent_any = send_video(number, video_url, vid_caption) or sent_any
                    except Exception:
                        logger.exception("No se pudo enviar video por WhatsApp al usuario %s", recipient.get("id"))
                if sent_any:
                    result["sent"] += 1
                else:
                    result["failed"] += 1
            except Exception:
                result["failed"] += 1
                result["errors"].append(
                    {
                        "recipient_id": recipient.get("id"),
                        "number": number,
                        "error": str(_short_error_detail()),
                    }
                )
                logger.exception("No se pudo enviar WhatsApp al usuario %s", recipient.get("id"))
                continue
        return result

    def _notify_once(
        self,
        recipients: list[dict],
        message: str,
        image_url: str | None,
        video_url: str | None,
        alert_level: str = "",
    ) -> dict:
        result = {"sent": 0, "failed": 0, "errors": []}
        is_red = alert_level == "roja"
        img_caption = (
            "📸 Foto de la alerta ROJA — posible amenaza critica"
            if is_red
            else "📸 Foto de la alerta amarilla — actividad sospechosa"
        )
        vid_caption = (
            "🎥 Video del evento ROJO — revisa de inmediato"
            if is_red
            else "🎥 Video del evento amarillo — actividad detectada"
        )
        for recipient in recipients:
            number = recipient.get("numero")
            if not number:
                continue
            try:
                sent_any = False
                if settings.whatsapp_send_template_first:
                    sent_any = send_template(number)
                try:
                    sent_any = send_text(number, message) or sent_any
                except Exception:
                    logger.exception("No se pudo enviar texto libre por WhatsApp al usuario %s", recipient.get("id"))
                if image_url:
                    try:
                        sent_any = send_image(number, image_url, img_caption) or sent_any
                    except Exception:
                        logger.exception("No se pudo enviar imagen por WhatsApp al usuario %s", recipient.get("id"))
                if video_url:
                    try:
                        sent_any = send_video(number, video_url, vid_caption) or sent_any
                    except Exception:
                        logger.exception("No se pudo enviar video por WhatsApp al usuario %s", recipient.get("id"))
                if sent_any:
                    result["sent"] += 1
                else:
                    result["failed"] += 1
            except Exception:
                result["failed"] += 1
                result["errors"].append(
                    {
                        "recipient_id": recipient.get("id"),
                        "number": number,
                        "error": str(_short_error_detail()),
                    }
                )
                logger.exception("No se pudo enviar WhatsApp al usuario %s", recipient.get("id"))
                continue
        return result

    def _repeat_until_attended(
        self,
        event_id: str,
        recipients: list[dict],
        message: str,
        image_url: str | None,
        video_url: str | None,
    ) -> None:
        for _ in range(settings.red_alert_max_repeats):
            time.sleep(settings.red_alert_repeat_seconds)
            if is_event_attended(event_id):
                return
            self._notify_once_v2(recipients, f"RECORDATORIO: {message}", image_url, video_url, alert_level="roja")

    def _description(self, alert: dict, detections: list[dict]) -> str:
        counts = Counter(display_label(item["label"]) for item in detections)
        found = ", ".join(f"{label}: {count}" for label, count in counts.items())
        return f"Alerta {alert['level'].upper()} detectada. Objetos detectados: {found}"

    def _message(self, alert: dict, event_id: str | None) -> str:
        objects_list = alert["objects"]
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        if alert["level"] == "roja":
            # Diferenciar arma de fuego vs arma blanca
            descriptions = []
            for obj in objects_list:
                if obj == "arma_de_fuego":
                    descriptions.append("un arma de fuego (pistola/revolver)")
                elif obj == "arma_blanca":
                    descriptions.append("un arma blanca (cuchillo/navaja/machete)")
                else:
                    descriptions.append(display_label(obj))
            what = " y ".join(descriptions)
            body = (
                f"🔴 *ALERTA ROJA — PELIGRO CRITICO* 🔴\n\n"
                f"Se detecto una persona manipulando {what}.\n\n"
                f"📍 Fecha y hora: {now}\n"
                f"⚠️ Nivel de riesgo: CRITICO\n\n"
                f"Se adjunta foto y video del momento."
            )
        else:
            # Diferenciar cada objeto amarillo
            descriptions = []
            for obj in objects_list:
                if obj == "pasamontana":
                    descriptions.append("un pasamontanas (cubriendo el rostro)")
                elif obj == "mascarilla":
                    descriptions.append("una mascarilla sospechosa")
                elif obj == "casco":
                    descriptions.append("un casco")
                else:
                    descriptions.append(display_label(obj))
            what = " y ".join(descriptions)
            risk = alert.get("risk", "MEDIO")
            body = (
                f"🟡 *ALERTA AMARILLA — Actividad Sospechosa* 🟡\n\n"
                f"Se detecto una persona portando {what}.\n\n"
                f"📍 Fecha y hora: {now}\n"
                f"⚠️ Nivel de riesgo: {risk}\n\n"
                f"Se adjunta foto y video del momento."
            )

        suffix = f"\n🆔 ID de evento: {event_id}" if event_id else ""
        return f"{body}{suffix}"
