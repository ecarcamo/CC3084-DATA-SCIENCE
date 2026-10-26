import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app import data, model_results

OUTPUT = ROOT / "docs" / "entregables" / "01_diego_validacion.json"


def profile_monthly(path, value_column):
    raw = pd.read_csv(path)
    dates = pd.to_datetime(raw["fecha"], errors="coerce")
    values = pd.to_numeric(raw[value_column], errors="coerce")
    valid_dates = pd.DatetimeIndex(dates.dropna())
    expected = pd.date_range(valid_dates.min(), valid_dates.max(), freq="MS") if len(valid_dates) else []
    return {
        "file": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "columns": raw.columns.tolist(),
        "rows": len(raw),
        "first_date": valid_dates.min().strftime("%Y-%m-%d") if len(valid_dates) else None,
        "last_date": valid_dates.max().strftime("%Y-%m-%d") if len(valid_dates) else None,
        "invalid_dates": int(dates.isna().sum()),
        "duplicate_dates": int(dates.duplicated().sum()),
        "non_month_start_dates": int((dates.notna() & ~dates.dt.is_month_start).sum()),
        "absent_months": int(len(pd.DatetimeIndex(expected).difference(valid_dates))),
        "missing_values": int(raw[value_column].isna().sum()),
        "non_numeric_values": int((raw[value_column].notna() & values.isna()).sum()),
        "infinite_values": int(np.isinf(values).sum()),
        "zero_values": int((values == 0).sum()),
    }


def build_audit():
    labels = data.load_labels()
    metrics = model_results.load_metrics()
    files = []
    coverage = []
    differences = []
    for series_key in labels.index:
        files.append(profile_monthly(data.SERIES_DIR / f"serie_{series_key}.csv", "viajeros"))
        keys = model_results.available_models(series_key)
        for model_key in keys:
            files.append(profile_monthly(model_results.PREDICTIONS_DIR / f"{series_key}_{model_key}.csv", "prediccion"))
        aligned = model_results.align_models(series_key, keys)
        calculated = model_results.calculate_errors(series_key, keys)
        coverage.append({
            "series": series_key,
            "models": keys,
            "observed_rows": len(model_results.load_observations(series_key)),
            "common_rows": len(aligned),
            "observed_rows_outside_comparison": len(model_results.load_observations(series_key)) - len(aligned),
            "first_common_date": aligned.index.min().strftime("%Y-%m-%d") if len(aligned) else None,
            "last_common_date": aligned.index.max().strftime("%Y-%m-%d") if len(aligned) else None,
            "zero_observations_in_comparison": int((aligned["observed"] == 0).sum()),
        })
        for model_key, row in calculated.iterrows():
            stored = metrics.loc[(metrics["serie"] == series_key) & (metrics["modelo"] == model_key)]
            entry = {"series": series_key, "model": model_key, "common_rows": int(row["count"])}
            for metric in ["mae", "rmse", "mape"]:
                current = float(row[metric])
                original = float(stored.iloc[0][metric]) if len(stored) == 1 else float("nan")
                entry[metric] = current if math.isfinite(current) else None
                entry[f"stored_{metric}"] = original if math.isfinite(original) else None
                entry[f"matches_stored_{metric}"] = math.isclose(current, original, rel_tol=1e-9, abs_tol=1e-8)
            differences.append(entry)
    invalid_fields = [
        "invalid_dates", "duplicate_dates", "non_month_start_dates", "absent_months",
        "missing_values", "non_numeric_values", "infinite_values",
    ]
    sample = model_results.align_observations("total", "ses").iloc[0]
    report = {
        "grain": "Una observación mensual por serie; una predicción mensual por serie y modelo.",
        "files": files,
        "coverage": coverage,
        "metrics_file": {
            "file": model_results.METRICS_FILE.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(model_results.METRICS_FILE.read_bytes()).hexdigest(),
            "rows": len(metrics),
            "columns": metrics.columns.tolist(),
            "duplicate_series_model": int(metrics.duplicated(["serie", "modelo"]).sum()),
            "missing_error_values": int(metrics[["mae", "rmse", "mape"]].isna().sum().sum()),
        },
        "recalculated_metrics": differences,
        "example": {
            "series": "total", "model": "ses", "date": sample.name.strftime("%Y-%m-%d"),
            "observed": float(sample["observed"]), "predicted": float(sample["predicted"]),
            "error_observed_minus_predicted": float(sample["error"]),
        },
        "checks": {
            "monthly_files_profiled": len(files),
            "data_issues": int(sum(row[column] for row in files for column in invalid_fields)),
            "all_series_have_at_least_three_models": all(len(row["models"]) >= 3 and row["common_rows"] > 0 for row in coverage),
            "stored_metric_mismatches": sum(not row[f"matches_stored_{metric}"] for row in differences for metric in ["mae", "rmse", "mape"]),
        },
        "limitations": [
            "Las fuentes no documentan aquí la separación entre entrenamiento y evaluación independiente.",
            "Las fechas coincidentes permiten una comparación histórica, no una garantía de precisión futura.",
            "AIC, BIC y order no se utilizan para comparar los cinco modelos; sus campos vacíos no se rellenan.",
            "La validación comprueba los CSV del repositorio, no su procedencia externa ni una explicación causal.",
        ],
    }
    return report


if __name__ == "__main__":
    report = build_audit()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report["checks"], ensure_ascii=False))
    print(json.dumps(report["example"], ensure_ascii=False))
    print(OUTPUT)
