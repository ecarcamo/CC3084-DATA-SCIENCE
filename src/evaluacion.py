import numpy as np
import pandas as pd


def metricas(y_real: pd.Series, y_pred: pd.Series) -> dict:
    real = np.asarray(y_real, dtype=float)
    prediccion = np.asarray(y_pred, dtype=float)
    if real.shape != prediccion.shape:
        raise ValueError("Las series real y predicha deben tener igual longitud")

    errores = real - prediccion
    mascara_mape = real != 0
    mape = np.mean(
        np.abs(errores[mascara_mape] / real[mascara_mape])
    ) * 100

    return {
        "mae": np.mean(np.abs(errores)),
        "rmse": np.sqrt(np.mean(errores**2)),
        "mape": mape,
        "mape_excluidos": int((~mascara_mape).sum()),
    }
