"""Carga de la base de migración desde el Excel fuente."""

import pandas as pd

SHAPE_ESPERADO = (161036, 13)
N_MESES_ESPERADO = 210
MES_INICIO = "2009-01-01"
MES_FIN = "2026-06-01"


def cargar_base(path: str) -> pd.DataFrame:
    """Lee la hoja 'Datos' del Excel de migración y valida su integridad.

    Construye la columna `fecha` a partir de Año y Mes cod, y valida que
    exista exactamente un mes por cada uno de los 210 meses consecutivos
    entre 2009-01 y 2026-06, sin huecos.
    """
    df = pd.read_excel(path, sheet_name="Datos")

    if df.shape != SHAPE_ESPERADO:
        raise ValueError(
            f"Shape inesperado: se obtuvo {df.shape}, se esperaba {SHAPE_ESPERADO}"
        )

    df["fecha"] = pd.to_datetime(
        dict(year=df["Año"], month=df["Mes cod"], day=1)
    )

    meses_esperados = pd.date_range(MES_INICIO, MES_FIN, freq="MS")
    meses_obtenidos = pd.DatetimeIndex(sorted(df["fecha"].unique()))

    if len(meses_obtenidos) != N_MESES_ESPERADO:
        raise ValueError(
            f"Se esperaban {N_MESES_ESPERADO} meses únicos, "
            f"se obtuvieron {len(meses_obtenidos)}"
        )

    if not meses_obtenidos.equals(meses_esperados):
        faltantes = meses_esperados.difference(meses_obtenidos)
        raise ValueError(
            f"Hay huecos en la serie de meses. Meses faltantes: {list(faltantes)}"
        )

    return df
