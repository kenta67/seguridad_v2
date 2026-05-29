from pathlib import Path

from supabase import Client, create_client

from app.config import settings


def get_supabase() -> Client | None:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def upload_file(local_path: Path, storage_path: str, content_type: str) -> str | None:
    client = get_supabase()
    if client is None:
        return None

    with local_path.open("rb") as file:
        client.storage.from_(settings.supabase_storage_bucket).upload(
            storage_path,
            file,
            {"content-type": content_type, "upsert": "true"},
        )

    return storage_path


def insert_event(
    tipo_evento: str,
    descripcion: str,
    confianza: float,
    nivel_riesgo: str,
    imagen_path: str | None,
    video_path: str | None,
) -> None:
    client = get_supabase()
    if client is None:
        return

    client.table("eventos_sospechosos").insert(
        {
            "tipo_evento": tipo_evento,
            "descripcion": descripcion,
            "confianza": round(confianza * 100, 2),
            "nivel_riesgo": nivel_riesgo,
            "imagen_evidencia_url": imagen_path,
            "video_evidencia_url": video_path,
        }
    ).execute()

