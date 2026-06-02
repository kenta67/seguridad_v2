import hashlib
import tempfile
from typing import Any
from pathlib import Path
from uuid import uuid4

import requests
from fastapi import APIRouter, File, Header, HTTPException, Request, UploadFile
from pydantic import BaseModel

from app.config import settings
from app.supabase_client import get_family_recipients, list_events, storage_public_url, upload_file
from app.telegram_client import bot_username, get_updates, send_text, status as telegram_status


router = APIRouter(prefix="/admin", tags=["admin"])


class UserCreate(BaseModel):
    nombres: str
    apellidos: str
    email: str
    usuario: str
    password: str
    rol: str
    numero: str | None = None
    telegram_chat_id: str | None = None
    activo: bool = True


class UserUpdate(BaseModel):
    nombres: str
    apellidos: str
    usuario: str
    rol: str
    numero: str | None = None
    telegram_chat_id: str | None = None
    activo: bool = True


class ProfileUpdate(BaseModel):
    nombres: str
    apellidos: str
    usuario: str
    numero: str | None = None


class TelegramTest(BaseModel):
    chat_id: str | None = None
    mensaje: str = "Prueba de Telegram desde Seguridad V2"


class ConfigUpdate(BaseModel):
    deteccion_personas: bool = True
    deteccion_armas: bool = True
    deteccion_armas_blancas: bool = True
    deteccion_rostro_cubierto: bool = True
    grabacion_automatica: bool = True
    notificaciones_push: bool = True


DEFAULT_CONFIG = {
    "deteccion_personas": True,
    "deteccion_armas": True,
    "deteccion_armas_blancas": True,
    "deteccion_rostro_cubierto": True,
    "grabacion_automatica": True,
    "notificaciones_push": True,
}


def _headers() -> dict[str, str]:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(status_code=503, detail="Supabase backend no configurado")
    return {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
    }


def _request(method: str, path: str, **kwargs: Any) -> Any:
    response = requests.request(
        method,
        f"{settings.supabase_url}{path}",
        headers=_headers() | kwargs.pop("headers", {}),
        timeout=30,
        **kwargs,
    )
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json() if response.text else None


