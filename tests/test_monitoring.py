import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from pipeline.checks import OK, WARNING, run_checks, write_quality_report
from pipeline.config import ROOT, load_config
from pipeline.monitoring import run_monitoring
from pipeline.stages import prepare_series
from tests.synthetic_source import build_source

SAMPLE_DIR = ROOT / "tests" / "fixtures" / "approved_sample" / "current"


class MonitoringTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config("config/pipeline.yaml")
        self.source = build_source(self.config)
        self.checks = run_checks(self.source, self.config)
        self.series = prepare_series(self.source, self.config)
        periods = self.config["periods"]
        forecast = pd.period_range(periods["forecast_start"], periods["forecast_end"], freq="M")
        previous_year = self.series.reindex((forecast - 12).to_timestamp()).to_numpy()
        self.estimates = pd.DataFrame({"period": forecast.astype(str), "value": previous_year * 1.05})

    def monitor(self, previous_dir=None, checks=None):
        results = run_monitoring(
            self.series, self.estimates, self.checks if checks is None else checks, previous_dir, self.config
        )
        return {result.name: result for result in results}

    def test_healthy_run_is_ok_without_previous_version(self):
        results = self.monitor()
        self.assertEqual(list(results), ["monitor_freshness", "monitor_quality", "monitor_results"])
        self.assertEqual({result.status for result in results.values()}, {OK})
        self.assertIn("No hay versión aprobada anterior", results["monitor_quality"].message)

    def test_missing_previous_folder_is_ok(self):
        with TemporaryDirectory() as folder:
            quality = self.monitor(Path(folder) / "sin_version")["monitor_quality"]
        self.assertEqual(quality.status, OK)
        self.assertIn("No hay versión aprobada anterior", quality.message)

    def test_previous_version_without_quality_details_is_ok(self):
        quality = self.monitor(SAMPLE_DIR)["monitor_quality"]
        self.assertEqual(quality.status, OK)
        self.assertEqual(quality.details["increases"], {})

    def test_quality_drift_against_previous_version_warns(self):
        degraded = self.source.loc[~(self.source["Año"].eq(2015) & self.source["Mes cod"].eq(4))]
        with TemporaryDirectory() as folder:
            write_quality_report(self.checks, Path(folder) / "quality_report.json", "anterior")
            worse = self.monitor(folder, run_checks(degraded, self.config))["monitor_quality"]
            same = self.monitor(folder)["monitor_quality"]
        self.assertEqual(worse.status, WARNING)
        self.assertIn("meses sin datos", worse.message)
        self.assertEqual(worse.details["increases"]["missing_months"], 1)
        self.assertEqual(same.status, OK)
        self.assertEqual(same.details["increases"], {"missing_values": 0, "duplicate_rows": 0, "missing_months": 0})

    def test_late_series_and_missing_estimates_warn(self):
        self.series = self.series.iloc[:-1]
        self.estimates = self.estimates.iloc[:-1]
        freshness = self.monitor()["monitor_freshness"]
        self.assertEqual(freshness.status, WARNING)
        self.assertEqual(freshness.details["last_observed"], "2026-05")
        self.assertEqual(freshness.details["missing_estimates"], ["2026-12"])

    def test_negative_and_non_finite_estimates_warn(self):
        self.estimates.loc[0, "value"] = -1
        self.estimates.loc[1, "value"] = float("inf")
        result = self.monitor()["monitor_results"]
        self.assertEqual(result.status, WARNING)
        self.assertEqual(result.details["invalid_estimates"], ["2026-07", "2026-08"])

    def test_large_year_over_year_change_warns_and_skips_zero_base(self):
        self.estimates.loc[0, "value"] = self.series.loc["2025-07-01"] * 1.5
        self.series.loc["2025-08-01"] = 0
        result = self.monitor()["monitor_results"]
        self.assertEqual(result.status, WARNING)
        self.assertEqual([change["period"] for change in result.details["large_changes"]], ["2026-07"])
        self.assertEqual(result.details["large_changes"][0]["change_pct"], 50.0)
        self.assertEqual(result.details["not_comparable"], ["2026-08"])
        json.dumps(result.details)


if __name__ == "__main__":
    unittest.main()
