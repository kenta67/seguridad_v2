import logging
from dataclasses import dataclass
from html import escape

import requests

from app.config import settings


logger = logging.getLogger("seguridad.telegram")
LAST_ERROR: dict | None = None
BOT_INFO: dict | None = None


def _has_real_token() -> bool:
    token = settings.telegram_bot_token.strip()
    return bool(token) and "TU_TOKEN" not in token


@dataclass
class TelegramApiError(Exception):
    status_code: int
    detail: str

    def __str__(self) -> str:
        return self.detail


def _valid_config() -> bool:
    global LAST_ERROR
    if not settings.telegram_enabled:
        LAST_ERROR = {"type": "config", "detail": "TELEGRAM_ENABLED=false"}
        return False
    if not _has_real_token():
        LAST_ERROR = {"type": "config", "detail": "Falta TELEGRAM_BOT_TOKEN"}
        return False
    return True


def _api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"


def _post(method: str, data: dict | None = None, files: dict | None = None) -> bool:
    global LAST_ERROR
    if not _valid_config():
        return False

    response = requests.post(
        _api_url(method),
        data=data or {},
        files=files,
        timeout=60,
    )
    if response.status_code >= 400:
        LAST_ERROR = {
            "type": "telegram",
            "status_code": response.status_code,
            "detail": response.text,
            "method": method,
            "chat_id": (data or {}).get("chat_id"),
        }
        logger.error("Telegram rechazo la solicitud: %s", response.text)
        raise TelegramApiError(response.status_code, response.text)

    payload = response.json()
    if not payload.get("ok"):
        LAST_ERROR = {
            "type": "telegram",
            "status_code": response.status_code,
            "detail": response.text,
            "method": method,
            "chat_id": (data or {}).get("chat_id"),
        }
        raise TelegramApiError(response.status_code, response.text)

    LAST_ERROR = None
    return True


def send_text(chat_id: str, text: str) -> bool:
    if not chat_id:
        return False
    return _post(
        "sendMessage",
        data={
            "chat_id": str(chat_id),
            "text": text,
            "parse_mode": settings.telegram_parse_mode,
            "disable_web_page_preview": "false",
        },
    )


def send_photo(chat_id: str, image_url: str | None, caption: str = "") -> bool:
    if not chat_id or not image_url:
        return False
    return _post(
        "sendPhoto",
        data={
            "chat_id": str(chat_id),
            "photo": image_url,
            "caption": caption[:1024],
            "parse_mode": settings.telegram_parse_mode,
        },
    )


def send_video(chat_id: str, video_url: str | None, caption: str = "") -> bool:
    if not chat_id or not video_url:
        return False
    return _post(
        "sendVideo",
        data={
            "chat_id": str(chat_id),
            "video": video_url,
            "caption": caption[:1024],
            "parse_mode": settings.telegram_parse_mode,
            "supports_streaming": "true",
        },
    )


def get_updates() -> list[dict]:
    if not _valid_config():
        return []
    response = requests.get(_api_url("getUpdates"), timeout=15)
    if response.status_code >= 400:
        raise TelegramApiError(response.status_code, response.text)
    payload = response.json()
    return payload.get("result", []) if payload.get("ok") else []


def get_me() -> dict:
    global BOT_INFO
    if BOT_INFO:
        return BOT_INFO
    if not _valid_config():
        return {}
    response = requests.get(_api_url("getMe"), timeout=15)
    if response.status_code >= 400:
        raise TelegramApiError(response.status_code, response.text)
    payload = response.json()
    BOT_INFO = payload.get("result", {}) if payload.get("ok") else {}
    return BOT_INFO


def bot_username() -> str | None:
    if settings.telegram_bot_username:
        return settings.telegram_bot_username.removeprefix("@")
    try:
        return get_me().get("username")
    except Exception:
        logger.exception("No se pudo obtener el username del bot")
        return None


def status() -> dict:
    return {
        "enabled": settings.telegram_enabled,
        "has_token": _has_real_token(),
        "parse_mode": settings.telegram_parse_mode,
        "bot_username": bot_username() if _has_real_token() else None,
        "last_error": LAST_ERROR,
    }


def format_alert_message(message: str, image_url: str | None = None, video_url: str | None = None) -> str:
    parts = [escape(message)]
    if image_url:
        parts.append(f'<a href="{escape(image_url)}">Abrir imagen</a>')
    if video_url:
        parts.append(f'<a href="{escape(video_url)}">Abrir video</a>')
    return "\n\n".join(parts)
