import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

from pipeline.checks import STOP, WARNING, has_stop, run_checks, serialize_results, write_quality_report
from pipeline.config import ROOT, load_config
from pipeline.evaluation import accept, evaluate
from pipeline.model import fit_and_forecast, model_parameters
from pipeline.monitoring import run_monitoring
from pipeline.publish import publish
from pipeline.stages import prepare_series, read_source, source_fingerprint
from pipeline.tracking import log_run


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
        "model_parameters": None,
        "metrics": None,
        "acceptance": None,
        "monitoring": [],
        "warnings": [],
        "errors": [],
        "publication": "not_attempted",
        "mlflow_run_id": None,
    }
    stages = metadata["completed_stages"]
    try:
        frame = read_source(config)
        metadata["source_fingerprint"] = source_fingerprint(config["source"]["path"])
        stages.append("read_source")
        checks = run_checks(frame, config)
        metadata["checks"] = serialize_results(checks)
        metadata["checks_status"] = "executed"
        metadata["warnings"] = [f"{result.name}: {result.message}" for result in checks if result.status == WARNING]
        stages.append("run_checks")
        write_quality_report(checks, candidate_dir / config["outputs"]["quality_report_file"], run_id)
        if has_stop(checks):
            metadata["publication"] = "blocked"
            stopped = " ".join(f"{result.name}: {result.message}" for result in checks if result.status == STOP)
            raise ValueError(f"Los controles de calidad detuvieron el flujo. {stopped}")
        series = prepare_series(frame, config)
        stages.append("prepare_series")
        observed = _output_frame(series.index.strftime("%Y-%m"), series.to_numpy(), "observado", metadata, config)
        observed.to_csv(candidate_dir / "observed.csv", index=False)
        stages.append("write_observed")
        forecast = fit_and_forecast(series, config)
        metadata["model_parameters"] = model_parameters(series, config)
        stages.append("fit_and_forecast")
        metrics = evaluate(series, config)
        metadata["metrics"] = metrics
        stages.append("evaluate")
        estimates = _output_frame(forecast["period"], forecast["value"].to_numpy(), "estimado", metadata, config)
        estimates.to_csv(candidate_dir / config["outputs"]["estimates_file"], index=False)
        _write_json(candidate_dir / "metrics.json", metrics)
        stages.append("write_estimates")
        decision = accept(checks, estimates, metrics, config)
        metadata["acceptance"] = decision
        stages.append("accept")
        monitoring = run_monitoring(series, estimates, config["outputs"]["approved_dir"], config)
        metadata["monitoring"] = serialize_results(monitoring)
        metadata["warnings"] += [f"{result.name}: {result.message}" for result in monitoring if result.status == WARNING]
        stages.append("run_monitoring")
        metadata["status"] = "completed"
        if decision["accepted"]:
            metadata["publication"] = "published"
            _write_json(candidate_dir / "run.json", metadata)
            publish(candidate_dir, config)
            stages.append("publish")
        else:
            metadata["publication"] = "rejected"
    except Exception as error:
        metadata["status"] = "failed"
        metadata["errors"].append(str(error))
        if metadata["publication"] == "published":
            metadata["publication"] = "not_attempted"
        raise
    finally:
        metadata["finished_at"] = datetime.now(timezone.utc).isoformat()
        try:
            metadata["mlflow_run_id"] = log_run(metadata, config, candidate_dir)
            stages.append("log_run")
        except Exception as error:
            metadata["warnings"].append(f"No se registró la ejecución en MLflow: {error}")
        _write_json(candidate_dir / "run.json", metadata)
        log_dir = config["outputs"]["run_log_dir"]
        log_dir.mkdir(parents=True, exist_ok=True)
        _write_json(log_dir / f"{run_id}.json", metadata)
    return candidate_dir


def _output_frame(periods, values, kind, metadata, config):
    frame = pd.DataFrame({
        "destination": config["destination"]["key"],
        "period": list(periods),
        "value": values,
        "unit": config["target"]["unit"],
        "kind": kind,
        "run_id": metadata["run_id"],
        "generated_at": metadata["started_at"],
        "procedure_version": config["model"]["procedure_version"],
    })
    return frame[config["outputs"]["estimate_columns"]]


def _write_json(path, content):
    Path(path).write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Actualizar las estimaciones mensuales de visitantes.")
    parser.add_argument("--config", required=True, help="Ruta del archivo de configuración YAML.")
    args = parser.parse_args(argv)
    try:
        candidate_dir = run_pipeline(args.config)
    except Exception as error:
        print(f"El pipeline no pudo completarse: {error}", file=sys.stderr)
        return 1
    metadata = json.loads((candidate_dir / "run.json").read_text(encoding="utf-8"))
    print(f"Ejecución terminada. Candidato: {candidate_dir}")
    print(f"Resultado de la publicación: {metadata['publication']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
