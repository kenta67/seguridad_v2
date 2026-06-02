import requests
import logging
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger("seguridad.whatsapp")
LAST_ERROR: dict | None = None


@dataclass
class WhatsAppApiError(Exception):
    status_code: int
    detail: str

    def __str__(self) -> str:
        return self.detail


def _normalize_phone(number: str) -> str:
    phone = "".join(ch for ch in number if ch.isdigit())
    if len(phone) == 8 and settings.whatsapp_default_country_code:
        return f"{settings.whatsapp_default_country_code}{phone}"
    return phone


def _valid_config() -> bool:
    global LAST_ERROR
    if not settings.whatsapp_enabled:
        LAST_ERROR = {"type": "config", "detail": "WHATSAPP_ENABLED=false"}
        return False
    if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
        detail = "WhatsApp esta habilitado, pero falta token o phone_number_id"
        LAST_ERROR = {"type": "config", "detail": detail}
        logger.warning(detail)
        return False
    if not settings.whatsapp_phone_number_id.isdigit():
        detail = "WHATSAPP_PHONE_NUMBER_ID debe contener un solo ID numerico"
        LAST_ERROR = {"type": "config", "detail": detail}
        logger.warning(detail)
        return False
    return True


def _post_message(payload: dict) -> bool:
    global LAST_ERROR
    if not _valid_config():
        return False

    url = (
        f"https://graph.facebook.com/{settings.whatsapp_graph_version}/"
        f"{settings.whatsapp_phone_number_id}/messages"
    )
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {settings.whatsapp_access_token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    if response.status_code >= 400:
        LAST_ERROR = {
            "type": "meta",
            "status_code": response.status_code,
            "detail": response.text,
            "to": payload.get("to"),
            "message_type": payload.get("type"),
        }
        logger.error("Meta WhatsApp rechazo el mensaje: %s", response.text)
        raise WhatsAppApiError(response.status_code, response.text)
    LAST_ERROR = None
    return True


def send_text(to_number: str, body: str) -> bool:
    phone = _normalize_phone(to_number)
    if not phone:
        return False
    return _post_message(
        {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"preview_url": True, "body": body},
        }
    )


def send_template(
    to_number: str,
    template_name: str | None = None,
    language_code: str | None = None,
    body_parameters: list[str] | None = None,
) -> bool:
    phone = _normalize_phone(to_number)
    if not phone:
        return False
    template = {
        "name": template_name or settings.whatsapp_template_name,
        "language": {"code": language_code or settings.whatsapp_template_language},
    }
    if body_parameters:
        template["components"] = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": str(parameter)[:1024]}
                    for parameter in body_parameters
                ],
            }
        ]
    return _post_message(
        {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": template,
        }
    )


def send_image(to_number: str, image_url: str, caption: str) -> bool:
    phone = _normalize_phone(to_number)
    if not phone or not image_url:
        return False
    return _post_message(
        {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "image",
            "image": {"link": image_url, "caption": caption},
        }
    )


def send_video(to_number: str, video_url: str, caption: str) -> bool:
    phone = _normalize_phone(to_number)
    if not phone or not video_url:
        return False
    return _post_message(
        {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "video",
            "video": {"link": video_url, "caption": caption},
        }
    )


def status() -> dict:
    return {
        "enabled": settings.whatsapp_enabled,
        "has_token": bool(settings.whatsapp_access_token),
        "phone_number_id": settings.whatsapp_phone_number_id,
        "phone_number_id_valid": settings.whatsapp_phone_number_id.isdigit(),
        "graph_version": settings.whatsapp_graph_version,
        "default_country_code": settings.whatsapp_default_country_code,
        "send_template_first": settings.whatsapp_send_template_first,
        "template_name": settings.whatsapp_template_name,
        "template_language": settings.whatsapp_template_language,
        "template_body_params": settings.whatsapp_template_body_params,
        "last_error": LAST_ERROR,
    }
