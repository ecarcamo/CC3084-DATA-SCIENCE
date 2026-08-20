"""Variable respuesta y variables predictoras para los modelos de ML (Parte 2, incisos 2-3).

La variable respuesta se deriva de `clorofila` (clorofila-a en µg/L, calculada en
`src/dataset.py` a partir del índice NDCI). Las variables que participan en esa
construcción quedan excluidas como predictoras para evitar fuga de información.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_sample_weight

from src.config import RUTA_DATA_PROCESSED

SEMILLA = 42
RUTA_MODELOS = RUTA_DATA_PROCESSED / "modelos"

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
# `verde_azul_ratio` es la única variable derivada (inciso 3.3): no se agregan más razones
# de bandas SWIR/red-edge porque b11, b12, b07 y b8a ya entran individualmente como
# predictoras y una razón entre ellas sería casi colineal, sin aportar señal adicional.
PREDICTORES = [
    "verde", "azul", "b07", "b08", "b8a", "b11", "b12", "fai", "ndvi", "ndwi",
    "verde_azul_ratio",
]


def agregar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega `verde_azul_ratio`, único predictor derivado del inciso 3.3.

    Razón entre las bandas verde (B03) y azul (B02), análoga simplificada a las razones de
    color oceánico OC2/OC3 (O'Reilly et al., 1998) usadas para estimar pigmentos
    fotosintéticos en agua abierta. No comparte bandas con `ndci`/`clorofila`, por lo que no
    introduce fuga de información. No modifica `df` in place, retorna una copia.
    """
    out = df.copy()
    out["verde_azul_ratio"] = (out["verde"] / out["azul"]).astype(np.float32)
    return out


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


def dividir_datos(
    df: pd.DataFrame, predictores: list[str] = PREDICTORES, test_size: float = 0.3, semilla: int = SEMILLA
):
    """División 70/30 estratificada por `alta_cianobacteria` (inciso 4.2).

    Estratificar preserva la proporción de clases del inciso 2.4 en ambos subconjuntos. La
    semilla fija hace que el mismo conjunto de prueba se reproduzca en cualquier notebook que
    llame esta función sobre el mismo `df`, sin necesidad de persistir los índices, y es el
    conjunto de prueba compartido que exige el inciso 4.4 para comparar los tres modelos.
    """
    X = df[predictores]
    y = df["alta_cianobacteria"]
    return train_test_split(X, y, test_size=test_size, stratify=y, random_state=semilla)


def construir_modelos_base(semilla: int = SEMILLA) -> dict:
    """Instancia los tres modelos mínimos del inciso 4.1, sin ajustar.

    Regresión Logística incluye escalado en un `Pipeline` porque, a diferencia de los dos
    modelos de árboles, es sensible a la escala de los predictores. Random Forest y
    Regresión Logística reciben `class_weight="balanced"` para compensar el desbalance del
    inciso 2.4; `GradientBoostingClassifier` no admite ese parámetro, así que su
    entrenamiento se compensa con `sample_weight` en `entrenar_modelos`.
    """
    return {
        "regresion_logistica": Pipeline([
            ("escalado", StandardScaler()),
            ("modelo", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=semilla)),
        ]),
        "random_forest": RandomForestClassifier(class_weight="balanced", random_state=semilla, n_jobs=-1),
        "gradient_boosting": GradientBoostingClassifier(random_state=semilla),
    }


def entrenar_modelos(modelos: dict, X_train: pd.DataFrame, y_train: pd.Series) -> dict:
    """Entrena cada modelo de `construir_modelos_base` (inciso 4.2)."""
    pesos = compute_sample_weight("balanced", y_train)
    ajustados = {}
    for nombre, modelo in modelos.items():
        if nombre == "gradient_boosting":
            modelo.fit(X_train, y_train, sample_weight=pesos)
        else:
            modelo.fit(X_train, y_train)
        ajustados[nombre] = modelo
    return ajustados


# Grids pequeños e intencionalmente distintos por modelo (inciso 4.3): para cada uno se
# varían los hiperparámetros que más afectan el balance sesgo/varianza -- regularización en
# Regresión Logística, profundidad/tamaño de hoja en Random Forest, número de árboles/tasa
# de aprendizaje/profundidad en Gradient Boosting -- explorados con RandomizedSearchCV para
# mantener el costo de cómputo acotado sobre la muestra de trabajo.
GRIDS_HIPERPARAMETROS = {
    "regresion_logistica": {"modelo__C": [0.01, 0.1, 1.0, 10.0]},
    "random_forest": {
        "n_estimators": [200, 400],
        "max_depth": [8, 16, None],
        "min_samples_leaf": [1, 5, 20],
    },
    "gradient_boosting": {
        "n_estimators": [100, 200],
        "learning_rate": [0.05, 0.1],
        "max_depth": [2, 3, 4],
    },
}


def ajustar_hiperparametros(
    nombre: str, modelo, X_train: pd.DataFrame, y_train: pd.Series,
    n_iter: int = 8, cv: int = 3, semilla: int = SEMILLA,
):
    """Búsqueda aleatoria de hiperparámetros para un modelo (inciso 4.3).

    Optimiza ROC-AUC por validación cruzada de `cv` particiones sobre el conjunto de
    entrenamiento. Es el criterio de selección: se elige la combinación con mejor ROC-AUC
    promedio, la métrica menos sensible al desbalance de clases del inciso 2.4. Retorna el
    mejor estimador ya ajustado y sus hiperparámetros.
    """
    grid = GRIDS_HIPERPARAMETROS[nombre]
    fit_params = {}
    if nombre == "gradient_boosting":
        fit_params["sample_weight"] = compute_sample_weight("balanced", y_train)
    buscador = RandomizedSearchCV(
        modelo, grid, n_iter=n_iter, cv=cv, scoring="roc_auc", random_state=semilla, n_jobs=-1,
    )
    buscador.fit(X_train, y_train, **fit_params)
    return buscador.best_estimator_, buscador.best_params_


