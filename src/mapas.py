"""Reconstrucción espacial de predicciones y mapas de error (Parte 2, inciso 9).

Convierte las probabilidades predichas por observación de vuelta a una imagen 2D usando la
posición `fila`/`columna` dentro del raster original (`src/dataset.py`, inciso 1), para
generar mapas de probabilidad y de error comparables con los mapas de cianobacteria de la
Parte I.
"""

import numpy as np
import pandas as pd

# Límites de la escala de 4 niveles del inciso 9.4: muy baja, baja, alta, muy alta.
NIVELES_PROBABILIDAD = [0.0, 0.25, 0.5, 0.75, 1.0]
ETIQUETAS_PROBABILIDAD = ["muy baja", "baja", "alta", "muy alta"]


def probabilidad_por_pixel(modelo, df: pd.DataFrame, predictores: list[str]) -> np.ndarray:
    """Probabilidad de alta presencia de cianobacteria para cada observación (inciso 9.1)."""
    return modelo.predict_proba(df[predictores])[:, 1]


def rejilla_desde_columnas(
    df: pd.DataFrame, valores: np.ndarray, alto: int | None = None, ancho: int | None = None
) -> np.ndarray:
    """Reconstruye una imagen 2D a partir de las columnas `fila`/`columna` y un arreglo de valores.

    Las celdas sin observación válida (píxeles fuera de agua o descartados en la limpieza del
    inciso 1) quedan en NaN, para distinguirlas de un valor real de probabilidad 0.
    """
    if alto is None:
        alto = int(df["fila"].max()) + 1
    if ancho is None:
        ancho = int(df["columna"].max()) + 1
    grilla = np.full((alto, ancho), np.nan, dtype=np.float32)
    grilla[df["fila"].to_numpy(), df["columna"].to_numpy()] = valores
    return grilla


def clasificar_error(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    """Clasifica cada observación en VP, FP, FN o VN (inciso 9.6)."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    resultado = np.full(len(y_true), "", dtype=object)
    resultado[(y_true == 1) & (y_pred == 1)] = "VP"
    resultado[(y_true == 0) & (y_pred == 1)] = "FP"
    resultado[(y_true == 1) & (y_pred == 0)] = "FN"
    resultado[(y_true == 0) & (y_pred == 0)] = "VN"
    return resultado


def _demo():
    """Self-check: reconstrucción de rejilla, NaN fuera de las observaciones, y clasificación de error."""
    df = pd.DataFrame({"fila": [0, 0, 1, 2], "columna": [0, 1, 1, 0]})
    valores = np.array([0.1, 0.9, 0.4, 0.6])
    grilla = rejilla_desde_columnas(df, valores)
    assert grilla.shape == (3, 2)
    np.testing.assert_allclose(grilla[0, 0], 0.1)
    np.testing.assert_allclose(grilla[0, 1], 0.9)
    assert np.isnan(grilla[1, 0]), "una celda sin observación debería quedar en NaN"

    y_true = np.array([1, 0, 1, 0])
    y_pred = np.array([1, 0, 0, 1])
    etiquetas = clasificar_error(y_true, y_pred)
    assert list(etiquetas) == ["VP", "VN", "FN", "FP"]

    print("src.mapas: self-check OK")


if __name__ == "__main__":
    _demo()
