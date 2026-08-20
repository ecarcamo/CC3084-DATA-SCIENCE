"""Validación espacial mediante bloques regulares (Parte 2, inciso 6).

Divide cada lago en una cuadrícula regular sobre las coordenadas UTM 15N (EPSG:32615, ya
calculadas en el inciso 1) y usa esa cuadrícula como agrupador para una validación cruzada
que respeta la dependencia espacial entre observaciones cercanas, en contraste con la
validación aleatoria del inciso 4.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold, cross_validate

# Tamaño de bloque pedido por el enunciado (inciso 6.1). Se evalúa en el notebook si produce
# un número suficiente de bloques por lago antes de usarlo para la validación espacial.
TAMANO_BLOQUE_M = 1000


def asignar_bloques(df: pd.DataFrame, tam_m: float = TAMANO_BLOQUE_M) -> pd.Series:
    """Asigna cada observación a un bloque de una cuadrícula regular de `tam_m` metros.

    El bloque se deriva de la posición entera `(x_utm // tam_m, y_utm // tam_m)` y se
    calcula independientemente por lago (columna `lago`), para que un mismo identificador de
    bloque de Atitlán no se confunda con uno de Amatitlán. Retorna una Serie de strings
    "<lago>_<col>_<fila>", usable directamente como `groups` en GroupKFold/StratifiedGroupKFold.
    """
    col = (df["x_utm"] // tam_m).astype(int)
    fila = (df["y_utm"] // tam_m).astype(int)
    return df["lago"].astype(str) + "_" + col.astype(str) + "_" + fila.astype(str)


def resumen_bloques(df: pd.DataFrame, bloques: pd.Series) -> pd.DataFrame:
    """Número de bloques y observaciones por bloque, por lago (inciso 6.1)."""
    tmp = pd.DataFrame({"lago": df["lago"].to_numpy(), "bloque": bloques.to_numpy()})
    conteo = tmp.groupby(["lago", "bloque"], observed=True).size()
    return conteo.groupby("lago", observed=True).agg(
        n_bloques="count",
        obs_por_bloque_min="min",
        obs_por_bloque_mediana="median",
        obs_por_bloque_max="max",
    )


def n_splits_seguro(bloques: pd.Series, y: pd.Series, maximo: int = 5, minimo: int = 2) -> int:
    """Elige un número de folds que quepa en el lago con menos bloques y en la clase minoritaria.

    `StratifiedGroupKFold` necesita al menos `n_splits` bloques distintos y, para poder
    estratificar, al menos `n_splits` observaciones de la clase minoritaria. Si el tamaño de
    bloque del inciso 6.1 no alcanza para `maximo` folds, se reduce automáticamente en lugar
    de fallar, y el notebook reporta el valor efectivamente usado.
    """
    n_bloques_min = pd.Series(bloques).nunique()
    n_clase_min = int(y.value_counts().min())
    return max(minimo, min(maximo, n_bloques_min, n_clase_min))


def cv_espacial(modelo, X: pd.DataFrame, y: pd.Series, bloques: pd.Series, n_splits: int = 5, semilla: int = 42):
    """Validación cruzada agrupada por bloque espacial (inciso 6.3 y 6.4).

    Usa `StratifiedGroupKFold`: las observaciones de un mismo bloque nunca se separan entre
    entrenamiento y validación dentro de un fold (restricción de grupo), y además intenta
    mantener la proporción de clases de cada fold cercana a la global, algo que un
    `GroupKFold` simple no garantiza y que aquí es relevante por el desbalance del inciso 2.4.
    """
    cv = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=semilla)
    return cross_validate(modelo, X, y, groups=bloques, cv=cv, scoring=["roc_auc", "recall", "f1"], n_jobs=-1)


def cv_aleatoria(modelo, X: pd.DataFrame, y: pd.Series, n_splits: int = 5, semilla: int = 42):
    """Validación cruzada aleatoria estratificada (línea base de comparación, inciso 6.5)."""
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=semilla)
    return cross_validate(modelo, X, y, cv=cv, scoring=["roc_auc", "recall", "f1"], n_jobs=-1)


def _demo():
    """Self-check: cuadrícula, conteo por bloque, elección segura de folds y ambas CV."""
    rng = np.random.default_rng(0)
    n = 600
    df = pd.DataFrame({
        "lago": ["atitlan"] * 400 + ["amatitlan"] * 200,
        "x_utm": np.concatenate([rng.uniform(0, 5000, 400), rng.uniform(0, 3000, 200)]),
        "y_utm": np.concatenate([rng.uniform(0, 5000, 400), rng.uniform(0, 3000, 200)]),
    })
    bloques = asignar_bloques(df, tam_m=1000)
    assert bloques.nunique() <= 25 + 9, "más bloques de los que caben en las cuadrículas simuladas"
    assert bloques.str.startswith("atitlan_").sum() == 400
    assert bloques.str.startswith("amatitlan_").sum() == 200

    resumen = resumen_bloques(df, bloques)
    assert set(resumen.index) == {"atitlan", "amatitlan"}
    assert (resumen["n_bloques"] > 0).all()

    X = pd.DataFrame({"pred": rng.uniform(0, 1, n)})
    y = pd.Series((rng.uniform(0, 1, n) < 0.3).astype(int))
    n_splits = n_splits_seguro(bloques, y, maximo=5)
    assert 2 <= n_splits <= 5

    from sklearn.linear_model import LogisticRegression

    modelo = LogisticRegression()
    res_espacial = cv_espacial(modelo, X, y, bloques, n_splits=n_splits)
    res_aleatoria = cv_aleatoria(modelo, X, y, n_splits=n_splits)
    assert len(res_espacial["test_roc_auc"]) == n_splits
    assert len(res_aleatoria["test_roc_auc"]) == n_splits

    print("src.espacial: self-check OK")


if __name__ == "__main__":
    _demo()
