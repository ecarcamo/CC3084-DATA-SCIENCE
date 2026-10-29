import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

from pipeline.checks import run_checks
from pipeline.config import ROOT, load_config
from pipeline.stages import prepare_series, read_source, source_fingerprint


def run_pipeline(config_path):
    config_path = (ROOT / Path(config_path)).resolve()
    config = load_config(config_path)
    started_at = datetime.now(timezone.utc)
    run_id = f"{started_at:%Y%m%dT%H%M%S%fZ}_{uuid4().hex[:8]}"
    candidate_dir = config["outputs"]["candidates_dir"] / run_id
    candidate_dir.mkdir(parents=True)
    metadata = {
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "finished_at": None,
        "status": "running",
        "completed_stages": [],
        "source_fingerprint": None,
        "config_path": str(config_path),
        "checks_status": "pending",
        "checks": [],
        "warnings": [],
        "errors": [],
        "publication": "not_attempted",
    }
    try:
        frame = read_source(config)
        metadata["source_fingerprint"] = source_fingerprint(config["source"]["path"])
        metadata["completed_stages"].append("read_source")
        checks = run_checks(frame, config)
        metadata["checks"] = checks
        if checks:
            metadata["checks_status"] = "executed"
            metadata["completed_stages"].append("run_checks")
        else:
            metadata["warnings"].append("Los seis controles de calidad están pendientes de integración.")
        series = prepare_series(frame, config)
        metadata["completed_stages"].append("prepare_series")
        observed = pd.DataFrame({
            "destination": config["destination"]["key"],
            "period": series.index.strftime("%Y-%m"),
            "value": series.to_numpy(),
            "unit": config["target"]["unit"],
            "kind": "observado",
            "run_id": run_id,
            "generated_at": started_at.isoformat(),
            "procedure_version": config["model"]["procedure_version"],
        })
        observed.to_csv(
            candidate_dir / "observed.csv",
            columns=config["outputs"]["estimate_columns"],
            index=False,
        )
        metadata["completed_stages"].append("write_observed")
        metadata["status"] = "prepared"
    except Exception as error:
        metadata["status"] = "failed"
        metadata["errors"].append(str(error))
        raise
    finally:
        metadata["finished_at"] = datetime.now(timezone.utc).isoformat()
        content = json.dumps(metadata, ensure_ascii=False, indent=2) + "\n"
        (candidate_dir / "run.json").write_text(content, encoding="utf-8")
        log_dir = config["outputs"]["run_log_dir"]
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"{run_id}.json").write_text(content, encoding="utf-8")
    return candidate_dir


def main(argv=None):
    parser = argparse.ArgumentParser(description="Preparar la serie mensual de visitantes.")
    parser.add_argument("--config", required=True, help="Ruta del archivo de configuración YAML.")
    args = parser.parse_args(argv)
    try:
        candidate_dir = run_pipeline(args.config)
    except Exception as error:
        print(f"El pipeline no pudo completarse: {error}", file=sys.stderr)
        return 1
    print(f"Preparación terminada. Candidato: {candidate_dir}")
    print("No se publicaron resultados. Los controles de calidad requieren integración.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
