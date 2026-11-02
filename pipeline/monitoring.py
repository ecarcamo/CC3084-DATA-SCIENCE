import json
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.checks import OK, WARNING, CheckResult, serialize_results

QUALITY_MEASURES = {
    "missing_values": ("max_missing_rows_increase", "valores faltantes"),
    "duplicate_rows": ("max_duplicate_rows_increase", "filas duplicadas"),
    "missing_months": ("max_missing_months_increase", "meses sin datos"),
}


def run_monitoring(series, estimates, checks, previous_approved_dir, config):
    """Ejecuta las verificaciones de actualización, calidad y resultados.

    Entrada: `series` es la serie mensual de `prepare_series`; `estimates` es el DataFrame de
    `estimates.csv`; `checks` es la lista de `CheckResult` de `run_checks`; `previous_approved_dir` es
    la carpeta de la versión aprobada vigente, que puede no existir; `config` contiene `monitoring`,
    `periods` y `baseline`.

    Salida: lista de `pipeline.checks.CheckResult` con estado `ok` o `warning`. El monitoreo genera
    alertas para revisión y no usa `stop`. Se guarda en `run.json` bajo `monitoring`.
    """
    return [
        check_freshness(series, estimates, config),
        check_quality_drift(checks, previous_approved_dir, config),
        check_results(series, estimates, config),
    ]


def check_freshness(series, estimates, config):
    periods = config["periods"]
    observed = series.dropna()
    last_observed = observed.index.max().strftime("%Y-%m") if not observed.empty else None
    expected_last = str(periods["expected_last_period"])
    expected_forecast = pd.period_range(periods["forecast_start"], periods["forecast_end"], freq="M").astype(str)
    found = estimates["period"].astype(str).tolist()
    missing = [period for period in expected_forecast if period not in found]
    details = {
        "last_observed": last_observed,
        "expected_last_period": expected_last,
        "last_estimate": found[-1] if found else None,
        "missing_estimates": missing,
    }
    reasons = []
    if last_observed != expected_last:
        reasons.append(f"La serie llega a {last_observed} y se esperaba {expected_last}.")
    if missing:
        reasons.append(f"Faltan estimaciones para {', '.join(missing)}.")
    name = "monitor_freshness"
    if reasons:
        return CheckResult(name, WARNING, " ".join(reasons), details)
    return CheckResult(name, OK, "La serie y las estimaciones llegan a los períodos esperados.", details)


def check_quality_drift(checks, previous_approved_dir, config):
    name = "monitor_quality"
    current = _quality_counts(serialize_results(checks))
    report_file = config["outputs"]["quality_report_file"]
    if previous_approved_dir is None or not (report := Path(previous_approved_dir) / report_file).is_file():
        message = "No hay versión aprobada anterior; la calidad no se compara."
        return CheckResult(name, OK, message, {"current": current})
    previous = _quality_counts(json.loads(report.read_text(encoding="utf-8"))["checks"])
    increases = {
        key: current[key] - previous[key]
        for key in QUALITY_MEASURES
        if current[key] is not None and previous[key] is not None
    }
    limits = config["monitoring"]
    exceeded = [
        QUALITY_MEASURES[key][1] for key, increase in increases.items()
        if increase > limits[QUALITY_MEASURES[key][0]]
    ]
    details = {"current": current, "previous": previous, "increases": increases}
    if exceeded:
        message = f"La calidad empeoró frente a la versión aprobada en: {', '.join(exceeded)}."
        return CheckResult(name, WARNING, message, details)
    if not increases:
        return CheckResult(name, OK, "La versión aprobada no tiene datos de calidad comparables.", details)
    return CheckResult(name, OK, "La calidad no empeoró frente a la versión aprobada.", details)


def check_results(series, estimates, config):
    limit = config["monitoring"]["max_abs_year_over_year_change_pct"]
    periods = pd.PeriodIndex(estimates["period"].astype(str), freq="M")
    values = pd.to_numeric(estimates["value"], errors="coerce").to_numpy(dtype=float)
    lagged = periods - config["baseline"]["lag_months"]
    previous = series.reindex(lagged.to_timestamp()).to_numpy(dtype=float)
    invalid = [str(period) for period, value in zip(periods, values) if not np.isfinite(value) or value < 0]
    comparable = np.isfinite(values) & np.isfinite(previous) & (previous != 0)
    large = []
    for period, value, base, valid in zip(periods, values, previous, comparable):
        change = (value - base) / base * 100 if valid else None
        if change is not None and abs(change) > limit:
            large.append({
                "period": str(period),
                "estimate": float(value),
                "previous_year": float(base),
                "change_pct": round(float(change), 2),
            })
    details = {
        "limit_pct": limit,
        "invalid_estimates": invalid,
        "large_changes": large,
        "not_comparable": [str(period) for period, valid in zip(periods, comparable) if not valid],
    }
    reasons = []
    if invalid:
        reasons.append(f"Hay estimaciones negativas o no finitas en {', '.join(invalid)}.")
    if large:
        reasons.append(
            f"{len(large)} estimaciones cambian más de {limit} % frente al mismo mes del año anterior; "
            "revisar antes de usarlas."
        )
    name = "monitor_results"
    if reasons:
        return CheckResult(name, WARNING, " ".join(reasons), details)
    return CheckResult(name, OK, "Las estimaciones son válidas y su variación interanual está en el rango.", details)


def _quality_counts(checks):
    details = {check["name"]: check["details"] for check in checks}
    missing = details.get("check_missing_values")
    uniqueness = details.get("check_uniqueness")
    coverage = details.get("check_dates_and_coverage")
    return {
        "missing_values": sum(missing["missing_blocking"].values()) + sum(missing["missing_allowed"].values())
        if missing else None,
        "duplicate_rows": uniqueness["duplicated_rows"] if uniqueness else None,
        "missing_months": len(coverage["missing_in_fit"]) + len(coverage["missing_before_fit"])
        if coverage else None,
    }
