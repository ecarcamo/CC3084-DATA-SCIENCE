import numpy as np
import pandas as pd

from app import data

PREDICTIONS_DIR = data.RESULTS_DIR / "predicciones"
METRICS_FILE = data.RESULTS_DIR / "metricas_modelos.csv"
MODEL_LABELS = {
    "sarima": "SARIMA",
    "holt_winters": "Holt-Winters",
    "ses": "Suavizamiento exponencial simple (SES)",
    "seasonal_naive": "Referencia estacional (Seasonal Naive)",
    "prophet": "Prophet",
}
ERROR_COLUMNS = ["mae", "rmse", "mape", "count", "mape_excluded", "start", "end"]


class ModelDataError(ValueError):
    pass


def _check_series(series_key):
    if series_key not in data.load_labels().index:
        raise ModelDataError("Seleccione una serie disponible.")


def _check_model(model_key):
    if model_key not in MODEL_LABELS:
        raise ModelDataError("Seleccione un modelo disponible.")


def _read_monthly(path, value_column, name):
    try:
        frame = pd.read_csv(path)
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
        raise ModelDataError("No se pudieron leer los datos de la selección.") from error
    if not {"fecha", value_column}.issubset(frame.columns):
        raise ModelDataError("La fuente no contiene las columnas necesarias para comparar resultados.")
    dates = pd.to_datetime(frame["fecha"], errors="coerce")
    if dates.isna().any() or not dates.dt.is_month_start.all():
        raise ModelDataError("La fuente contiene fechas mensuales inválidas.")
    if dates.duplicated().any():
        raise ModelDataError("La fuente contiene fechas repetidas; no se puede comparar sin duplicar datos.")
    values = pd.to_numeric(frame[value_column], errors="coerce").astype(float)
    if (frame[value_column].notna() & values.isna()).any() or np.isinf(values).any():
        raise ModelDataError("La fuente contiene valores no numéricos o infinitos.")
    result = pd.Series(values.to_numpy(), index=pd.DatetimeIndex(dates, name="date"), name=name)
    return result.sort_index()


def load_observations(series_key):
    _check_series(series_key)
    return _read_monthly(data.SERIES_DIR / f"serie_{series_key}.csv", "viajeros", "observed")


def load_predictions(series_key, model_key):
    _check_series(series_key)
    _check_model(model_key)
    return _read_monthly(PREDICTIONS_DIR / f"{series_key}_{model_key}.csv", "prediccion", "predicted")


def available_models(series_key):
    _check_series(series_key)
    return [key for key in MODEL_LABELS if (PREDICTIONS_DIR / f"{series_key}_{key}.csv").is_file()]


def load_metrics(series_key=None):
    if series_key is not None:
        _check_series(series_key)
    try:
        frame = pd.read_csv(METRICS_FILE)
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
        raise ModelDataError("No se pudieron leer las métricas existentes.") from error
    if not {"serie", "modelo", "mae", "rmse", "mape"}.issubset(frame.columns):
        raise ModelDataError("Las métricas no contienen las columnas necesarias.")
    if frame[["serie", "modelo"]].isna().any().any() or frame.duplicated(["serie", "modelo"]).any():
        raise ModelDataError("Las métricas tienen combinaciones de serie y modelo ausentes o repetidas.")
    for column in ["mae", "rmse", "mape"]:
        values = pd.to_numeric(frame[column], errors="coerce").astype(float)
        if (frame[column].notna() & values.isna()).any() or np.isinf(values).any() or (values < 0).any():
            raise ModelDataError("Las métricas contienen errores numéricos inválidos.")
        frame[column] = values
    return frame.copy() if series_key is None else frame.loc[frame["serie"] == series_key].copy()


def _slice_dates(frame, start, end):
    try:
        first = pd.Timestamp(start) if start is not None else None
        last = pd.Timestamp(end) if end is not None else None
        if (first is not None and pd.isna(first)) or (last is not None and pd.isna(last)):
            raise ValueError
        if first is not None and last is not None and first > last:
            raise ModelDataError("La fecha inicial debe ser anterior o igual a la fecha final.")
        return frame.loc[first:last]
    except (ValueError, TypeError) as error:
        if isinstance(error, ModelDataError):
            raise
        raise ModelDataError("Seleccione un rango de fechas válido.") from error


def align_models(series_key, model_keys=None, start=None, end=None):
    keys = available_models(series_key) if model_keys is None else list(dict.fromkeys(model_keys))
    if not keys:
        raise ModelDataError("No hay modelos seleccionados con resultados disponibles.")
    observed = load_observations(series_key)
    sources = [observed]
    for key in keys:
        sources.append(load_predictions(series_key, key).rename(key))
    frame = pd.concat(sources, axis=1, join="inner").dropna().sort_index()
    frame = _slice_dates(frame, start, end).copy()
    frame.attrs["models"] = keys
    frame.attrs["observed_rows"] = int(observed.notna().sum())
    return frame


def align_observations(series_key, model_key, start=None, end=None):
    _check_model(model_key)
    frame = align_models(series_key, [model_key], start, end).rename(columns={model_key: "predicted"})
    frame["error"] = frame["observed"] - frame["predicted"]
    return frame


def calculate_errors(series_key, model_keys=None, start=None, end=None):
    frame = align_models(series_key, model_keys, start, end)
    if frame.empty:
        return pd.DataFrame(columns=ERROR_COLUMNS, index=pd.Index([], name="model"))
    percentage_rows = frame["observed"] != 0
    records = []
    for key in frame.attrs["models"]:
        error = frame["observed"] - frame[key]
        mape = float((error[percentage_rows] / frame.loc[percentage_rows, "observed"]).abs().mean() * 100)
        records.append({
            "model": key,
            "mae": float(error.abs().mean()),
            "rmse": float(np.sqrt(np.mean(np.square(error.to_numpy())))),
            "mape": mape,
            "count": len(frame),
            "mape_excluded": int((~percentage_rows).sum()),
            "start": frame.index.min(),
            "end": frame.index.max(),
        })
    return pd.DataFrame(records).set_index("model")[ERROR_COLUMNS]
