"""Construcción de las series de tiempo mensuales de viajeros.

Cada serie se guarda como CSV con exactamente dos columnas: `fecha`
(formato YYYY-MM-01) y `viajeros` (float), con índice mensual completo
y sin huecos (los meses sin registros quedan en 0).
"""

import os

import pandas as pd

FECHA_INICIO = "2009-01-01"
FECHA_FIN = "2026-06-01"
FECHA_FIN_TRAIN = "2021-03-01"

VIAS = {
    "aerea": "Aérea",
    "terrestre": "Terrestre",
    "maritima": "Marítima",
}

# Top 3 países de residencia excluyendo Guatemala (residentes retornando,
# no viajeros internacionales entrantes; ver decisión documentada en el
# informe de datos y limpieza).
PAISES_TOP3 = {
    "el_salvador": "El Salvador",
    "estados_unidos": "Estados Unidos de América",
    "honduras": "Honduras",
}


def _agregar_mensual(df_filtrado: pd.DataFrame, fecha_fin: str) -> pd.DataFrame:
    agregado = df_filtrado.groupby("fecha")["Viajero"].sum()
    indice_completo = pd.date_range(FECHA_INICIO, fecha_fin, freq="MS")
    agregado = agregado.reindex(indice_completo, fill_value=0.0)
    return pd.DataFrame(
        {
            "fecha": agregado.index.strftime("%Y-%m-01"),
            "viajeros": agregado.values.astype(float),
        }
    )


def serie_total(df: pd.DataFrame, train: bool = False) -> pd.DataFrame:
    fecha_fin = FECHA_FIN_TRAIN if train else FECHA_FIN
    return _agregar_mensual(df, fecha_fin)


def serie_via(df: pd.DataFrame, via: str, train: bool = False) -> pd.DataFrame:
    fecha_fin = FECHA_FIN_TRAIN if train else FECHA_FIN
    return _agregar_mensual(df[df["Vía"] == via], fecha_fin)


def serie_pais(df: pd.DataFrame, pais: str, train: bool = False) -> pd.DataFrame:
    fecha_fin = FECHA_FIN_TRAIN if train else FECHA_FIN
    return _agregar_mensual(df[df["País"] == pais], fecha_fin)


def _verificar_suma_vias(series_vias: dict, serie_total_df: pd.DataFrame) -> None:
    suma_vias = sum(s["viajeros"].values for s in series_vias.values())
    if not (abs(suma_vias - serie_total_df["viajeros"].values).max() < 1e-6):
        raise ValueError(
            "La suma de las series por vía no reproduce la serie total"
        )


def generar_series(df: pd.DataFrame, output_dir: str) -> dict:
    """Genera y guarda las 7 series (obligatoria + vías + países) y sus
    versiones de entrenamiento en `output_dir`. Devuelve un dict con todas
    las series en memoria para uso posterior (p. ej. en el notebook)."""
    os.makedirs(output_dir, exist_ok=True)

    resultado = {}

    resultado["total"] = serie_total(df)
    resultado["total_train"] = serie_total(df, train=True)

    series_vias = {}
    series_vias_train = {}
    for clave, valor in VIAS.items():
        series_vias[clave] = serie_via(df, valor)
        series_vias_train[clave] = serie_via(df, valor, train=True)
        resultado[f"via_{clave}"] = series_vias[clave]
        resultado[f"via_{clave}_train"] = series_vias_train[clave]

    _verificar_suma_vias(series_vias, resultado["total"])
    _verificar_suma_vias(series_vias_train, resultado["total_train"])

    for clave, valor in PAISES_TOP3.items():
        resultado[f"pais_{clave}"] = serie_pais(df, valor)
        resultado[f"pais_{clave}_train"] = serie_pais(df, valor, train=True)

    nombres_archivo = {
        "total": "serie_total.csv",
        "total_train": "serie_total_train.csv",
        **{f"via_{c}": f"serie_via_{c}.csv" for c in VIAS},
        **{f"via_{c}_train": f"serie_via_{c}_train.csv" for c in VIAS},
        **{f"pais_{c}": f"serie_pais_{c}.csv" for c in PAISES_TOP3},
        **{f"pais_{c}_train": f"serie_pais_{c}_train.csv" for c in PAISES_TOP3},
    }

    for clave, nombre_archivo in nombres_archivo.items():
        resultado[clave].to_csv(
            os.path.join(output_dir, nombre_archivo), index=False
        )

    return resultado