def evaluar(modelo, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """Calcula Accuracy, Precision, Recall, F1, ROC-AUC y matriz de confusión (inciso 5.1)."""
    y_pred = modelo.predict(X_test)
    y_proba = modelo.predict_proba(X_test)[:, 1]
    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_proba),
        "matriz_confusion": confusion_matrix(y_test, y_pred),
        "y_pred": y_pred,
        "y_proba": y_proba,
    }


def guardar_modelo(nombre: str, modelo, ruta: Path = RUTA_MODELOS) -> None:
    """Persiste un modelo ajustado, para reusarlo en los incisos 7 a 9 sin reentrenar."""
    ruta.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, ruta / f"{nombre}.joblib")


def cargar_modelo(nombre: str, ruta: Path = RUTA_MODELOS):
    """Carga un modelo previamente guardado con `guardar_modelo`."""
    return joblib.load(ruta / f"{nombre}.joblib")


def importancia_global(modelo, predictores: list[str] = PREDICTORES) -> pd.Series:
    """Importancia global de cada predictora para el modelo ajustado (inciso 8.1).

    Random Forest y Gradient Boosting exponen `feature_importances_` directamente. Regresión
    Logística, envuelta en un `Pipeline` con escalado, no la tiene: se usa el valor absoluto
    de sus coeficientes, comparables entre sí porque el escalado ya deja a todas las
    predictoras en la misma escala. Retorna una Serie ordenada de mayor a menor importancia.
    """
    if hasattr(modelo, "feature_importances_"):
        valores = modelo.feature_importances_
    elif hasattr(modelo, "named_steps"):
        valores = np.abs(modelo.named_steps["modelo"].coef_[0])
    else:
        raise ValueError("modelo sin `feature_importances_` ni `coef_` reconocido")
    return pd.Series(valores, index=predictores).sort_values(ascending=False)


def _demo():
    """Self-check: valida la regla del umbral, la feature derivada y que predictoras y
    excluidas no se traslapen."""
    assert set(PREDICTORES).isdisjoint(EXCLUIDAS), "una predictora está marcada también como excluida"

    df = pd.DataFrame({
        "lago": ["atitlan"] * 4 + ["amatitlan"] * 2,
        "fecha": pd.to_datetime(["2025-01-01"] * 6),
        "clorofila": [5.0, 9.99, 10.0, 15.0, 3.0, 20.0],
        "verde": [0.2, 0.4, 0.3, 0.6, 0.1, 0.5],
        "azul": [0.1, 0.2, 0.1, 0.3, 0.2, 0.25],
    })
    out = construir_respuesta(df)
    assert out["alta_cianobacteria"].tolist() == [0, 0, 1, 1, 0, 1], "el umbral no se aplicó como >="

    dist = distribucion_respuesta(out)
    assert dist["global"]["n"] == 6 and dist["global"]["n_alta"] == 3
    assert dist["por_lago"].loc["atitlan", "n_alta"] == 2
    assert dist["por_lago"].loc["amatitlan", "n_alta"] == 1

    con_features = agregar_features(df)
    np.testing.assert_allclose(con_features["verde_azul_ratio"], df["verde"] / df["azul"])
    assert "verde_azul_ratio" not in df.columns, "agregar_features no debe mutar el df original"

    import tempfile

    rng = np.random.default_rng(0)
    n = 400
    df_grande = pd.DataFrame({p: rng.uniform(0.01, 1.5, n) for p in PREDICTORES})
    df_grande["clorofila"] = rng.uniform(-5, 30, n)
    df_grande = construir_respuesta(df_grande)

    X_train, X_test, y_train, y_test = dividir_datos(df_grande)
    assert len(X_train) + len(X_test) == n
    assert abs(y_train.mean() - y_test.mean()) < 0.15, "el split estratificado no preservó el balance de clases"

    modelos = entrenar_modelos(construir_modelos_base(), X_train, y_train)
    assert set(modelos) == {"regresion_logistica", "random_forest", "gradient_boosting"}

    mejor, params = ajustar_hiperparametros("regresion_logistica", modelos["regresion_logistica"], X_train, y_train, n_iter=2, cv=2)
    assert "modelo__C" in params

    metricas = evaluar(mejor, X_test, y_test)
    for clave in ("accuracy", "precision", "recall", "f1", "roc_auc"):
        assert 0.0 <= metricas[clave] <= 1.0, f"{clave} fuera de rango"
    assert metricas["matriz_confusion"].shape == (2, 2)

    with tempfile.TemporaryDirectory() as tmp:
        ruta_tmp = Path(tmp)
        guardar_modelo("test", mejor, ruta=ruta_tmp)
        recargado = cargar_modelo("test", ruta=ruta_tmp)
        np.testing.assert_array_equal(recargado.predict(X_test), mejor.predict(X_test))

    imp_logreg = importancia_global(mejor)
    assert set(imp_logreg.index) == set(PREDICTORES)
    assert (imp_logreg.diff().dropna() <= 0).all(), "importancia_global no quedó ordenada de mayor a menor"

    imp_rf = importancia_global(modelos["random_forest"])
    assert set(imp_rf.index) == set(PREDICTORES)
    assert (imp_rf >= 0).all()

    print("src.modelado: self-check OK")


if __name__ == "__main__":
    _demo()
