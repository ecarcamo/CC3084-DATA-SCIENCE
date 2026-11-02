import numpy as np
import pandas as pd

from pipeline.checks import STOP
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
    stopped = [result.name for result in checks if result.status == STOP]
    reasons = [f"Controles de calidad con estado stop: {', '.join(stopped)}."] if stopped else []
    reasons += _output_reasons(estimates, config)
    reasons += _forecast_reasons(estimates, config)
    reasons += _performance_reasons(metrics, config["acceptance"])
    return {"accepted": not reasons, "reasons": reasons}


def _output_reasons(estimates, config):
    columns = config["outputs"]["estimate_columns"]
    missing = [column for column in columns if column not in estimates.columns]
    empty = [
        column for column in columns
        if column in estimates.columns
        and (estimates[column].isna() | estimates[column].astype(str).str.strip().eq("")).any()
    ]
    reasons = []
    if missing:
        reasons.append(f"Faltan columnas en las estimaciones: {', '.join(missing)}.")
    if empty:
        reasons.append(f"Hay valores vacíos en las columnas: {', '.join(empty)}.")
    return reasons


def _forecast_reasons(estimates, config):
    periods = config["periods"]
    acceptance = config["acceptance"]
    expected_months = acceptance["expected_forecast_months"]
    expected = list(pd.period_range(periods["forecast_start"], periods["forecast_end"], freq="M").astype(str))
    found = estimates["period"].astype(str).tolist() if "period" in estimates.columns else []
    missing = [period for period in expected if period not in found]
    reasons = []
    if missing or len(found) != expected_months:
        reasons.append(
            f"Se esperaban {expected_months} meses de pronóstico de {expected[0]} a {expected[-1]} y hay "
            f"{len(found)}; faltan: {', '.join(missing) or 'ninguno'}."
        )
    if "value" not in estimates.columns:
        return reasons
    values = pd.to_numeric(estimates["value"], errors="coerce")
    if acceptance["require_finite_estimates"] and not np.isfinite(values).all():
        reasons.append("Hay estimaciones vacías o no finitas.")
    if acceptance["require_non_negative_estimates"] and values.lt(0).any():
        reasons.append("Hay estimaciones negativas.")
    return reasons


def _performance_reasons(metrics, acceptance):
    procedure = metrics["procedure"]
    baseline_mae = metrics["baseline"]["mae"]
    max_mape = acceptance["max_mape_pct"]
    max_ratio = acceptance["max_mae_ratio_to_baseline"]
    reasons = []
    if procedure["mape_pct"] is None:
        reasons.append("No hay MAPE del procedimiento para comparar con el umbral.")
    elif procedure["mape_pct"] > max_mape:
        reasons.append(f"El MAPE es {procedure['mape_pct']:.2f} %, mayor que el máximo de {max_mape} %.")
    if procedure["mae"] is None or not baseline_mae:
        reasons.append("No se puede calcular la razón de MAE frente a la referencia.")
    elif (ratio := procedure["mae"] / baseline_mae) > max_ratio:
        reasons.append(f"La razón de MAE frente a la referencia es {ratio:.2f}, mayor que el máximo de {max_ratio}.")
    return reasons
