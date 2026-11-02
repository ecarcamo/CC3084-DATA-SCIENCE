import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

FITTED_PARAMETERS = (
    "smoothing_level",
    "smoothing_trend",
    "smoothing_seasonal",
    "damping_trend",
    "initial_level",
    "initial_trend",
    "initial_seasons",
)


def fit_and_forecast(series, config):
    """Ajusta el procedimiento configurado y estima los meses futuros.

    Entrada: `series` es la serie mensual de `prepare_series`, con `DatetimeIndex` de frecuencia `MS`
    y meses sin cobertura como `NaN`; `config` es la configuración con rutas resueltas. El ajuste usa
    los meses desde `periods.fit_start` hasta `periods.expected_last_period` y `model.seed`.

    Salida: DataFrame con las columnas `period` y `value`, una fila por mes entre
    `periods.forecast_start` y `periods.forecast_end`, en orden. `period` usa el formato `AAAA-MM` y
    `value` es un número finito. `run.py` completa las demás columnas de `outputs.estimate_columns`
    y asigna `kind="estimado"`.
    """
    periods = config["periods"]
    last = pd.Timestamp(periods["expected_last_period"])
    forecast_index = pd.date_range(periods["forecast_start"], periods["forecast_end"], freq="MS")
    steps = len(pd.date_range(last, forecast_index[-1], freq="MS")) - 1
    values = fit_model(series, config, last).forecast(steps).loc[forecast_index]
    return pd.DataFrame({"period": forecast_index.strftime("%Y-%m"), "value": values.to_numpy()})


def model_parameters(series, config):
    """Devuelve los parámetros necesarios para reproducir el ajuste.

    Entrada: las mismas `series` y `config` de `fit_and_forecast`.

    Salida: diccionario serializable en JSON con, como mínimo, `procedure`, `procedure_version`,
    `fit_start`, `fit_end`, `seed` y los parámetros ajustados del modelo. Se guarda en `run.json`
    bajo `model_parameters` y se registra en MLflow.
    """
    model = config["model"]
    periods = config["periods"]
    fitted = fit_model(series, config, periods["expected_last_period"])
    return {
        "procedure": model["procedure"],
        "procedure_version": model["procedure_version"],
        "fit_start": str(periods["fit_start"]),
        "fit_end": str(periods["expected_last_period"]),
        "seed": model["seed"],
        "trend": model["trend"],
        "damped_trend": model["damped_trend"],
        "seasonal": model["seasonal"],
        "seasonal_periods": model["seasonal_periods"],
        "initialization_method": model["initialization_method"],
        "fitted": {name: np.asarray(fitted.params[name], dtype=float).tolist() for name in FITTED_PARAMETERS},
    }


def fit_model(series, config, last_period):
    model = config["model"]
    window = series.reindex(pd.date_range(config["periods"]["fit_start"], last_period, freq="MS"))
    if window.isna().any():
        missing = ", ".join(window.index[window.isna()].strftime("%Y-%m"))
        raise ValueError(f"Faltan valores en el período de ajuste: {missing}.")
    np.random.seed(model["seed"])
    return ExponentialSmoothing(
        window,
        trend=model["trend"],
        damped_trend=model["damped_trend"],
        seasonal=model["seasonal"],
        seasonal_periods=model["seasonal_periods"],
        initialization_method=model["initialization_method"],
    ).fit()
