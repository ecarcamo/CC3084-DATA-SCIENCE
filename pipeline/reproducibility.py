import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from pipeline.config import load_config

SCORES = ("procedure", "baseline")
METRIC_KEYS = ("mae", "rmse", "mape_pct")


def compare_runs(first_dir, second_dir, config):
    tolerance = config["reproducibility"]["relative_tolerance"]
    first_estimates, first_metrics = _read_outputs(first_dir, config)
    second_estimates, second_metrics = _read_outputs(second_dir, config)
    differences = []
    if first_estimates["period"].tolist() != second_estimates["period"].tolist():
        differences.append("Los períodos estimados no coinciden.")
    if first_metrics["evaluated_periods"] != second_metrics["evaluated_periods"]:
        differences.append("Los meses evaluados no coinciden.")
    pairs = [
        (f"value {period}", first, second)
        for period, first, second in zip(
            first_estimates["period"], first_estimates["value"], second_estimates["value"]
        )
    ]
    pairs += [
        (f"{score}.{key}", first_metrics[score][key], second_metrics[score][key])
        for score in SCORES
        for key in METRIC_KEYS
    ]
    max_relative = 0.0
    for label, first, second in pairs:
        if pd.isna(first) or pd.isna(second):
            if not (pd.isna(first) and pd.isna(second)):
                differences.append(f"{label}: {first} frente a {second}.")
            continue
        relative = abs(first - second) / max(abs(first), abs(second)) if first != second else 0.0
        max_relative = max(max_relative, float(relative))
        if relative > tolerance:
            differences.append(f"{label}: {first} frente a {second}.")
    return {
        "reproducible": not differences,
        "relative_tolerance": tolerance,
        "max_relative_difference": max_relative,
        "differences": differences,
    }


def _read_outputs(folder, config):
    folder = Path(folder)
    estimates = pd.read_csv(folder / config["outputs"]["estimates_file"])
    metrics = json.loads((folder / "metrics.json").read_text(encoding="utf-8"))
    return estimates, metrics


def main(argv=None):
    parser = argparse.ArgumentParser(description="Comparar las estimaciones y métricas de dos ejecuciones.")
    parser.add_argument("first", help="Carpeta candidata de la primera ejecución.")
    parser.add_argument("second", help="Carpeta candidata de la segunda ejecución.")
    parser.add_argument("--config", required=True, help="Ruta del archivo de configuración YAML.")
    args = parser.parse_args(argv)
    result = compare_runs(args.first, args.second, load_config(args.config))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["reproducible"] else 1


if __name__ == "__main__":
    sys.exit(main())
