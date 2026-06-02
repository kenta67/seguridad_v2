from pathlib import Path

from storage3.exceptions import StorageApiError
from supabase import Client, create_client

from app.config import settings


DEFAULT_CONFIG = {
    "deteccion_personas": True,
    "deteccion_armas": True,
    "deteccion_armas_blancas": True,
    "deteccion_rostro_cubierto": True,
    "grabacion_automatica": True,
    "notificaciones_push": True,
}


def get_supabase() -> Client | None:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def upload_file(local_path: Path, storage_path: str, content_type: str) -> str | None:
    client = get_supabase()
    if client is None:
        return None
    file_options = {
        "content-type": content_type,
        "contentType": content_type,
        "cache-control": "3600",
        "upsert": "true",
    }

    try:
        with local_path.open("rb") as file:
            client.storage.from_(settings.supabase_storage_bucket).upload(
                storage_path,
                file,
                file_options,
            )
    except StorageApiError as error:
        if "Bucket not found" not in str(error):
            raise
        ensure_storage_bucket(client)
        with local_path.open("rb") as file:
            client.storage.from_(settings.supabase_storage_bucket).upload(
                storage_path,
                file,
                file_options,
            )

    return storage_path


def storage_public_url(storage_path: str | None) -> str | None:
    if not storage_path:
        return None
    if storage_path.startswith(("http://", "https://")):
        return storage_path
    base_url = settings.supabase_url.rstrip("/")
    bucket = settings.supabase_storage_bucket.strip("/")
    path = storage_path.lstrip("/")
    return f"{base_url}/storage/v1/object/public/{bucket}/{path}"


def storage_path_from_url(value: str | None) -> str | None:
    if not value:
        return None
    marker = f"/storage/v1/object/public/{settings.supabase_storage_bucket}/"
    if marker in value:
        return value.split(marker, 1)[1]
    if value.startswith(("http://", "https://")):
        return None
    return value


def ensure_storage_bucket(client: Client | None = None) -> None:
    client = client or get_supabase()
    if client is None:
        return
    try:
        client.storage.create_bucket(
            settings.supabase_storage_bucket,
            settings.supabase_storage_bucket,
            {"public": True},
        )
    except Exception as error:
        if "already exists" not in str(error).lower() and "Duplicate" not in str(error):
            raise
    try:
        client.storage.update_bucket(settings.supabase_storage_bucket, {"public": True})
    except Exception:
        pass


def create_signed_url(storage_path: str, expires_in: int = 3600) -> str | None:
    client = get_supabase()
    if client is None or not storage_path:
        return None
    path = storage_path_from_url(storage_path)
    if path is None:
        return storage_path

    result = client.storage.from_(settings.supabase_storage_bucket).create_signed_url(
        path,
        expires_in,
    )
    if isinstance(result, dict):
        return result.get("signedURL") or result.get("signedUrl") or result.get("signed_url")
    return None


def get_family_recipients() -> list[dict]:
    client = get_supabase()
    if client is None:
        return []

    result = (
        client.table("perfiles_usuarios")
        .select("id,nombres,apellidos,numero,telegram_chat_id,rol,activo")
        .eq("activo", True)
        .execute()
    )
    return [item for item in (result.data or []) if item.get("telegram_chat_id")]


def get_system_config() -> dict:
    client = get_supabase()
    if client is None:
        return dict(DEFAULT_CONFIG)

    result = (
        client.table("configuraciones")
        .select("*")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        return dict(DEFAULT_CONFIG)
    return {**DEFAULT_CONFIG, **result.data[0]}


def is_event_attended(event_id: str) -> bool:
    client = get_supabase()
    if client is None:
        return True

    result = (
        client.table("eventos_sospechosos")
        .select("atendido")
        .eq("id", event_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        return True
    return bool(result.data[0].get("atendido"))


def insert_event(
    tipo_evento: str,
    descripcion: str,
    confianza: float,
    nivel_riesgo: str,
    imagen_url: str | None,
    video_url: str | None,
) -> str | None:
    client = get_supabase()
    if client is None:
        return

    result = client.table("eventos_sospechosos").insert(
        {
            "tipo_evento": tipo_evento,
            "descripcion": descripcion,
            "confianza": round(confianza * 100, 2),
            "nivel_riesgo": nivel_riesgo,
            "imagen_evidencia_url": imagen_url,
            "video_evidencia_url": video_url,
        }
    ).execute()
    if result.data:
        return result.data[0].get("id")
    return None


def list_events(limit: int = 50) -> list[dict]:
    client = get_supabase()
    if client is None:
        return []

    result = (
        client.table("eventos_sospechosos")
        .select("*")
        .order("fecha_evento", desc=True)
        .limit(limit)
        .execute()
    )
    events = result.data or []
    for event in events:
        event["imagen_evidencia_url"] = storage_public_url(event.get("imagen_evidencia_url"))
        event["video_evidencia_url"] = storage_public_url(event.get("video_evidencia_url"))
    return events
