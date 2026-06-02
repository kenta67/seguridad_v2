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
    alert_temp_dir: Path = BASE_DIR / os.getenv("ALERT_TEMP_DIR", "tmp")
    camera_index: int = int(os.getenv("CAMERA_INDEX", "0"))
    detection_confidence: float = float(os.getenv("DETECTION_CONFIDENCE", "0.45"))
    detection_iou: float = float(os.getenv("DETECTION_IOU", "0.70"))
    detection_max_det: int = int(os.getenv("DETECTION_MAX_DET", "100"))
    detection_frame_skip: int = int(os.getenv("DETECTION_FRAME_SKIP", "3"))
    test_detection_confidence: float = float(os.getenv("TEST_DETECTION_CONFIDENCE", "0.01"))
    test_detection_imgsz: int = int(os.getenv("TEST_DETECTION_IMGSZ", "1280"))
    suspicious_labels: set[str] = None
    alert_cooldown_seconds: int = int(os.getenv("ALERT_COOLDOWN_SECONDS", "20"))
    video_seconds: int = int(os.getenv("VIDEO_SECONDS", "4"))
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    alerts_enabled: bool = os.getenv("ALERTS_ENABLED", "true").lower() == "true"
    telegram_enabled: bool = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_bot_username: str = os.getenv("TELEGRAM_BOT_USERNAME", "")
    telegram_parse_mode: str = os.getenv("TELEGRAM_PARSE_MODE", "HTML")
    red_alert_repeat_seconds: int = int(os.getenv("RED_ALERT_REPEAT_SECONDS", "30"))
    red_alert_max_repeats: int = int(os.getenv("RED_ALERT_MAX_REPEATS", "30"))

    def __post_init__(self):
        if self.suspicious_labels is None:
            labels = os.getenv(
                "SUSPICIOUS_LABELS",
                "arma_de_fuego,arma_blanca,pasamontana,mascarilla,casco",
            )
            object.__setattr__(self, "suspicious_labels", _labels(labels))


settings = Settings()
