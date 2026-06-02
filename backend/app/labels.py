RISK_LABELS = {
    "persona": {"color": (0, 180, 0), "risk": "BAJO", "display": "Persona"},
    "arma_de_fuego": {"color": (0, 0, 255), "risk": "CRITICO", "display": "Arma de fuego"},
    "arma_blanca": {"color": (0, 0, 255), "risk": "ALTO", "display": "Arma blanca"},
    "pasamontana": {"color": (0, 140, 255), "risk": "ALTO", "display": "Pasamontana"},
    "mascarilla": {"color": (0, 200, 255), "risk": "MEDIO", "display": "Mascarilla"},
    "casco": {"color": (0, 200, 255), "risk": "MEDIO", "display": "Casco"},
}

LABEL_ALIASES = {
    "0": "persona",
    "person": "persona",
    "persona": "persona",
    "personas": "persona",
    "1": "arma_de_fuego",
    "arma": "arma_de_fuego",
    "arma_fuego": "arma_de_fuego",
    "arma_de_fuego": "arma_de_fuego",
    "pistola": "arma_de_fuego",
    "gun": "arma_de_fuego",
    "firearm": "arma_de_fuego",
    "2": "arma_blanca",
    "arma_blanca": "arma_blanca",
    "arma_blancas": "arma_blanca",
    "cuchillo": "arma_blanca",
    "cuchillos": "arma_blanca",
    "knife": "arma_blanca",
    "navaja": "arma_blanca",
    "machete": "arma_blanca",
    "3": "pasamontana",
    "pasamontanas": "pasamontana",
    "balaclava": "pasamontana",
    "4": "mascarilla",
    "mascara": "mascarilla",
    "mask": "mascarilla",
    "face_mask": "mascarilla",
    "5": "casco",
    "helmet": "casco",
}


def normalize_label(label: str) -> str:
    normalized = label.strip().lower().replace(" ", "_").replace("-", "_")
    return LABEL_ALIASES.get(normalized, normalized)


def label_color(label: str):
    return RISK_LABELS.get(normalize_label(label), {"color": (0, 180, 0)})["color"]


def display_label(label: str) -> str:
    return RISK_LABELS.get(normalize_label(label), {"display": label})["display"]


def risk_level(label: str) -> str:
    return RISK_LABELS.get(normalize_label(label), {"risk": "BAJO"})["risk"]
