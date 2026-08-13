from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_DATA_RAW = RAIZ_PROYECTO / "data" / "raw"
RUTA_DATA_PROCESSED = RAIZ_PROYECTO / "data" / "processed"
RUTA_FIGURAS = RAIZ_PROYECTO / "informe" / "figuras"

PERFIL_SH = "cdse"
SH_BASE_URL = "https://sh.dataspace.copernicus.eu"
SH_TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
)

COLECCION_S2 = "sentinel-2-l1c"

LAGOS = {
    "atitlan": {
        "nombre": "Lago de Atitlán",
        "bbox": (-91.326256, 14.5948, -91.07151, 14.750979),
    },
    "amatitlan": {
        "nombre": "Lago de Amatitlán",
        "bbox": (-90.638065, 14.412347, -90.512924, 14.493799),
    },
}

RESOLUCION_M = 20

FECHAS_OFICIALES = {
    "amatitlan": [
        "2025-01-28", "2025-04-15", "2025-04-28", "2025-11-24", "2026-01-08",
        "2026-02-02", "2026-02-07", "2026-03-29", "2026-04-13", "2026-04-28",
        "2026-06-19",
    ],
    "atitlan": [
        "2025-01-18", "2025-04-13", "2025-05-13", "2025-07-17", "2025-11-21",
        "2025-12-29", "2026-02-12", "2026-03-24", "2026-04-13", "2026-04-28",
        "2026-07-22",
    ],
}

NUBOSIDAD_OFICIAL = {
    "amatitlan": {
        "2025-01-28": (0.06, "Sentinel-2B"),
        "2025-04-15": (0.09, "Sentinel-2A"),
        "2025-04-28": (1.03, "Sentinel-2B"),
        "2025-11-24": (0.50, "Sentinel-2B"),
        "2026-01-08": (0.77, "Sentinel-2C"),
        "2026-02-02": (0.39, "Sentinel-2B"),
        "2026-02-07": (0.02, "Sentinel-2C"),
        "2026-03-29": (0.01, "Sentinel-2C"),
        "2026-04-13": (0.09, "Sentinel-2B"),
        "2026-04-28": (4.96, "Sentinel-2C"),
        "2026-06-19": (13.00, "Sentinel-2A"),
    },
    "atitlan": {
        "2025-01-18": (0.02, "Sentinel-2B"),
        "2025-04-13": (0.54, "Sentinel-2C"),
        "2025-05-13": (4.37, "Sentinel-2C"),
        "2025-07-17": (3.57, "Sentinel-2A"),
        "2025-11-21": (3.15, "Sentinel-2A"),
        "2025-12-29": (3.17, "Sentinel-2C"),
        "2026-02-12": (0.04, "Sentinel-2B"),
        "2026-03-24": (3.17, "Sentinel-2B"),
        "2026-04-13": (0.01, "Sentinel-2B"),
        "2026-04-28": (4.96, "Sentinel-2C"),
        "2026-07-22": (4.02, "Sentinel-2B"),
    },
}

FECHA_COBERTURA_PARCIAL = {"lago": "amatitlan", "fecha": "2026-02-07", "cobertura_pct": 57.1}

BANDAS_REQUERIDAS = ["B02", "B03", "B04", "B05", "B07", "B08", "B8A", "B11", "B12"]

RUTA_DATA_RAW.mkdir(parents=True, exist_ok=True)
RUTA_DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
RUTA_FIGURAS.mkdir(parents=True, exist_ok=True)
