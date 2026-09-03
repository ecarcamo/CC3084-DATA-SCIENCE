"""Carga e integración de los datos del Laboratorio 6 (YouTube).

Funciones puras y reutilizables por todas las etapas. No limpian nada: la
limpieza es la Etapa 2. Ejecutar este archivo (`python src/carga.py`) corre un
self-check con los números verificados sobre los CSV originales.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
VIDEOS_CSV = RAW / "youtube_videos.csv"
COMMENTS_CSV = RAW / "youtube_comments.csv"

# Columnas cuyo valor textual original debe preservarse tal cual (identificadores).
# El resto se deja con la inferencia de tipos de pandas.
_ID_COLS_VIDEOS = ["video_id", "channel_id"]
_ID_COLS_COMMENTS = ["video_id", "comment_id", "channel_id", "author_channel_id"]


def cargar_videos() -> pd.DataFrame:
    """youtube_videos.csv crudo. 1 fila = 1 video. Llave primaria: video_id."""
    return pd.read_csv(VIDEOS_CSV, dtype={c: "string" for c in _ID_COLS_VIDEOS})


def cargar_comentarios() -> pd.DataFrame:
    """youtube_comments.csv crudo. 1 fila = 1 comentario principal. Llave: comment_id."""
    return pd.read_csv(COMMENTS_CSV, dtype={c: "string" for c in _ID_COLS_COMMENTS})


def catalogo_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Resumen por columna: tipo, nulos, cardinalidad, si es constante y un ejemplo.

    Sirve para el inciso 1.2 (clasificar variables) y arranca el diagnóstico 2.1.
    """
    filas = []
    for col in df.columns:
        s = df[col]
        no_nulos = s.dropna()
        nunq = no_nulos.nunique()
        ejemplo = no_nulos.iloc[0] if not no_nulos.empty else pd.NA
        filas.append(
            {
                "variable": col,
                "dtype": str(s.dtype),
                "nulos": int(s.isna().sum()),
                "pct_nulos": round(100 * s.isna().mean(), 1),
                "unicos": int(nunq),
                "constante": nunq <= 1,
                "ejemplo": ejemplo,
            }
        )
    return pd.DataFrame(filas)


def _columnas_redundantes(comentarios: pd.DataFrame, videos: pd.DataFrame) -> list[str]:
    """Columnas presentes en ambos conjuntos (aparte de video_id, la llave)."""
    comunes = (set(comentarios.columns) & set(videos.columns)) - {"video_id"}
    return sorted(comunes)


def integrar(comentarios: pd.DataFrame, videos: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Left join comentarios <- videos por video_id (relación muchos-a-uno).

    Devuelve (df_integrado, reporte). El left join conserva los 406 comentarios;
    `validate="m:1"` garantiza que no se dupliquen filas. Las columnas presentes
    en ambos lados se marcan con sufijos _com / _vid para auditar redundancias.
    """
    redundantes = _columnas_redundantes(comentarios, videos)
    integrado = comentarios.merge(
        videos, on="video_id", how="left", validate="m:1", suffixes=("_com", "_vid")
    )

    vids_con = comentarios["video_id"].nunique()
    asociados = comentarios["video_id"].isin(videos["video_id"]).sum()
    reporte = {
        "comentarios_entrada": len(comentarios),
        "comentarios_salida": len(integrado),
        "comentarios_asociados": int(asociados),
        "pct_asociados": round(100 * float(asociados) / len(comentarios), 2),
        "videos_totales": videos["video_id"].nunique(),
        "videos_con_comentarios": int(vids_con),
        "videos_sin_comentarios": int(videos["video_id"].nunique() - vids_con),
        "columnas_redundantes": redundantes,
        "filas_agregadas_por_join": len(integrado) - len(comentarios),
    }
    return integrado, reporte


def _self_check() -> None:
    v = cargar_videos()
    c = cargar_comentarios()

    assert v.shape == (293, 20), v.shape
    assert c.shape == (406, 17), c.shape
    assert v["video_id"].is_unique and c["comment_id"].is_unique
    assert v["channel_id"].nunique() == 97
    assert c["author_channel_id"].nunique() == 332

    # relaciones 1:1 entre id y nombre visible
    assert (v.groupby("channel_id")["channel_name"].nunique() <= 1).all()
    assert (c.groupby("author_channel_id")["author_name"].nunique() <= 1).all()

    # los dos conjuntos de nodos de la red bipartita son disjuntos
    assert c["author_channel_id"].isin(v["channel_id"]).sum() == 0

    integrado, rep = integrar(c, v)
    assert rep["pct_asociados"] == 100.0, rep
    assert rep["videos_con_comentarios"] == 19, rep
    assert rep["videos_sin_comentarios"] == 274, rep
    assert rep["filas_agregadas_por_join"] == 0, rep
    assert len(integrado) == 406

    print("carga.py: self-check OK")
    print(f"  videos={v.shape}  comentarios={c.shape}  integrado={integrado.shape}")
    print(f"  reporte de integración: {rep}")


if __name__ == "__main__":
    _self_check()
