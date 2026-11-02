import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.config import ROOT, load_config

SAMPLE_DIR = ROOT / "tests" / "fixtures" / "approved_sample"
APPROVED_FILES = {"estimates.csv", "observed.csv", "metrics.json", "quality_report.json", "run.json"}
METRICS_KEYS = {"procedure", "baseline", "evaluated_periods", "mape_zero_rule"}
SCORE_KEYS = {"name", "mae", "rmse", "mape_pct"}
PERIOD_PATTERN = r"\d{4}-(0[1-9]|1[0-2])"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def assert_approved_version(test, folder, config):
    folder = Path(folder)
    test.assertEqual({path.name for path in folder.iterdir()}, APPROVED_FILES)
    run = read_json(folder / "run.json")
    report = read_json(folder / "quality_report.json")
    metrics = read_json(folder / "metrics.json")
    test.assertEqual(run["publication"], "published")
    test.assertEqual(report["run_id"], run["run_id"])
    test.assertIn(report["status"], {"ok", "warning"})
    test.assertEqual(set(metrics), METRICS_KEYS)
    for score in ("procedure", "baseline"):
        test.assertEqual(set(metrics[score]), SCORE_KEYS)
    test.assertTrue(all(pd.Series(metrics["evaluated_periods"]).str.fullmatch(PERIOD_PATTERN)))
    periods = config["periods"]
    forecast = [str(period) for period in pd.period_range(periods["forecast_start"], periods["forecast_end"], freq="M")]
    for name, kind in (("estimates.csv", "estimado"), ("observed.csv", "observado")):
        frame = pd.read_csv(folder / name)
        test.assertEqual(list(frame.columns), config["outputs"]["estimate_columns"])
        test.assertEqual(set(frame["kind"]), {kind})
        test.assertEqual(set(frame["run_id"]), {run["run_id"]})
        test.assertTrue(frame["period"].str.fullmatch(PERIOD_PATTERN).all())
        test.assertFalse(frame["period"].duplicated().any())
    estimates = pd.read_csv(folder / "estimates.csv")
    test.assertEqual(list(estimates["period"]), forecast)
    test.assertTrue(np.isfinite(estimates["value"]).all())
    test.assertTrue(estimates["value"].ge(0).all())


class ApprovedSampleTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config("config/pipeline.yaml")

    def test_current_sample_follows_contract(self):
        assert_approved_version(self, SAMPLE_DIR / "current", self.config)

    def test_history_versions_follow_contract_and_use_run_id_as_folder(self):
        versions = list((SAMPLE_DIR / "history").iterdir())
        self.assertTrue(versions)
        for folder in versions:
            with self.subTest(version=folder.name):
                assert_approved_version(self, folder, self.config)
                self.assertEqual(read_json(folder / "run.json")["run_id"], folder.name)


if __name__ == "__main__":
    unittest.main()
