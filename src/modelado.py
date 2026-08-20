"""Variable respuesta y variables predictoras para los modelos de ML (Parte 2, incisos 2-3).

La variable respuesta se deriva de `clorofila` (clorofila-a en µg/L, calculada en
`src/dataset.py` a partir del índice NDCI). Las variables que participan en esa
construcción quedan excluidas como predictoras para evitar fuga de información.
"""

import numpy as np
import pandas as pd

# Umbral de clorofila-a (µg/L) para separar alta presencia de cianobacteria. WHO (2003),
# Guidelines for Safe Recreational Water Environments, fija el Alert Level 1 en aguas
# recreativas en clorofila-a >= 10 µg/L con presencia visible de cianobacterias. Coincide
# con el límite inferior del estado eutrófico del Trophic State Index de Carlson (1977) y
# de la clasificación OECD (1982). Justificación y referencias completas en
# informe/secciones/p2_02_variable_respuesta.md.
UMBRAL_CLOROFILA = 10.0

# Variables usadas para construir la variable respuesta: clorofila = f(ndci), ndci =
# f(rojo, b05). Quedan excluidas como predictoras porque producirían fuga de información
# directa hacia la variable respuesta (inciso 2.5).
EXCLUIDAS = ["clorofila", "ndci", "rojo", "b05"]

# Variables predictoras: bandas espectrales e índices independientes de la construcción de
# la respuesta. `clp` (probabilidad residual de nube) también se excluye de este conjunto:
# no es fuga de información, pero es un remanente de la limpieza de nubes del inciso 1 sin
# señal ambiental relevante para cianobacteria, no un predictor espectral o espacial.
PREDICTORES = ["verde", "azul", "b07", "b08", "b8a", "b11", "b12", "fai", "ndvi", "ndwi"]


def construir_respuesta(df: pd.DataFrame, umbral: float = UMBRAL_CLOROFILA) -> pd.DataFrame:
    """Agrega la columna binaria `alta_cianobacteria` según el umbral de clorofila-a.

    0 = ausencia o baja presencia (clorofila < umbral); 1 = alta presencia (clorofila >=
    umbral). No modifica `df` in place, retorna una copia.
    """
    out = df.copy()
    out["alta_cianobacteria"] = (out["clorofila"] >= umbral).astype(np.int8)
    return out


def distribucion_respuesta(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Distribución de `alta_cianobacteria` global, por lago y por combinación lago-fecha.

    Retorna un dict con tres tablas (n, n_alta, proporcion_alta), usadas en el inciso 2.3
    para describir la distribución y en el 2.4 para cuantificar el desbalance de clases.
    """

    def resumen(grupo: pd.DataFrame) -> pd.Series:
        n = len(grupo)
        n_alta = int(grupo["alta_cianobacteria"].sum())
        return pd.Series({"n": n, "n_alta": n_alta, "proporcion_alta": n_alta / n})

    global_ = resumen(df)
    por_lago = df.groupby("lago", observed=True).apply(resumen, include_groups=False)
    por_lago_fecha = df.groupby(["lago", "fecha"], observed=True).apply(resumen, include_groups=False)
    return {"global": global_, "por_lago": por_lago, "por_lago_fecha": por_lago_fecha}


def _demo():
    """Self-check: valida la regla del umbral y que predictoras y excluidas no se traslapen."""
    assert set(PREDICTORES).isdisjoint(EXCLUIDAS), "una predictora está marcada también como excluida"

    df = pd.DataFrame({
        "lago": ["atitlan"] * 4 + ["amatitlan"] * 2,
        "fecha": pd.to_datetime(["2025-01-01"] * 6),
        "clorofila": [5.0, 9.99, 10.0, 15.0, 3.0, 20.0],
    })
    out = construir_respuesta(df)
    assert out["alta_cianobacteria"].tolist() == [0, 0, 1, 1, 0, 1], "el umbral no se aplicó como >="

    dist = distribucion_respuesta(out)
    assert dist["global"]["n"] == 6 and dist["global"]["n_alta"] == 3
    assert dist["por_lago"].loc["atitlan", "n_alta"] == 2
    assert dist["por_lago"].loc["amatitlan", "n_alta"] == 1

    print("src.modelado: self-check OK")


if __name__ == "__main__":
    _demo()
