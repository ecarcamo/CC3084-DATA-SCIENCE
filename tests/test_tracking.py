import json
import os
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from mlflow.tracking import MlflowClient

from pipeline.config import ROOT, load_config
from pipeline.tracking import log_run

SAMPLE_DIR = ROOT / "tests" / "fixtures" / "approved_sample" / "current"


class TrackingTests(unittest.TestCase):
    def setUp(self):
        pool = patch.dict(os.environ, {"MLFLOW_SQLALCHEMYSTORE_POOLCLASS": "NullPool"})
        pool.start()
        self.addCleanup(pool.stop)
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        root = Path(folder.name)
        self.config = load_config("config/pipeline.yaml")
        self.config["mlflow"]["tracking_uri"] = f"sqlite:///{(root / 'mlflow' / 'mlflow.db').as_posix()}"
        self.config["mlflow"]["artifact_root"] = root / "mlflow" / "artifacts"
        self.candidate = root / "candidate"
        shutil.copytree(SAMPLE_DIR, self.candidate)
        self.metadata = json.loads((SAMPLE_DIR / "run.json").read_text(encoding="utf-8"))
        self.metadata.update(config_path=str(ROOT / "config" / "pipeline.yaml"), mlflow_run_id=None)
        self.client = MlflowClient(tracking_uri=self.config["mlflow"]["tracking_uri"])

    def failed_metadata(self):
        self.metadata.update(
            status="failed",
            publication="not_attempted",
            metrics=None,
            model_parameters=None,
            acceptance=None,
            errors=["No se encontró la fuente institucional."],
        )
        return self.metadata

    def test_completed_run_logs_parameters_metrics_tags_and_artifacts(self):
        run = self.client.get_run(log_run(self.metadata, self.config, self.candidate))
        params, metrics, tags = run.data.params, run.data.metrics, run.data.tags
        self.assertEqual(run.info.status, "FINISHED")
        self.assertEqual(run.info.run_name, self.metadata["run_id"])
        self.assertEqual(params["source_fingerprint"], "muestra-sintetica")
        self.assertEqual(params["source_path"], "data/raw/base_migracion_2009_2026jun.xlsx")
        self.assertEqual(params["periods.fit_start"], "2023-01")
        self.assertEqual(params["periods.evaluation_end"], "2026-06")
        self.assertEqual(params["model.procedure"], "holt_winters")
        self.assertEqual(json.loads(params["evaluated_periods"]), self.metadata["metrics"]["evaluated_periods"])
        self.assertEqual(metrics["procedure.mae"], 250.0)
        self.assertEqual(metrics["baseline.mape_pct"], 3.5)
        self.assertEqual(metrics["evaluated_periods"], 12)
        self.assertEqual(tags["pipeline_run_id"], self.metadata["run_id"])
        self.assertEqual(tags["status"], "completed")
        self.assertEqual(tags["publication"], "published")
        self.assertEqual(tags["accepted"], "True")
        self.assertTrue(tags["git_commit"])
        self.assertNotIn("error", tags)
        artifacts = {artifact.path for artifact in self.client.list_artifacts(run.info.run_id)}
        self.assertTrue({"run.json", "estimates.csv", "metrics.json", "quality_report.json", "pipeline.yaml"} <= artifacts)

    def test_failed_run_logs_cause_without_metrics(self):
        run = self.client.get_run(log_run(self.failed_metadata(), self.config, self.candidate))
        self.assertEqual(run.info.status, "FAILED")
        self.assertEqual(run.data.metrics, {})
        self.assertEqual(run.data.tags["error"], "No se encontró la fuente institucional.")
        self.assertEqual(run.data.tags["status"], "failed")
        self.assertNotIn("evaluated_periods", run.data.params)
        self.assertNotIn("model.procedure", run.data.params)

    def test_runs_share_experiment_stored_in_artifact_root(self):
        first = self.client.get_run(log_run(self.metadata, self.config, self.candidate))
        second = self.client.get_run(log_run(self.failed_metadata(), self.config, self.candidate))
        experiment = self.client.get_experiment(first.info.experiment_id)
        self.assertEqual(first.info.experiment_id, second.info.experiment_id)
        self.assertEqual(experiment.name, self.config["mlflow"]["experiment_name"])
        self.assertEqual(experiment.artifact_location, Path(self.config["mlflow"]["artifact_root"]).as_uri())
        self.assertTrue(any(Path(self.config["mlflow"]["artifact_root"]).rglob("run.json")))

    def test_missing_git_is_recorded_as_unknown(self):
        with patch("pipeline.tracking.subprocess.run", side_effect=FileNotFoundError("git")):
            run = self.client.get_run(log_run(self.metadata, self.config, self.candidate))
        self.assertEqual(run.data.tags["git_commit"], "desconocido")
        self.assertEqual(run.data.tags["git_dirty"], "desconocido")


if __name__ == "__main__":
    unittest.main()
