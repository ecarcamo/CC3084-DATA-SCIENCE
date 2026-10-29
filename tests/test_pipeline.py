import hashlib
import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd
import yaml

from pipeline.config import ROOT, load_config
from pipeline.run import main, run_pipeline
from pipeline.stages import prepare_series, read_source, source_fingerprint
from tests.synthetic_source import build_source


class PipelineTests(unittest.TestCase):
    def setUp(self):
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
        config = yaml.safe_load((ROOT / "config/pipeline.yaml").read_text(encoding="utf-8"))
        config["source"]["path"] = str(folder / "source.xlsx")
        for key in ("candidates_dir", "approved_dir", "history_dir", "run_log_dir"):
            config["outputs"][key] = str(folder / key)
        config_path = folder / "pipeline.yaml"
        config_path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
        if with_source:
            frame = self.frame if source is None else source
            frame.to_excel(config["source"]["path"], sheet_name=config["source"]["sheet"], index=False)
        return config_path, config

    def write_approved(self, config):
        approved = Path(config["outputs"]["approved_dir"])
        approved.mkdir()
        previous = approved / "estimates.csv"
        previous.write_bytes(b"version aprobada")
        return previous

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

    def test_pipeline_writes_candidate_and_quality_report_without_publication(self):
        with TemporaryDirectory(dir=ROOT) as folder:
            config_path, config = self.write_config(Path(folder), self.source)
            previous = self.write_approved(config)
            candidate = run_pipeline(config_path)
            observed = pd.read_csv(candidate / "observed.csv")
            metadata = json.loads((candidate / "run.json").read_text(encoding="utf-8"))
            report = json.loads((candidate / config["outputs"]["quality_report_file"]).read_text(encoding="utf-8"))
            self.assertEqual(list(observed.columns), config["outputs"]["estimate_columns"])
            self.assertEqual(len(observed), len(self.source) // 2)
            self.assertEqual(observed["value"].iloc[0], 200)
            self.assertFalse(observed["value"].isna().any())
            self.assertEqual(set(observed["kind"]), {"observado"})
            self.assertEqual(set(observed["destination"]), {"guatemala"})
            self.assertEqual(set(observed["run_id"]), {candidate.name})
            self.assertEqual(metadata["run_id"], candidate.name)
            self.assertEqual(metadata["status"], "prepared")
            self.assertEqual(metadata["checks_status"], "executed")
            self.assertEqual({check["status"] for check in metadata["checks"]}, {"ok"})
            self.assertEqual(metadata["warnings"], [])
            self.assertEqual(metadata["publication"], "not_attempted")
            self.assertEqual(
                metadata["completed_stages"], ["read_source", "run_checks", "prepare_series", "write_observed"]
            )
            self.assertEqual(report["run_id"], candidate.name)
            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["checks"], metadata["checks"])
            self.assertLessEqual(metadata["started_at"], metadata["finished_at"])
            self.assertEqual(metadata["source_fingerprint"], source_fingerprint(config["source"]["path"]))
            log_path = Path(config["outputs"]["run_log_dir"]) / f"{candidate.name}.json"
            self.assertEqual(json.loads(log_path.read_text(encoding="utf-8")), metadata)
            self.assertEqual(previous.read_bytes(), b"version aprobada")

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
            metadata = json.loads((candidate / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["status"], "failed")
            self.assertEqual(metadata["completed_stages"], [])
            self.assertIsNone(metadata["source_fingerprint"])
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
            metadata = json.loads((candidate / "run.json").read_text(encoding="utf-8"))
            report = json.loads((candidate / config["outputs"]["quality_report_file"]).read_text(encoding="utf-8"))
            self.assertEqual(metadata["status"], "failed")
            self.assertEqual(metadata["completed_stages"], ["read_source", "run_checks"])
            self.assertEqual(report["status"], "stop")
            self.assertFalse((candidate / "observed.csv").exists())
            self.assertEqual(previous.read_bytes(), b"version aprobada")

    def test_check_exception_stops_preparation_and_preserves_approved_version(self):
        with TemporaryDirectory(dir=ROOT) as folder:
            config_path, config = self.write_config(Path(folder))
            previous = self.write_approved(config)
            with patch("pipeline.run.run_checks", side_effect=ValueError("Control crítico fallido")):
                with self.assertRaisesRegex(ValueError, "Control crítico"):
                    run_pipeline(config_path)
            candidate = next(Path(config["outputs"]["candidates_dir"]).iterdir())
            metadata = json.loads((candidate / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["status"], "failed")
            self.assertEqual(metadata["completed_stages"], ["read_source"])
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
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("No se publicaron resultados", result.stdout)
            self.assertEqual(len(list(Path(config["outputs"]["candidates_dir"]).glob("*/observed.csv"))), 1)


if __name__ == "__main__":
    unittest.main()
