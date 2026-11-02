import pandas as pd

from pipeline.model import fit_model


def evaluate(series, config):
    """Evalúa el procedimiento y la referencia sobre los mismos meses ocultos.

    Entrada: `series` es la serie mensual de `prepare_series`; `config` es la configuración con rutas
    resueltas. Cada mes entre `periods.evaluation_start` y `periods.evaluation_end` se estima solo con
    información anterior a ese mes. Los meses sin valor observado no se evalúan.

    Salida: diccionario serializable en JSON con estas claves:
        procedure: {"name": str, "mae": float, "rmse": float, "mape_pct": float | None}
        baseline: {"name": str, "mae": float, "rmse": float, "mape_pct": float | None}
        evaluated_periods: lista de períodos `AAAA-MM` evaluados
        mape_zero_rule: texto que explica cómo se tratan los observados iguales a cero
    Se guarda como `metrics.json`.
    """
    forecasts = hidden_month_forecasts(series, config)
    return {
        "procedure": {"name": config["model"]["procedure"]},
        "evaluated_periods": list(forecasts.index),
    }


def hidden_month_forecasts(series, config):
    periods = config["periods"]
    horizon = config["model"]["evaluation_horizon"]
    rows = []
    for month in pd.date_range(periods["evaluation_start"], periods["evaluation_end"], freq="MS"):
        observed = series.get(month)
        if pd.isna(observed):
            continue
        last_known = month - pd.DateOffset(months=horizon)
        history = series.loc[:last_known]
        estimate = fit_model(history, config, last_known).forecast(horizon).iloc[-1]
        rows.append({"period": month.strftime("%Y-%m"), "observed": observed, "procedure": estimate})
    return pd.DataFrame(rows, columns=["period", "observed", "procedure"]).set_index("period").astype(float)


def accept(checks, estimates, metrics, config):
    """Aplica la regla de aceptación de una versión candidata.

    Entrada: `checks` es la lista de `CheckResult` de `run_checks`; `estimates` es el DataFrame de
    `estimates.csv`; `metrics` es el resultado de `evaluate`; `config` contiene `acceptance`.

    Salida: {"accepted": bool, "reasons": [str, ...]}. `reasons` explica cada criterio incumplido y
    queda vacía cuando la versión se acepta.
    """
    raise NotImplementedError("accept pendiente: persona A")
