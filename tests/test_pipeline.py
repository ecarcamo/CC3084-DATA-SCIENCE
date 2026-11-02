import hashlib
import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from pipeline.checks import WARNING, CheckResult
from pipeline.config import ROOT, load_config
from pipeline.run import main, run_pipeline
from pipeline.stages import prepare_series, read_source, source_fingerprint
from tests.synthetic_source import build_source, write_config

SAMPLE_DIR = ROOT / "tests" / "fixtures" / "approved_sample" / "current"
FULL_STAGES = [
    "read_source", "run_checks", "prepare_series", "write_observed", "fit_and_forecast",
    "evaluate", "write_estimates", "accept", "run_monitoring",
]
PENDING_MODEL = NotImplementedError("fit_and_forecast pendiente: persona A")


class PipelineTests(unittest.TestCase):
    def setUp(self):
        tracking = patch("pipeline.run.log_run", return_value="mlflow-run")
        tracking.start()
        self.addCleanup(tracking.stop)
        self.config = load_config("config/pipeline.yaml")
        self.source = build_source(self.config)
        self.frame = pd.DataFrame({
            "Año": [2023] * 7,
            "Mes cod": [1, 1, 1, 2, 3, 3, 3],
            "Tipo de Viajero": [
                "Turista", "Excursionista", "Viajero", "Viajero",
                "Turista", "Excursionista", "Cruceristas",
            ],
            "Viajero": [100, 30, 900, 800, 200, 60, 700],
        })

    def write_config(self, folder, source=None, with_source=True):
        frame = (self.frame if source is None else source) if with_source else None
        return write_config(folder, frame)

    def write_approved(self, config):
        approved = Path(config["outputs"]["approved_dir"])
        approved.mkdir()
        previous = approved / "estimates.csv"
        previous.write_bytes(b"version aprobada")
        return previous

    def patch_stages(self, accepted=True):
        estimates = pd.read_csv(SAMPLE_DIR / "estimates.csv")
        metrics = json.loads((SAMPLE_DIR / "metrics.json").read_text(encoding="utf-8"))
        decision = {"accepted": accepted, "reasons": [] if accepted else ["El MAPE supera el umbral."]}
        results = {
            "fit_and_forecast": estimates[["period", "value"]],
            "model_parameters": {"procedure": "holt_winters"},
            "evaluate": metrics,
            "accept": decision,
            "run_monitoring": [],
            "publish": "version",
            "log_run": "mlflow-run",
        }
        stack = ExitStack()
        mocks = {
            name: stack.enter_context(patch(f"pipeline.run.{name}", return_value=value))
            for name, value in results.items()
        }
        return stack, mocks

    def read_metadata(self, candidate):
        return json.loads((candidate / "run.json").read_text(encoding="utf-8"))

    def test_series_preserves_missing_month_and_excludes_other_travelers(self):
        series = prepare_series(self.frame, self.config)
        self.assertIsInstance(series.index, pd.DatetimeIndex)
        self.assertEqual(list(series.index), list(pd.date_range("2023-01-01", periods=3, freq="MS")))
        self.assertEqual(series.iloc[0], 130)
        self.assertTrue(pd.isna(series.iloc[1]))
        self.assertEqual(series.iloc[2], 260)

    def test_all_missing_values_are_not_summed_as_zero(self):
        self.frame.loc[self.frame["Mes cod"].eq(3), "Viajero"] = float("nan")
        series = prepare_series(self.frame, self.config)
        self.assertTrue(pd.isna(series.loc["2023-03-01"]))

    def test_allocation_factor_comes_from_configuration(self):
        self.config["destination"]["allocation_factor"] = 0.5
        self.assertEqual(prepare_series(self.frame, self.config).iloc[0], 65)

    def test_empty_visitor_selection_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "tipos de visitantes"):
            prepare_series(self.frame[self.frame["Tipo de Viajero"].eq("Viajero")], self.config)

    def test_paths_do_not_depend_on_working_directory(self):
        script = (
            "from pipeline.config import load_config; "
            "from pathlib import Path; "
            "config = load_config('config/pipeline.yaml'); "
            "assert config['source']['path'] == "
            f"Path({str(ROOT / 'data/raw/base_migracion_2009_2026jun.xlsx')!r}); "
            "assert config['outputs']['candidates_dir'].is_absolute(); "
            "assert config['mlflow']['artifact_root'].is_absolute()"
        )
        with TemporaryDirectory(dir=ROOT) as folder:
            result = subprocess.run(
                [sys.executable, "-c", f"import sys; sys.path.insert(0, {str(ROOT)!r}); {script}"],
                cwd=folder,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_source_reader_uses_configured_sheet_and_fingerprint(self):
        with TemporaryDirectory(dir=ROOT) as folder:
            config_path, raw_config = self.write_config(Path(folder))
            loaded = read_source(load_config(config_path))
            pd.testing.assert_frame_equal(loaded, self.frame)
            source = Path(raw_config["source"]["path"])
            self.assertEqual(source_fingerprint(source), hashlib.sha256(source.read_bytes()).hexdigest())

    def test_pending_model_stage_fails_after_writing_observed(self):
        with TemporaryDirectory(dir=ROOT) as folder:
            config_path, config = self.write_config(Path(folder), self.source)
            previous = self.write_approved(config)
            error_output = io.StringIO()
            with patch("pipeline.run.fit_and_forecast", side_effect=PENDING_MODEL), \
                    patch("pipeline.run.log_run", side_effect=NotImplementedError("log_run pendiente: persona B")), \
                    redirect_stderr(error_output):
                self.assertEqual(main(["--config", str(config_path)]), 1)
            self.assertIn("fit_and_forecast pendiente", error_output.getvalue())
            candidate = next(Path(config["outputs"]["candidates_dir"]).iterdir())
            observed = pd.read_csv(candidate / "observed.csv")
            metadata = self.read_metadata(candidate)
            report = json.loads((candidate / config["outputs"]["quality_report_file"]).read_text(encoding="utf-8"))
            self.assertEqual(list(observed.columns), config["outputs"]["estimate_columns"])
            self.assertEqual(len(observed), len(self.source) // 2)
            self.assertEqual(observed["value"].iloc[0], 200)
            self.assertFalse(observed["value"].isna().any())
            self.assertEqual(set(observed["kind"]), {"observado"})
            self.assertEqual(set(observed["destination"]), {"guatemala"})
            self.assertEqual(set(observed["run_id"]), {candidate.name})
            self.assertEqual(metadata["run_id"], candidate.name)
            self.assertEqual(metadata["status"], "failed")
            self.assertEqual(metadata["errors"], ["fit_and_forecast pendiente: persona A"])
            self.assertEqual(metadata["completed_stages"], FULL_STAGES[:4])
            self.assertEqual(metadata["publication"], "not_attempted")
            self.assertIsNone(metadata["metrics"])
            self.assertIsNone(metadata["acceptance"])
            self.assertEqual(metadata["warnings"], ["No se registró la ejecución en MLflow: log_run pendiente: persona B"])
            self.assertEqual(metadata["checks_status"], "executed")
            self.assertEqual({check["status"] for check in metadata["checks"]}, {"ok"})
            self.assertEqual(report["run_id"], candidate.name)
            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["checks"], metadata["checks"])
            self.assertLessEqual(metadata["started_at"], metadata["finished_at"])
            self.assertEqual(metadata["source_fingerprint"], source_fingerprint(config["source"]["path"]))
            self.assertFalse((candidate / config["outputs"]["estimates_file"]).exists())
            self.assertFalse((candidate / "metrics.json").exists())
            log_path = Path(config["outputs"]["run_log_dir"]) / f"{candidate.name}.json"
            self.assertEqual(json.loads(log_path.read_text(encoding="utf-8")), metadata)
            self.assertEqual(list(previous.parent.iterdir()), [previous])
            self.assertEqual(previous.read_bytes(), b"version aprobada")

    def test_accepted_candidate_is_published_after_writing_every_file(self):
        with TemporaryDirectory(dir=ROOT) as folder:
            config_path, config = self.write_config(Path(folder), self.source)
            stack, mocks = self.patch_stages(accepted=True)
            published = {}
            mocks["publish"].side_effect = lambda candidate, _: published.update(
                files={path.name for path in candidate.iterdir()},
                run=self.read_metadata(candidate),
            )
            with stack, redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--config", str(config_path)]), 0)
            candidate = next(Path(config["outputs"]["candidates_dir"]).iterdir())
            metadata = self.read_metadata(candidate)
            estimates = pd.read_csv(candidate / config["outputs"]["estimates_file"])
            self.assertEqual(metadata["status"], "completed")
            self.assertEqual(metadata["publication"], "published")
            self.assertEqual(metadata["completed_stages"], FULL_STAGES + ["publish", "log_run"])
            self.assertEqual(metadata["mlflow_run_id"], "mlflow-run")
            self.assertEqual(metadata["acceptance"], {"accepted": True, "reasons": []})
            self.assertEqual(
                published["files"],
                {"estimates.csv", "observed.csv", "metrics.json", "quality_report.json", "run.json"},
            )
            self.assertEqual(published["run"]["publication"], "published")
            self.assertEqual(list(estimates.columns), config["outputs"]["estimate_columns"])
            self.assertEqual(set(estimates["kind"]), {"estimado"})
            self.assertEqual(set(estimates["run_id"]), {candidate.name})
            self.assertEqual(
                json.loads((candidate / "metrics.json").read_text(encoding="utf-8")), metadata["metrics"]
            )
            mocks["log_run"].assert_called_once()

    def test_rejected_candidate_is_not_published(self):
        with TemporaryDirectory(dir=ROOT) as folder:
            config_path, config = self.write_config(Path(folder), self.source)
            previous = self.write_approved(config)
            stack, mocks = self.patch_stages(accepted=False)
            with stack, redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--config", str(config_path)]), 0)
            metadata = self.read_metadata(next(Path(config["outputs"]["candidates_dir"]).iterdir()))
            self.assertEqual(metadata["status"], "completed")
            self.assertEqual(metadata["publication"], "rejected")
            self.assertEqual(metadata["completed_stages"], FULL_STAGES + ["log_run"])
            mocks["publish"].assert_not_called()
            self.assertEqual(previous.read_bytes(), b"version aprobada")

    def test_run_json_is_complete_before_tracking(self):
        with TemporaryDirectory(dir=ROOT) as folder:
            config_path, _ = self.write_config(Path(folder), self.source)
            stack, mocks = self.patch_stages(accepted=True)
            logged = {}
            mocks["log_run"].side_effect = lambda metadata, config, candidate: logged.update(
                self.read_metadata(candidate)
            ) or "mlflow-run"
            with stack, redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--config", str(config_path)]), 0)
            self.assertEqual(logged["status"], "completed")
            self.assertEqual(logged["publication"], "published")
            self.assertIsNotNone(logged["finished_at"])

    def test_publication_failure_is_recorded_as_failed(self):
        with TemporaryDirectory(dir=ROOT) as folder:
            config_path, config = self.write_config(Path(folder), self.source)
            stack, mocks = self.patch_stages(accepted=True)
            mocks["publish"].side_effect = OSError("No se pudo copiar la versión.")
            with stack, redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--config", str(config_path)]), 1)
            metadata = self.read_metadata(next(Path(config["outputs"]["candidates_dir"]).iterdir()))
            self.assertEqual(metadata["status"], "failed")
            self.assertEqual(metadata["publication"], "failed")
            self.assertEqual(metadata["errors"], ["No se pudo copiar la versión."])
            self.assertEqual(metadata["completed_stages"], FULL_STAGES + ["log_run"])

    def test_monitoring_warning_does_not_block_publication(self):
        with TemporaryDirectory(dir=ROOT) as folder:
            config_path, config = self.write_config(Path(folder), self.source)
            stack, mocks = self.patch_stages(accepted=True)
            mocks["run_monitoring"].return_value = [
                CheckResult("monitor_results", WARNING, "Variación interanual alta.", {})
            ]
            with stack, redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--config", str(config_path)]), 0)
            metadata = self.read_metadata(next(Path(config["outputs"]["candidates_dir"]).iterdir()))
            self.assertEqual(metadata["publication"], "published")
            self.assertEqual(metadata["acceptance"], {"accepted": True, "reasons": []})
            self.assertIn("monitor_results: Variación interanual alta.", metadata["warnings"])
            self.assertEqual(metadata["monitoring"][0]["status"], WARNING)
            mocks["publish"].assert_called_once()

    def test_tracking_failure_does_not_hide_original_error(self):
        with TemporaryDirectory(dir=ROOT) as folder:
            config_path, config = self.write_config(Path(folder), self.source)
            with patch("pipeline.run.fit_and_forecast", side_effect=ValueError("Modelo sin convergencia")), \
                    patch("pipeline.run.log_run", side_effect=RuntimeError("MLflow no disponible")):
                with self.assertRaisesRegex(ValueError, "Modelo sin convergencia"):
                    run_pipeline(config_path)
            metadata = self.read_metadata(next(Path(config["outputs"]["candidates_dir"]).iterdir()))
            self.assertEqual(metadata["errors"], ["Modelo sin convergencia"])
            self.assertEqual(metadata["warnings"], ["No se registró la ejecución en MLflow: MLflow no disponible"])

    def test_missing_source_returns_error_and_records_failure(self):
        with TemporaryDirectory(dir=ROOT) as folder:
            config_path, config = self.write_config(Path(folder), with_source=False)
            error_output = io.StringIO()
            with redirect_stderr(error_output):
                result = main(["--config", str(config_path)])
            self.assertEqual(result, 1)
            self.assertIn("No se encontró la fuente institucional", error_output.getvalue())
            candidates = list(Path(config["outputs"]["candidates_dir"]).iterdir())
            self.assertEqual(len(candidates), 1)
            candidate = candidates[0]
            metadata = self.read_metadata(candidate)
            self.assertEqual(metadata["status"], "failed")
            self.assertEqual(metadata["completed_stages"], ["log_run"])
            self.assertIsNone(metadata["source_fingerprint"])
            self.assertIsNone(metadata["metrics"])
            self.assertTrue(metadata["errors"])
            self.assertFalse((candidate / "observed.csv").exists())
            self.assertFalse(Path(config["outputs"]["approved_dir"]).exists())

    def test_quality_stop_halts_preparation_and_preserves_approved_version(self):
        with TemporaryDirectory(dir=ROOT) as folder:
            config_path, config = self.write_config(Path(folder), self.source.drop(columns="Frontera"))
            previous = self.write_approved(config)
            with self.assertRaisesRegex(ValueError, "check_columns_and_types"):
                run_pipeline(config_path)
            candidate = next(Path(config["outputs"]["candidates_dir"]).iterdir())
            metadata = self.read_metadata(candidate)
            report = json.loads((candidate / config["outputs"]["quality_report_file"]).read_text(encoding="utf-8"))
            self.assertEqual(metadata["status"], "failed")
            self.assertEqual(metadata["publication"], "blocked")
            self.assertEqual(metadata["completed_stages"], ["read_source", "run_checks", "log_run"])
            self.assertEqual(report["status"], "stop")
            self.assertFalse((candidate / "observed.csv").exists())
            self.assertEqual(previous.read_bytes(), b"version aprobada")

    def test_controlled_failure_blocks_publication_and_recovers_after_fix(self):
        with TemporaryDirectory(dir=ROOT) as folder:
            duplicated = pd.concat([self.source, self.source.iloc[[0]]], ignore_index=True)
            config_path, config = self.write_config(Path(folder), duplicated)
            previous = self.write_approved(config)
            candidates = Path(config["outputs"]["candidates_dir"])
            error_output = io.StringIO()
            with redirect_stderr(error_output):
                self.assertEqual(main(["--config", str(config_path)]), 1)
            self.assertIn("check_uniqueness", error_output.getvalue())
            candidate = next(candidates.iterdir())
            metadata = self.read_metadata(candidate)
            report = json.loads((candidate / config["outputs"]["quality_report_file"]).read_text(encoding="utf-8"))
            self.assertEqual(metadata["status"], "failed")
            self.assertEqual(metadata["publication"], "blocked")
            self.assertIn("check_uniqueness: Hay 1 claves repetidas.", metadata["errors"][0])
            self.assertEqual(report["status"], "stop")
            self.assertEqual([check["name"] for check in report["checks"] if check["status"] == "stop"], ["check_uniqueness"])
            self.assertFalse((candidate / "observed.csv").exists())
            self.assertEqual(list(previous.parent.iterdir()), [previous])
            self.assertEqual(previous.read_bytes(), b"version aprobada")
            self.source.to_excel(config["source"]["path"], sheet_name=config["source"]["sheet"], index=False)
            stack, mocks = self.patch_stages(accepted=True)
            with stack, redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--config", str(config_path)]), 0)
            self.assertEqual(len(list(candidates.iterdir())), 2)
            self.assertEqual(len(list(candidates.glob("*/observed.csv"))), 1)
            mocks["publish"].assert_called_once()

    def test_check_exception_stops_preparation_and_preserves_approved_version(self):
        with TemporaryDirectory(dir=ROOT) as folder:
            config_path, config = self.write_config(Path(folder))
            previous = self.write_approved(config)
            with patch("pipeline.run.run_checks", side_effect=ValueError("Control crítico fallido")):
                with self.assertRaisesRegex(ValueError, "Control crítico"):
                    run_pipeline(config_path)
            candidate = next(Path(config["outputs"]["candidates_dir"]).iterdir())
            metadata = self.read_metadata(candidate)
            self.assertEqual(metadata["status"], "failed")
            self.assertEqual(metadata["completed_stages"], ["read_source", "log_run"])
            self.assertFalse((candidate / "observed.csv").exists())
            self.assertEqual(previous.read_bytes(), b"version aprobada")

    def test_command_executes_with_synthetic_excel(self):
        with TemporaryDirectory(dir=ROOT) as folder:
            config_path, config = self.write_config(Path(folder), self.source)
            result = subprocess.run(
                [sys.executable, "-m", "pipeline.run", "--config", str(config_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            candidate = next(Path(config["outputs"]["candidates_dir"]).iterdir())
            metadata = self.read_metadata(candidate)
            self.assertEqual(result.returncode, 0 if metadata["status"] == "completed" else 1, result.stderr)
            self.assertIn("write_observed", metadata["completed_stages"])
            self.assertTrue((candidate / "observed.csv").is_file())
            if metadata["status"] == "failed":
                self.assertIn(metadata["errors"][0], result.stderr)


if __name__ == "__main__":
    unittest.main()
