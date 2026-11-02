import numpy as np
import pandas as pd

from pipeline.model import fit_model

MAPE_ZERO_RULE = (
    "Los meses con valor observado igual a cero se excluyen del MAPE porque el error porcentual no está "
    "definido; siguen incluidos en MAE y RMSE. Si todos los observados son cero, mape_pct es null."
)


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
        "procedure": {
            "name": config["model"]["procedure"],
            **error_metrics(forecasts["observed"], forecasts["procedure"]),
        },
        "baseline": {
            "name": config["baseline"]["procedure"],
            **error_metrics(forecasts["observed"], forecasts["baseline"]),
        },
        "evaluated_periods": list(forecasts.index),
        "mape_zero_rule": MAPE_ZERO_RULE,
    }


def error_metrics(observed, estimated):
    if observed.empty:
        return {"mae": None, "rmse": None, "mape_pct": None}
    errors = estimated - observed
    nonzero = observed.ne(0)
    mape = float((errors[nonzero].abs() / observed[nonzero]).mean() * 100) if nonzero.any() else None
    return {
        "mae": float(errors.abs().mean()),
        "rmse": float(np.sqrt((errors**2).mean())),
        "mape_pct": mape,
    }


def hidden_month_forecasts(series, config):
    periods = config["periods"]
    horizon = config["model"]["evaluation_horizon"]
    lag = config["baseline"]["lag_months"]
    rows = []
    for month in pd.date_range(periods["evaluation_start"], periods["evaluation_end"], freq="MS"):
        observed = series.get(month)
        last_known = month - pd.DateOffset(months=horizon)
        history = series.loc[:last_known]
        baseline = history.get(month - pd.DateOffset(months=lag))
        if pd.isna(observed) or pd.isna(baseline):
            continue
        estimate = fit_model(history, config, last_known).forecast(horizon).iloc[-1]
        rows.append({
            "period": month.strftime("%Y-%m"),
            "observed": observed,
            "procedure": estimate,
            "baseline": baseline,
        })
    columns = ["period", "observed", "procedure", "baseline"]
    return pd.DataFrame(rows, columns=columns).set_index("period").astype(float)


def accept(checks, estimates, metrics, config):
    """Aplica la regla de aceptación de una versión candidata.

    Entrada: `checks` es la lista de `CheckResult` de `run_checks`; `estimates` es el DataFrame de
    `estimates.csv`; `metrics` es el resultado de `evaluate`; `config` contiene `acceptance`.

    Salida: {"accepted": bool, "reasons": [str, ...]}. `reasons` explica cada criterio incumplido y
    queda vacía cuando la versión se acepta.
    """
    raise NotImplementedError("accept pendiente: persona A")
