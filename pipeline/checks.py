import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pandas.api import types

OK = "ok"
WARNING = "warning"
STOP = "stop"
MAX_EXAMPLES = 5

TYPE_VALIDATORS = {
    "integer": lambda column: types.is_integer_dtype(column) and not types.is_bool_dtype(column),
    "number": lambda column: types.is_numeric_dtype(column) and not types.is_bool_dtype(column),
    "string": types.is_string_dtype,
}


@dataclass
class CheckResult:
    name: str
    status: str
    message: str
    details: dict = field(default_factory=dict)


def check_columns_and_types(df, config):
    source = config["source"]
    missing = [column for column in source["required_columns"] if column not in df.columns]
    incompatible = {
        column: {"expected": expected, "found": str(df[column].dtype)}
        for column, expected in source["required_columns"].items()
        if column in df.columns and not _is_compatible(df[column], expected)
    }
    missing_optional = [column for column in source["optional_columns"] if column not in df.columns]
    details = {
        "missing_required": missing,
        "incompatible_types": incompatible,
        "missing_optional": missing_optional,
    }
    name = "check_columns_and_types"
    if missing or incompatible:
        return CheckResult(name, STOP, "Faltan columnas indispensables o tienen un tipo incompatible.", details)
    if missing_optional:
        return CheckResult(name, WARNING, "Faltan columnas opcionales; el flujo continúa.", details)
    return CheckResult(name, OK, "Las columnas indispensables están presentes y con tipos compatibles.", details)


def check_dates_and_coverage(df, config):
    name = "check_dates_and_coverage"
    invalid = df.loc[~df["Mes cod"].between(1, 12), ["Año", "Mes cod"]]
    if not invalid.empty:
        details = {"invalid_rows": len(invalid), "examples": _records(invalid)}
        return CheckResult(name, STOP, "Hay fechas inválidas: el mes debe estar entre 1 y 12.", details)

    periods = config["periods"]
    quality = config["quality"]
    fit_start = pd.Period(periods["fit_start"], freq="M")
    expected_last = pd.Period(periods["expected_last_period"], freq="M")
    present = _target_periods(df, config)
    last = max(present) if present else None
    missing_in_fit = _missing_periods(present, fit_start, expected_last)
    missing_before_fit = _missing_periods(present, pd.Period(periods["source_start"], freq="M"), fit_start - 1)
    details = {
        "first_period": str(min(present)) if present else None,
        "last_period": str(last) if last else None,
        "expected_last_period": str(expected_last),
        "missing_in_fit": missing_in_fit,
        "missing_before_fit": missing_before_fit,
    }

    stop_reasons = []
    warning_reasons = []
    if last is None or last < expected_last:
        stop_reasons.append(f"La fuente no llega a {expected_last}.")
    if missing_in_fit:
        reason = f"Faltan {len(missing_in_fit)} meses dentro del período de ajuste."
        (stop_reasons if quality["stop_on_missing_months_in_fit"] else warning_reasons).append(reason)
    if missing_before_fit and quality["warn_missing_months_before_fit"]:
        warning_reasons.append(f"Faltan {len(missing_before_fit)} meses antes de {fit_start}.")

    if stop_reasons:
        return CheckResult(name, STOP, " ".join(stop_reasons + warning_reasons), details)
    if warning_reasons:
        return CheckResult(name, WARNING, " ".join(warning_reasons), details)
    return CheckResult(name, OK, "Las fechas son válidas y la cobertura mensual está completa.", details)


def check_uniqueness(df, config):
    key = config["source"]["unique_key"]
    repeated = df.loc[df.duplicated(subset=key, keep=False), key]
    keys = repeated.drop_duplicates()
    details = {
        "duplicated_keys": len(keys),
        "duplicated_rows": len(repeated),
        "examples": _records(keys),
    }
    name = "check_uniqueness"
    if keys.empty:
        return CheckResult(name, OK, "No hay filas repetidas según la clave única.", details)
    status = STOP if config["quality"]["stop_on_duplicate_key"] else WARNING
    return CheckResult(name, status, f"Hay {len(keys)} claves repetidas.", details)


CHECKS = (check_columns_and_types, check_dates_and_coverage, check_uniqueness)


def run_checks(df, config):
    results = []
    for check in CHECKS:
        result = check(df, config)
        results.append(result)
        if result.status == STOP:
            break
    return results


def has_stop(results):
    return any(result.status == STOP for result in results)


def overall_status(results):
    statuses = {result.status for result in results}
    return next((status for status in (STOP, WARNING) if status in statuses), OK)


def serialize_results(results):
    return [asdict(result) for result in results]


def write_quality_report(results, path, run_id):
    report = {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": overall_status(results),
        "checks": serialize_results(results),
    }
    Path(path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _is_compatible(column, expected):
    validator = TYPE_VALIDATORS.get(expected)
    return validator is not None and validator(column)


def _target_periods(df, config):
    target = df.loc[df["Tipo de Viajero"].isin(config["target"]["visitor_types"])]
    dates = pd.to_datetime({"year": target["Año"], "month": target["Mes cod"], "day": 1})
    return set(dates.dt.to_period("M"))


def _missing_periods(present, start, end):
    if start > end:
        return []
    return [str(period) for period in pd.period_range(start, end, freq="M") if period not in present]


def _records(frame):
    return json.loads(frame.head(MAX_EXAMPLES).to_json(orient="records", force_ascii=False))