def _get_auth_user(authorization: str | None) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sesion requerida")

    token = authorization.removeprefix("Bearer ").strip()
    auth_response = requests.get(
        f"{settings.supabase_url}/auth/v1/user",
        headers={"apikey": settings.supabase_service_role_key, "Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if auth_response.status_code >= 400:
        raise HTTPException(status_code=401, detail="Sesion invalida")
    return auth_response.json()


def _require_parent(authorization: str | None) -> dict[str, Any]:
    auth_user = _get_auth_user(authorization)

    user_id = auth_user["id"]
    metadata_role = (auth_user.get("user_metadata") or {}).get("rol")
    profile = _request(
        "GET",
        f"/rest/v1/perfiles_usuarios?id=eq.{user_id}&select=id,rol&limit=1",
    )
    profile_role = profile[0]["rol"] if profile else None
    role = str(profile_role or metadata_role or "").strip().upper()
    if role != "PADRES":
        raise HTTPException(status_code=403, detail="Solo un padre puede administrar usuarios")
    return auth_user


def _require_session(authorization: str | None) -> dict[str, Any]:
    return _get_auth_user(authorization)


def _get_or_create_config(user_id: str) -> dict[str, Any]:
    rows = _request(
        "GET",
        f"/rest/v1/configuraciones?usuarios_id=eq.{user_id}&select=*&limit=1",
    )
    if rows:
        return rows[0]

    payload = {"usuarios_id": user_id, **DEFAULT_CONFIG}
    created = _request(
        "POST",
        "/rest/v1/configuraciones",
        headers={"Prefer": "return=representation"},
        json=payload,
    )
    if isinstance(created, list) and created:
        return created[0]
    return payload


def _client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else None


def _write_log(
    usuario_id: str | None,
    accion: str,
    descripcion: str,
    resultado: str,
    request: Request,
) -> None:
    try:
        _request(
            "POST",
            "/rest/v1/logs_sistema",
            json={
                "usuario_id": usuario_id,
                "accion": accion,
                "descripcion": descripcion,
                "ip_address": _client_ip(request),
                "user_agent": request.headers.get("user-agent"),
                "resultado": resultado,
            },
        )
    except Exception:
        pass


def _with_profile_names(logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    user_ids = sorted({item.get("usuario_id") for item in logs if item.get("usuario_id")})
    if not user_ids:
        return logs

    profiles = _request(
        "GET",
        f"/rest/v1/perfiles_usuarios?id=in.({','.join(user_ids)})&select=id,nombres,apellidos,usuario,rol",
    )
    by_id = {item["id"]: item for item in profiles or []}
    for item in logs:
        item["usuario"] = by_id.get(item.get("usuario_id"))
    return logs


def _telegram_payload(user_id: str) -> str:
    return f"u_{user_id.replace('-', '')}"


@router.get("/profile")
def get_profile(authorization: str | None = Header(default=None)):
    auth_user = _require_session(authorization)
    rows = _request(
        "GET",
        (
            f"/rest/v1/perfiles_usuarios?id=eq.{auth_user['id']}"
            "&select=id,nombres,apellidos,email,usuario,numero,telegram_chat_id,foto_perfil_url,rol,activo,ultimo_login,created_at"
            "&limit=1"
        ),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return rows[0]


@router.put("/profile")
def update_profile(payload: ProfileUpdate, request: Request, authorization: str | None = Header(default=None)):
    auth_user = _require_session(authorization)
    updated = _request(
        "PATCH",
        (
            f"/rest/v1/perfiles_usuarios?id=eq.{auth_user['id']}"
            "&select=id,nombres,apellidos,email,usuario,numero,telegram_chat_id,foto_perfil_url,rol,activo,ultimo_login,created_at"
        ),
        headers={"Prefer": "return=representation"},
        json=payload.model_dump(),
    )
    _write_log(
        auth_user["id"],
        "PERFIL_ACTUALIZADO",
        "El usuario actualizo sus datos de perfil",
        "OK",
        request,
    )
    return updated[0] if isinstance(updated, list) and updated else {"ok": True}


@router.post("/profile/photo")
async def update_profile_photo(
    request: Request,
    file: UploadFile = File(...),
    authorization: str | None = Header(default=None),
):
    auth_user = _require_session(authorization)
    suffix = Path(file.filename or "").suffix.lower()
    allowed = {".jpg", ".jpeg", ".png", ".webp"}
    if suffix not in allowed:
        raise HTTPException(status_code=415, detail="Formato no soportado. Usa JPG, PNG o WEBP.")

    content_type = file.content_type or "image/jpeg"
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="El archivo debe ser una imagen.")

    settings.alert_temp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=settings.alert_temp_dir) as temp:
        temp.write(await file.read())
        temp_path = Path(temp.name)

    try:
        storage_path = f"imagen_perfil/{auth_user['id']}/{uuid4()}{suffix}"
        uploaded_path = upload_file(temp_path, storage_path, content_type)
        public_url = storage_public_url(uploaded_path)
    finally:
        temp_path.unlink(missing_ok=True)

    updated = _request(
        "PATCH",
        (
            f"/rest/v1/perfiles_usuarios?id=eq.{auth_user['id']}"
            "&select=id,nombres,apellidos,email,usuario,numero,telegram_chat_id,foto_perfil_url,rol,activo,ultimo_login,created_at"
        ),
        headers={"Prefer": "return=representation"},
        json={"foto_perfil_url": public_url},
    )
    _write_log(
        auth_user["id"],
        "FOTO_PERFIL_ACTUALIZADA",
        "El usuario actualizo su imagen de perfil",
        "OK",
        request,
    )
    if isinstance(updated, list) and updated:
        return updated[0]
    return {"foto_perfil_url": public_url}


@router.post("/profile/telegram/link/start")
def start_profile_telegram_link(authorization: str | None = Header(default=None)):
    auth_user = _require_session(authorization)
    username = bot_username()
    if not username:
        raise HTTPException(status_code=503, detail="No se pudo obtener el usuario del bot de Telegram")

    rows = _request(
        "GET",
        f"/rest/v1/perfiles_usuarios?id=eq.{auth_user['id']}&select=id,telegram_chat_id&limit=1",
    )
    payload = _telegram_payload(auth_user["id"])
    current_chat_id = rows[0].get("telegram_chat_id") if rows else None
    return {
        "url": f"https://t.me/{username}?start={payload}",
        "payload": payload,
        "already_linked": bool(current_chat_id),
        "telegram_chat_id": current_chat_id,
    }


@router.post("/profile/telegram/link/sync")
def sync_profile_telegram_link(request: Request, authorization: str | None = Header(default=None)):
    auth_user = _require_session(authorization)
    payload = _telegram_payload(auth_user["id"])
    updates = get_updates()
    for update in reversed(updates):
        message = update.get("message") or update.get("edited_message") or {}
        text = (message.get("text") or "").strip()
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        if not chat_id:
            continue
        if text == f"/start {payload}" or text.endswith(f" {payload}"):
            data = {"telegram_chat_id": str(chat_id)}
            updated = _request(
                "PATCH",
                (
                    f"/rest/v1/perfiles_usuarios?id=eq.{auth_user['id']}"
                    "&select=id,nombres,apellidos,email,usuario,numero,telegram_chat_id,foto_perfil_url,rol,activo,ultimo_login,created_at"
                ),
                headers={"Prefer": "return=representation"},
                json=data,
            )
            _write_log(
                auth_user["id"],
                "TELEGRAM_PERFIL_VINCULADO",
                f"El usuario vinculo su Telegram Chat ID {chat_id}",
                "OK",
                request,
            )
            return {
                "linked": True,
                "telegram_chat_id": str(chat_id),
                "profile": updated[0] if isinstance(updated, list) and updated else data,
            }

    rows = _request(
        "GET",
        f"/rest/v1/perfiles_usuarios?id=eq.{auth_user['id']}&select=id,telegram_chat_id&limit=1",
    )
    current_chat_id = rows[0].get("telegram_chat_id") if rows else None
    return {"linked": bool(current_chat_id), "telegram_chat_id": current_chat_id}


@router.get("/users")
def list_users(authorization: str | None = Header(default=None)):
    _require_parent(authorization)
    return _request(
        "GET",
        "/rest/v1/perfiles_usuarios?select=*&order=created_at.desc",
    )


@router.get("/events")
def get_events(authorization: str | None = Header(default=None)):
    _require_session(authorization)
    return list_events()


@router.get("/logs")
def list_logs(authorization: str | None = Header(default=None)):
    _require_parent(authorization)
    logs = _request(
        "GET",
        "/rest/v1/logs_sistema?select=*&order=created_at.desc&limit=150",
    )
    return _with_profile_names(logs or [])


@router.get("/config")
def get_config(authorization: str | None = Header(default=None)):
    auth_user = _require_session(authorization)
    return _get_or_create_config(auth_user["id"])


@router.put("/config")
def update_config(payload: ConfigUpdate, request: Request, authorization: str | None = Header(default=None)):
    auth_user = _require_parent(authorization)
    _get_or_create_config(auth_user["id"])
    updated = _request(
        "PATCH",
        f"/rest/v1/configuraciones?usuarios_id=eq.{auth_user['id']}",
        headers={"Prefer": "return=representation"},
        json=payload.model_dump(),
    )
    _write_log(
        auth_user["id"],
        "CONFIGURACION_ACTUALIZADA",
        "Se actualizaron las reglas de deteccion y operacion del sistema",
        "OK",
        request,
    )
    if isinstance(updated, list) and updated:
        return updated[0]
    return _get_or_create_config(auth_user["id"])


@router.get("/telegram/status")
def get_telegram_status(authorization: str | None = Header(default=None)):
    _require_parent(authorization)
    recipients = get_family_recipients()
    return {
        **telegram_status(),
        "recipients": [
            {
                "id": item.get("id"),
                "nombres": item.get("nombres"),
                "apellidos": item.get("apellidos"),
                "numero": item.get("numero"),
                "telegram_chat_id": item.get("telegram_chat_id"),
            }
            for item in recipients
        ],
    }


@router.get("/telegram/updates")
def get_telegram_updates(authorization: str | None = Header(default=None)):
    _require_parent(authorization)
    updates = get_updates()
    chats = []
    seen = set()
    for update in updates:
        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None or chat_id in seen:
            continue
        seen.add(chat_id)
        chats.append(
            {
                "chat_id": str(chat_id),
                "type": chat.get("type"),
                "username": chat.get("username"),
                "first_name": chat.get("first_name"),
                "last_name": chat.get("last_name"),
                "text": message.get("text"),
            }
        )
    return {"chats": chats, "raw_count": len(updates)}


@router.post("/telegram/link/{user_id}/start")
def start_telegram_link(user_id: str, authorization: str | None = Header(default=None)):
    _require_parent(authorization)
    users = _request(
        "GET",
        f"/rest/v1/perfiles_usuarios?id=eq.{user_id}&select=id,nombres,apellidos,telegram_chat_id&limit=1",
    )
    if not users:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    username = bot_username()
    if not username:
        raise HTTPException(status_code=503, detail="No se pudo obtener el usuario del bot de Telegram")
    payload = _telegram_payload(user_id)
    return {
        "url": f"https://t.me/{username}?start={payload}",
        "payload": payload,
        "already_linked": bool(users[0].get("telegram_chat_id")),
        "telegram_chat_id": users[0].get("telegram_chat_id"),
    }


@router.post("/telegram/link/{user_id}/sync")
def sync_telegram_link(user_id: str, authorization: str | None = Header(default=None)):
    _require_parent(authorization)
    payload = _telegram_payload(user_id)
    updates = get_updates()
    for update in reversed(updates):
        message = update.get("message") or update.get("edited_message") or {}
        text = (message.get("text") or "").strip()
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        if not chat_id:
            continue
        if text == f"/start {payload}" or text.endswith(f" {payload}"):
            data = {"telegram_chat_id": str(chat_id)}
            _request(
                "PATCH",
                f"/rest/v1/perfiles_usuarios?id=eq.{user_id}",
                headers={"Prefer": "return=representation"},
                json=data,
            )
            return {"linked": True, "telegram_chat_id": str(chat_id)}

    users = _request(
        "GET",
        f"/rest/v1/perfiles_usuarios?id=eq.{user_id}&select=id,telegram_chat_id&limit=1",
    )
    current_chat_id = users[0].get("telegram_chat_id") if users else None
    return {"linked": bool(current_chat_id), "telegram_chat_id": current_chat_id}


@router.post("/telegram/test")
def test_telegram(payload: TelegramTest, request: Request, authorization: str | None = Header(default=None)):
    auth_user = _require_parent(authorization)
    chat_id = payload.chat_id
    if not chat_id:
        recipients = get_family_recipients()
        if not recipients:
            raise HTTPException(status_code=422, detail="No hay usuarios activos con telegram_chat_id registrado")
        chat_id = recipients[0].get("telegram_chat_id")

    try:
        sent = send_text(chat_id or "", payload.mensaje)
    except Exception as error:
        raise HTTPException(status_code=502, detail={"message": str(error), "telegram": telegram_status()}) from error
    _write_log(
        auth_user["id"],
        "TELEGRAM_PRUEBA",
        f"Se envio una prueba de Telegram al chat {chat_id}",
        "OK" if sent else "SIN_ENVIO",
        request,
    )
    return {"sent": sent, "to": chat_id, "telegram": telegram_status()}


@router.post("/users")
def create_user(payload: UserCreate, request: Request, authorization: str | None = Header(default=None)):
    auth_user_session = _require_parent(authorization)
    if payload.rol not in {"PADREs", "HIJOs", "OTROS"}:
        raise HTTPException(status_code=422, detail="Rol invalido")

    auth_user = _request(
        "POST",
        "/auth/v1/admin/users",
        json={
            "email": payload.email,
            "password": payload.password,
            "email_confirm": True,
            "user_metadata": {"usuario": payload.usuario, "rol": payload.rol},
        },
    )

    profile = {
        "id": auth_user["id"],
        "nombres": payload.nombres,
        "apellidos": payload.apellidos,
        "email": payload.email,
        "usuario": payload.usuario,
        "contrasena": hashlib.sha256(payload.password.encode("utf-8")).hexdigest(),
        "numero": payload.numero,
        "telegram_chat_id": payload.telegram_chat_id,
        "rol": payload.rol,
        "activo": payload.activo,
    }
    _request("POST", "/rest/v1/perfiles_usuarios", json=profile)
    _write_log(
        auth_user_session["id"],
        "USUARIO_CREADO",
        f"Se creo el usuario {payload.usuario} con rol {payload.rol}",
        "OK",
        request,
    )
    return profile


@router.put("/users/{user_id}")
def update_user(user_id: str, payload: UserUpdate, request: Request, authorization: str | None = Header(default=None)):
    auth_user = _require_parent(authorization)
    if payload.rol not in {"PADREs", "HIJOs", "OTROS"}:
        raise HTTPException(status_code=422, detail="Rol invalido")

    data = payload.model_dump()
    _request(
        "PATCH",
        f"/rest/v1/perfiles_usuarios?id=eq.{user_id}",
        headers={"Prefer": "return=representation"},
        json=data,
    )
    _write_log(
        auth_user["id"],
        "USUARIO_ACTUALIZADO",
        f"Se actualizo el usuario {payload.usuario} ({user_id})",
        "OK",
        request,
    )
    return {"ok": True}


@router.delete("/users/{user_id}")
def delete_user(user_id: str, request: Request, authorization: str | None = Header(default=None)):
    auth_user = _require_parent(authorization)
    _request("DELETE", f"/auth/v1/admin/users/{user_id}")
    _write_log(
        auth_user["id"],
        "USUARIO_ELIMINADO",
        f"Se elimino el usuario {user_id}",
        "OK",
        request,
    )
    return {"ok": True}


@router.patch("/events/{event_id}/attend")
def attend_event(event_id: str, request: Request, authorization: str | None = Header(default=None)):
    auth_user = _require_parent(authorization)
    _request(
        "PATCH",
        f"/rest/v1/eventos_sospechosos?id=eq.{event_id}",
        headers={"Prefer": "return=representation"},
        json={"atendido": True},
    )
    _write_log(
        auth_user["id"],
        "EVENTO_ATENDIDO",
        f"Se marco como atendido el evento {event_id}",
        "OK",
        request,
    )
    return {"ok": True}
