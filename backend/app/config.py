import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def _labels(value: str) -> set[str]:
    return {item.strip().lower() for item in value.split(",") if item.strip()}


@dataclass(frozen=True)
class Settings:
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    supabase_storage_bucket: str = os.getenv("SUPABASE_STORAGE_BUCKET", "evidencias")
    model_path: Path = BASE_DIR / os.getenv("MODEL_PATH", "models/best.pt")
    camera_index: int = int(os.getenv("CAMERA_INDEX", "0"))
    detection_confidence: float = float(os.getenv("DETECTION_CONFIDENCE", "0.45"))
    suspicious_labels: set[str] = None
    alert_cooldown_seconds: int = int(os.getenv("ALERT_COOLDOWN_SECONDS", "20"))
    video_seconds: int = int(os.getenv("VIDEO_SECONDS", "4"))
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    def __post_init__(self):
        if self.suspicious_labels is None:
            labels = os.getenv(
                "SUSPICIOUS_LABELS",
                "person,knife,pistol,gun,weapon,cuchillo,arma,persona",
            )
            object.__setattr__(self, "suspicious_labels", _labels(labels))


settings = Settings()

