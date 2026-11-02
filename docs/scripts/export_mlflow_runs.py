import argparse
import os
import sys

import mlflow

from pipeline.config import ROOT, load_config

COLUMNS = [
    "run_id",
    "experiment_name",
    "status",
    "start_time",
    "end_time",
    "tags.pipeline_run_id",
    "tags.status",
    "tags.publication",
    "tags.accepted",
    "tags.checks_status",
    "tags.error",
    "tags.git_commit",
    "tags.git_dirty",
    "params.source_path",
    "params.source_fingerprint",
    "metrics.procedure.mae",
    "metrics.procedure.rmse",
    "metrics.procedure.mape_pct",
    "metrics.baseline.mae",
    "metrics.baseline.mape_pct",
    "metrics.evaluated_periods",
]


def export_runs(config, experiment_names, output):
    mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])
    runs = mlflow.search_runs(experiment_names=experiment_names, order_by=["start_time ASC"])
    names = {mlflow.get_experiment_by_name(name).experiment_id: name for name in experiment_names}
    runs["experiment_name"] = runs["experiment_id"].map(names)
    runs = runs.reindex(columns=COLUMNS)
    runs["tags.error"] = runs["tags.error"].str.replace(f"{ROOT}{os.sep}", "", regex=False)
    runs.to_csv(output, index=False)
    return runs


def main(argv=None):
    parser = argparse.ArgumentParser(description="Exportar las ejecuciones registradas en MLflow.")
    parser.add_argument("--config", required=True, help="Ruta del archivo de configuración YAML.")
    parser.add_argument("--experiment", action="append", required=True, help="Nombre de un experimento.")
    parser.add_argument("--output", required=True, help="Archivo CSV de salida.")
    args = parser.parse_args(argv)
    runs = export_runs(load_config(args.config), args.experiment, args.output)
    print(runs[["experiment_name", "status", "tags.publication", "tags.error"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
