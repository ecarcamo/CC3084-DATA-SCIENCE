import argparse
import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

from pipeline.config import load_config

VERSION_FILES = ("estimates.csv", "observed.csv", "metrics.json", "quality_report.json", "run.json")


def publish(candidate_dir, config):
    """Instala una versión candidata aceptada como versión aprobada.

    Entrada: `candidate_dir` contiene `estimates.csv`, `observed.csv`, `metrics.json`,
    `quality_report.json` y `run.json`; `config` contiene `outputs.approved_dir` y
    `outputs.history_dir`.

    Salida: identificador de la versión instalada, igual al `run_id` del candidato. La versión vigente
    se copia a `history_dir/<run_id>/` antes de reemplazarla. Si algo falla, `approved_dir` conserva la
    versión anterior completa.
    """
    return _install(Path(candidate_dir), config)


def latest_approved(config):
    """Devuelve la carpeta de la versión aprobada vigente o `None` si todavía no existe."""
    folder = Path(config["outputs"]["approved_dir"])
    return folder if not _missing_files(folder) else None


def restore(version_id, config):
    """Reinstala una versión del historial como versión aprobada vigente.

    Entrada: `version_id` es el nombre de una carpeta en `outputs.history_dir`; `config` contiene las
    rutas de salida.

    Salida: identificador de la versión restaurada. La versión vigente pasa al historial antes del
    reemplazo.
    """
    history = Path(config["outputs"]["history_dir"])
    source = history / str(version_id)
    if source.resolve().parent != history.resolve() or not source.is_dir():
        raise ValueError(f"No existe la versión {version_id} en {history}.")
    return _install(source, config)


def _install(source, config):
    missing = _missing_files(source)
    if missing:
        raise FileNotFoundError(f"La versión en {source} no contiene: {', '.join(missing)}.")
    run_id = _run_id(source)
    approved = Path(config["outputs"]["approved_dir"])
    current = latest_approved(config)
    if approved.exists() and current is None:
        raise ValueError(f"La versión aprobada en {approved} está incompleta; revísela antes de reemplazarla.")
    staged = _stage(source, approved)
    try:
        if current is None:
            staged.rename(approved)
            return run_id
        _archive(current, Path(config["outputs"]["history_dir"]))
        retired = approved.with_name(f".{approved.name}.{uuid4().hex}.old")
        approved.rename(retired)
        try:
            staged.rename(approved)
        except BaseException:
            retired.rename(approved)
            raise
        shutil.rmtree(retired, ignore_errors=True)
        return run_id
    finally:
        shutil.rmtree(staged, ignore_errors=True)


def _archive(current, history):
    target = history / _run_id(current)
    if target.exists():
        return
    staged = _stage(current, target)
    try:
        staged.rename(target)
    finally:
        shutil.rmtree(staged, ignore_errors=True)


def _stage(source, target):
    """Copia los cinco archivos a una carpeta temporal junto a `target`, lista para renombrarse."""
    target.parent.mkdir(parents=True, exist_ok=True)
    staged = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
    staged.mkdir()
    try:
        for name in VERSION_FILES:
            shutil.copy2(source / name, staged / name)
    except BaseException:
        shutil.rmtree(staged, ignore_errors=True)
        raise
    return staged


def _missing_files(folder):
    return [name for name in VERSION_FILES if not (folder / name).is_file()]


def _run_id(folder):
    return json.loads((folder / "run.json").read_text(encoding="utf-8"))["run_id"]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Restaurar una versión aprobada del historial.")
    parser.add_argument("--restore", required=True, metavar="RUN_ID", help="Carpeta de outputs.history_dir.")
    parser.add_argument("--config", default="config/pipeline.yaml", help="Ruta del archivo de configuración YAML.")
    args = parser.parse_args(argv)
    try:
        run_id = restore(args.restore, load_config(args.config))
    except Exception as error:
        print(f"No se pudo restaurar la versión: {error}", file=sys.stderr)
        return 1
    print(f"Versión restaurada: {run_id}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
