from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent


def load_config(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    with path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ValueError("La configuración debe contener un mapa YAML.")
    config["source"]["path"] = (ROOT / config["source"]["path"]).resolve()
    for key in ("candidates_dir", "approved_dir", "history_dir", "run_log_dir"):
        config["outputs"][key] = (ROOT / config["outputs"][key]).resolve()
    config["mlflow"]["artifact_root"] = (ROOT / config["mlflow"]["artifact_root"]).resolve()
    tracking_uri = config["mlflow"]["tracking_uri"]
    if tracking_uri.startswith("sqlite:///"):
        database = tracking_uri.removeprefix("sqlite:///")
        config["mlflow"]["tracking_uri"] = f"sqlite:///{(ROOT / database).resolve().as_posix()}"
    return config
