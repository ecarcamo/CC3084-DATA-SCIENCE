"""Funciones puras de limpieza sobre la base de migración.

Ninguna función borra filas. Cada función que transforma una columna
conserva el valor original en una columna con sufijo `_raw`.
"""

import pandas as pd


def limpiar_region_dos(df: pd.DataFrame) -> pd.DataFrame:
    """Unifica 'Cruceristas'/'Cruceros' y reetiqueta el valor basura '0'."""
    df = df.copy()
    df["Región dos_raw"] = df["Región dos"]
    df["Región dos"] = df["Región dos"].replace(
        {"Cruceristas": "Cruceros", "0": "Sin especificar"}
    )
    return df


def limpiar_pais(df: pd.DataFrame) -> pd.DataFrame:
    """Unifica variantes de 'País' que solo difieren en mayúsculas/minúsculas.

    Para cada grupo de valores que coinciden al comparar en minúsculas, se
    elige como forma canónica la variante con más registros (la usada de
    forma consistente durante todo el período) y se reemplazan las demás.
    """
    df = df.copy()
    df["País_raw"] = df["País"]

    conteos = df["País"].value_counts()
    canonico_por_clave = {}
    for valor, conteo in conteos.items():
        clave = valor.lower()
        actual = canonico_por_clave.get(clave)
        if actual is None or conteo > conteos[actual]:
            canonico_por_clave[clave] = valor

    mapping = {
        valor: canonico_por_clave[valor.lower()] for valor in conteos.index
    }
    df["País"] = df["País"].map(mapping)
    return df


def limpiar_regiones_omt(df: pd.DataFrame) -> pd.DataFrame:
    """Unifica los valores basura '0x2a' y 'SIN ESPECIFICAR' en 'Sin especificar'."""
    df = df.copy()
    df["Regiones OMT_raw"] = df["Regiones OMT"]
    df["Regiones OMT"] = df["Regiones OMT"].replace(
        {"0x2a": "Sin especificar", "SIN ESPECIFICAR": "Sin especificar"}
    )
    return df


def validar_calidad(df: pd.DataFrame) -> dict:
    """Confirma por código la calidad de la base ya limpia.

    No modifica el DataFrame; documenta los hallazgos ya conocidos sobre
    `Viajero` (decimales por estimaciones/prorrateos, y ceros exactos) y
    sobre `Frontera` (la categoría 'Cruceros' aparece mezclada con
    fronteras terrestres/marítimas legítimas, se deja así pero se reporta).
    """
    n_nulos = int(df.isnull().sum().sum())
    n_duplicados = int(df.duplicated().sum())
    viajero_decimal = df["Viajero"] % 1 != 0
    n_viajero_decimal = int(viajero_decimal.sum())
    n_viajero_cero = int((df["Viajero"] == 0).sum())
    fronteras_no_numeradas = sorted(
        f for f in df["Frontera"].unique() if not f[:2].isdigit()
    )

    if n_nulos != 0:
        raise ValueError(f"La base tiene {n_nulos} valores nulos, se esperaban 0")
    if n_duplicados != 0:
        raise ValueError(
            f"La base tiene {n_duplicados} filas duplicadas exactas, se esperaban 0"
        )

    return {
        "n_nulos": n_nulos,
        "n_duplicados_exactos": n_duplicados,
        "n_viajero_con_decimales": n_viajero_decimal,
        "n_viajero_cero": n_viajero_cero,
        "fronteras_no_numeradas": fronteras_no_numeradas,
    }


def limpiar_base(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica el pipeline completo de limpieza y valida el resultado."""
    df = limpiar_region_dos(df)
    df = limpiar_pais(df)
    df = limpiar_regiones_omt(df)
    validar_calidad(df)
    return df
