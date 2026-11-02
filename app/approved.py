import json
import os
from pathlib import Path

import pandas as pd

from pipeline.config import load_config

APPROVED_DIR_VARIABLE = "APPROVED_DIR"
CONFIG_FILE = "config/pipeline.yaml"


def approved_dir():
    configured = os.environ.get(APPROVED_DIR_VARIABLE)
    if configured:
        return Path(configured)
    return load_config(CONFIG_FILE)["outputs"]["approved_dir"]


def load_approved(path=None):
    """Lee la versión aprobada vigente que consulta el tablero.

    Entrada: `path` es la carpeta de la versión aprobada. Si se omite, se usa la variable de entorno
    `APPROVED_DIR` y, en su ausencia, `outputs.approved_dir` de `config/pipeline.yaml`.

    Salida: `None` si la carpeta o `estimates.csv` no existen. En otro caso, un diccionario con
    `estimates` y `observed` como DataFrame y `metrics`, `quality_report` y `run` como diccionarios.
    """
    folder = Path(path) if path is not None else approved_dir()
    if not (folder / "estimates.csv").is_file():
        return None
    return {
        "estimates": pd.read_csv(folder / "estimates.csv"),
        "observed": pd.read_csv(folder / "observed.csv"),
        "metrics": _read_json(folder / "metrics.json"),
        "quality_report": _read_json(folder / "quality_report.json"),
        "run": _read_json(folder / "run.json"),
    }


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
