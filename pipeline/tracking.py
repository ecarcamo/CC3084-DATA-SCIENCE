import json
import subprocess
import time
from pathlib import Path

from mlflow.entities import Metric, Param, RunTag
from mlflow.tracking import MlflowClient

from pipeline.config import ROOT

SQLITE_PREFIX = "sqlite:///"
RUN_STATUS = {"completed": "FINISHED", "failed": "FAILED"}
UNKNOWN = "desconocido"
MAX_TAG_LENGTH = 5000
PERIOD_KEYS = (
    "fit_start",
    "expected_last_period",
    "evaluation_start",
    "evaluation_end",
    "forecast_start",
    "forecast_end",
)


def log_run(metadata, config, artifacts_dir):
    """Registra una ejecución en MLflow Tracking.

    Entrada: `metadata` es el contenido de `run.json`; `config` contiene la sección `mlflow`;
    `artifacts_dir` es la carpeta candidata con los archivos generados hasta el momento.

    Salida: identificador del run de MLflow. Registra el estado, el commit de Git, la huella de la
    fuente, los períodos, los parámetros, los controles y los archivos existentes. Si
    `metadata["metrics"]` es `None`, la ejecución se detuvo antes de la evaluación y no registra
    métricas; registra la causa desde `metadata["errors"]`.
    """
    settings = config["mlflow"]
    _prepare_store(settings)
    client = MlflowClient(tracking_uri=settings["tracking_uri"])
    run_id = client.create_run(_experiment_id(client, settings), run_name=metadata["run_id"]).info.run_id
    status = "FAILED"
    try:
        client.log_batch(
            run_id,
            metrics=_metrics(metadata["metrics"]),
            params=_params(metadata, config),
            tags=_tags(metadata),
        )
        client.log_artifacts(run_id, str(artifacts_dir))
        client.log_artifact(run_id, metadata["config_path"])
        status = RUN_STATUS.get(metadata["status"], "FAILED")
    finally:
        client.set_terminated(run_id, status)
    return run_id


def _prepare_store(settings):
    uri = settings["tracking_uri"]
    if uri.startswith(SQLITE_PREFIX):
        Path(uri.removeprefix(SQLITE_PREFIX)).parent.mkdir(parents=True, exist_ok=True)


def _experiment_id(client, settings):
    experiment = client.get_experiment_by_name(settings["experiment_name"])
    if experiment is not None:
        return experiment.experiment_id
    artifact_root = Path(settings["artifact_root"])
    artifact_root.mkdir(parents=True, exist_ok=True)
    return client.create_experiment(settings["experiment_name"], artifact_location=artifact_root.as_uri())


def _metrics(metrics):
    if metrics is None:
        return []
    timestamp = int(time.time() * 1000)
    values = {
        key: value for key, value in _flatten(metrics).items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }
    values["evaluated_periods"] = len(metrics["evaluated_periods"])
    return [Metric(key, float(value), timestamp, 0) for key, value in values.items()]


def _params(metadata, config):
    periods = config["periods"]
    values = {
        "source_path": _relative(config["source"]["path"]),
        "source_fingerprint": metadata["source_fingerprint"],
        **{f"periods.{key}": periods[key] for key in PERIOD_KEYS},
        **_flatten(metadata["model_parameters"] or {}, "model"),
    }
    if metadata["metrics"] is not None:
        values["evaluated_periods"] = metadata["metrics"]["evaluated_periods"]
    return [
        Param(key, json.dumps(value) if isinstance(value, list) else str(value))
        for key, value in values.items()
        if value is not None
    ]


def _tags(metadata):
    commit, dirty = _git_state()
    tags = {
        "pipeline_run_id": metadata["run_id"],
        "started_at": metadata["started_at"],
        "finished_at": metadata["finished_at"],
        "status": metadata["status"],
        "publication": metadata["publication"],
        "checks_status": metadata["checks_status"],
        "git_commit": commit,
        "git_dirty": dirty,
        **{f"check.{check['name']}": check["status"] for check in metadata["checks"]},
        **{f"monitor.{check['name']}": check["status"] for check in metadata["monitoring"]},
    }
    if metadata["acceptance"] is not None:
        tags["accepted"] = metadata["acceptance"]["accepted"]
    if metadata["errors"]:
        tags["error"] = " | ".join(metadata["errors"])[:MAX_TAG_LENGTH]
    return [RunTag(key, str(value)) for key, value in tags.items()]


def _git_state():
    commit = _git("rev-parse", "HEAD")
    changes = _git("status", "--porcelain", "--untracked-files=no")
    return commit or UNKNOWN, UNKNOWN if changes is None else str(bool(changes)).lower()


def _git(*args):
    try:
        result = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip()


def _flatten(values, prefix=""):
    flat = {}
    for key, value in values.items():
        name = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten(value, name))
        else:
            flat[name] = value
    return flat


def _relative(path):
    path = Path(path)
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
