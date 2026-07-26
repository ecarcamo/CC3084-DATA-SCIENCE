from pathlib import Path

import pandas as pd


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SERIES = RAIZ_PROYECTO / "data" / "processed" / "series"
RUTA_FIGURAS = RAIZ_PROYECTO / "informe" / "figuras"
RUTA_RESULTADOS = RAIZ_PROYECTO / "resultados"

SERIES = {
    "total": "Total",
    "via_aerea": "Vía Aérea",
    "via_terrestre": "Vía Terrestre",
    "via_maritima": "Vía Marítima",
    "pais_el_salvador": "El Salvador",
    "pais_estados_unidos": "Estados Unidos",
    "pais_honduras": "Honduras",
}

CONJUNTOS = {
    "train": "_train",
    "test": "_test",
    "completa": "",
}


def cargar_serie(clave: str, conjunto: str) -> pd.Series:
    if clave not in SERIES:
        raise ValueError(f"Serie desconocida: {clave}")
    if conjunto not in CONJUNTOS:
        raise ValueError(f"Conjunto desconocido: {conjunto}")

    sufijo = CONJUNTOS[conjunto]
    ruta = RUTA_SERIES / f"serie_{clave}{sufijo}.csv"
    datos = pd.read_csv(ruta, parse_dates=["fecha"])
    serie = datos.set_index("fecha")["viajeros"].astype(float)
    return serie.asfreq("MS")
