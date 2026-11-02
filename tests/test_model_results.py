import os
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from app import approved, model_results
from app.approved import APPROVED_DIR_VARIABLE
from pipeline.config import ROOT, load_config
from pipeline.publish import publish, restore
from tests.test_approved_contract import SAMPLE_DIR

OLD_ID = "20260701T120000000000Z_a1b2c3d4"
NEW_ID = "20260801T120000000000Z_e5f6a7b8"


def use_folder(test, folder):
    test.enterContext(patch.dict(os.environ, {APPROVED_DIR_VARIABLE: str(folder)}))
    model_results._cache.update(key=None, version=None)


class CurrentVersionTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(self.enterContext(TemporaryDirectory()))
        self.config = load_config("config/pipeline.yaml")
        self.config["outputs"]["approved_dir"] = self.folder / "current"
        self.config["outputs"]["history_dir"] = self.folder / "history"
        use_folder(self, self.config["outputs"]["approved_dir"])

    def test_missing_version_is_unavailable_until_one_is_published(self):
        self.assertIsNone(model_results.current_version())
        publish(SAMPLE_DIR / "current", self.config)
        self.assertEqual(model_results.current_version()["run"]["run_id"], NEW_ID)

    def test_version_is_read_once_and_reread_only_after_publication_or_restore(self):
        shutil.copytree(SAMPLE_DIR / "history" / OLD_ID, self.config["outputs"]["approved_dir"])
        with patch.object(model_results.approved, "load_approved", wraps=approved.load_approved) as loader:
            for _ in range(3):
                self.assertEqual(model_results.current_version()["run"]["run_id"], OLD_ID)
            self.assertEqual(loader.call_count, 1)
            publish(SAMPLE_DIR / "current", self.config)
            self.assertEqual(model_results.current_version()["run"]["run_id"], NEW_ID)
            restore(OLD_ID, self.config)
            self.assertEqual(model_results.current_version()["run"]["run_id"], OLD_ID)
            self.assertEqual(loader.call_count, 3)

    def test_unreadable_version_is_reported_as_unavailable(self):
        current = self.config["outputs"]["approved_dir"]
        shutil.copytree(SAMPLE_DIR / "current", current)
        (current / "run.json").write_text("{", encoding="utf-8")
        with self.assertLogs("app.model_results", level="ERROR"):
            self.assertIsNone(model_results.current_version())


class FormattingTests(unittest.TestCase):
    def test_monthly_values_keep_absent_months_empty_instead_of_zero(self):
        frame = pd.DataFrame({"period": ["2024-03", "2024-01", "2024-04"], "value": [30, 10, None]})
        series = model_results.monthly(frame)
        self.assertEqual(list(series.index), list(pd.date_range("2024-01-01", "2024-04-01", freq="MS")))
        self.assertEqual(series.iloc[0], 10)
        self.assertTrue(series.iloc[[1, 3]].isna().all())

    def test_spanish_labels(self):
        self.assertEqual(model_results.number(12345.678, 1), "12.345,7")
        self.assertEqual(model_results.number(250), "250")
        self.assertEqual(model_results.updated_label("2026-08-01T12:00:00+00:00"), "1 de agosto de 2026, 12:00 UTC")
        self.assertEqual(model_results.updated_label("2026-08-01T06:30:00-06:00"), "1 de agosto de 2026, 12:30 UTC")
        self.assertEqual(
            model_results.evaluated_label(["2026-06", "2025-07", "2025-08"]),
            "3 meses evaluados entre julio de 2025 y junio de 2026",
        )
        self.assertEqual(model_results.evaluated_label([]), "ningún mes evaluado")
        self.assertEqual(model_results.procedure_label("holt_winters"), "Holt-Winters")
        self.assertEqual(model_results.procedure_label("otro"), "otro")


class SourceBoundaryTests(unittest.TestCase):
    def test_no_dashboard_module_reads_previous_lab_results(self):
        for path in (ROOT / "app").rglob("*.py"):
            with self.subTest(path=path.name):
                self.assertNotIn("resultados", path.read_text(encoding="utf-8"))

    def test_estimate_components_do_not_read_insumos(self):
        for name in ["predictions.py", "model_errors.py"]:
            text = (ROOT / "app" / "components" / name).read_text(encoding="utf-8")
            self.assertNotIn("app import data", text)
            self.assertNotIn("insumos", text)


if __name__ == "__main__":
    unittest.main()
