import hashlib
from typing import Any

import requests
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.supabase_client import get_family_recipients, list_events
from app.whatsapp_client import _normalize_phone, send_template, send_text, status as whatsapp_status


router = APIRouter(prefix="/admin", tags=["admin"])


class UserCreate(BaseModel):
    nombres: str
    apellidos: str
    email: str
    usuario: str
    password: str
    rol: str
    numero: str | None = None
    activo: bool = True


class UserUpdate(BaseModel):
    nombres: str
    apellidos: str
    usuario: str
    rol: str
    numero: str | None = None
    activo: bool = True


class WhatsAppTest(BaseModel):
    numero: str | None = None
    mensaje: str = "Prueba de WhatsApp desde Seguridad V2"


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


def _require_parent(authorization: str | None) -> None:
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

    auth_user = auth_response.json()
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


def _require_session(authorization: str | None) -> None:
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


@router.get("/whatsapp/status")
def get_whatsapp_status(authorization: str | None = Header(default=None)):
    _require_parent(authorization)
    recipients = get_family_recipients()
    return {
        **whatsapp_status(),
        "recipients": [
            {
                "id": item.get("id"),
                "nombres": item.get("nombres"),
                "apellidos": item.get("apellidos"),
                "numero": item.get("numero"),
                "whatsapp": _normalize_phone(item.get("numero") or ""),
            }
            for item in recipients
        ],
    }


@router.post("/whatsapp/test")
def test_whatsapp(payload: WhatsAppTest, authorization: str | None = Header(default=None)):
    _require_parent(authorization)
    number = payload.numero
    if not number:
        recipients = get_family_recipients()
        if not recipients:
            raise HTTPException(status_code=422, detail="No hay usuarios activos con numero registrado")
        number = recipients[0].get("numero")

    try:
        sent = False
        if settings.whatsapp_send_template_first:
            template_params = [payload.mensaje] if settings.whatsapp_template_body_params else None
            sent = send_template(number or "", body_parameters=template_params)
        try:
            sent = send_text(number or "", payload.mensaje) or sent
        except Exception:
            if not sent:
                raise
    except Exception as error:
        raise HTTPException(status_code=502, detail={"message": str(error), "whatsapp": whatsapp_status()}) from error
    return {"sent": sent, "to": _normalize_phone(number or ""), "whatsapp": whatsapp_status()}


@router.post("/users")
def create_user(payload: UserCreate, authorization: str | None = Header(default=None)):
    _require_parent(authorization)
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
        "rol": payload.rol,
        "activo": payload.activo,
    }
    _request("POST", "/rest/v1/perfiles_usuarios", json=profile)
    return profile


@router.put("/users/{user_id}")
def update_user(user_id: str, payload: UserUpdate, authorization: str | None = Header(default=None)):
    _require_parent(authorization)
    if payload.rol not in {"PADREs", "HIJOs", "OTROS"}:
        raise HTTPException(status_code=422, detail="Rol invalido")

    data = payload.model_dump()
    _request(
        "PATCH",
        f"/rest/v1/perfiles_usuarios?id=eq.{user_id}",
        headers={"Prefer": "return=representation"},
        json=data,
    )
    return {"ok": True}


@router.delete("/users/{user_id}")
def delete_user(user_id: str, authorization: str | None = Header(default=None)):
    _require_parent(authorization)
    _request("DELETE", f"/auth/v1/admin/users/{user_id}")
    return {"ok": True}


@router.patch("/events/{event_id}/attend")
def attend_event(event_id: str, authorization: str | None = Header(default=None)):
    _require_parent(authorization)
    _request(
        "PATCH",
        f"/rest/v1/eventos_sospechosos?id=eq.{event_id}",
        headers={"Prefer": "return=representation"},
        json={"atendido": True},
    )
    return {"ok": True}
