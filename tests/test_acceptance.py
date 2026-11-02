import json
import unittest

import numpy as np
import pandas as pd

from pipeline.checks import OK, STOP, WARNING, CheckResult
from pipeline.config import ROOT, load_config
from pipeline.evaluation import accept

SAMPLE_DIR = ROOT / "tests" / "fixtures" / "approved_sample" / "current"


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config("config/pipeline.yaml")
        self.checks = [CheckResult("check_uniqueness", OK, "ok"), CheckResult("check_missing_values", WARNING, "aviso")]
        self.estimates = pd.read_csv(SAMPLE_DIR / "estimates.csv")
        self.metrics = json.loads((SAMPLE_DIR / "metrics.json").read_text(encoding="utf-8"))

    def decide(self):
        return accept(self.checks, self.estimates, self.metrics, self.config)

    def test_complete_candidate_within_thresholds_is_accepted(self):
        self.assertEqual(self.decide(), {"accepted": True, "reasons": []})

    def test_stop_check_rejects(self):
        self.checks.append(CheckResult("check_uniqueness", STOP, "duplicados"))
        decision = self.decide()
        self.assertFalse(decision["accepted"])
        self.assertEqual(decision["reasons"], ["Controles de calidad con estado stop: check_uniqueness."])

    def test_missing_forecast_month_rejects(self):
        self.estimates = self.estimates.iloc[:-1]
        decision = self.decide()
        self.assertFalse(decision["accepted"])
        self.assertIn("faltan: 2026-12", decision["reasons"][0])

    def test_negative_and_non_finite_estimates_reject(self):
        self.estimates["value"] = self.estimates["value"].astype(float)
        self.estimates.loc[0, "value"] = -1
        self.estimates.loc[1, "value"] = np.inf
        self.assertEqual(
            self.decide()["reasons"], ["Hay estimaciones vacías o no finitas.", "Hay estimaciones negativas."]
        )

    def test_missing_column_and_empty_values_reject(self):
        self.estimates = self.estimates.drop(columns="unit")
        self.estimates.loc[2, "run_id"] = ""
        self.assertEqual(
            self.decide()["reasons"],
            ["Faltan columnas en las estimaciones: unit.", "Hay valores vacíos en las columnas: run_id."],
        )

    def test_mape_above_threshold_rejects(self):
        self.metrics["procedure"]["mape_pct"] = 10.5
        self.assertEqual(self.decide()["reasons"], ["El MAPE es 10.50 %, mayor que el máximo de 10.0 %."])

    def test_mae_ratio_above_threshold_rejects(self):
        self.metrics["procedure"]["mae"] = 601.0
        self.assertEqual(
            self.decide()["reasons"],
            ["La razón de MAE frente a la referencia es 1.50, mayor que el máximo de 1.5."],
        )

    def test_thresholds_are_inclusive(self):
        self.metrics["procedure"]["mape_pct"] = 10.0
        self.metrics["procedure"]["mae"] = 600.0
        self.assertTrue(self.decide()["accepted"])

    def test_missing_metrics_reject(self):
        self.metrics["procedure"]["mape_pct"] = None
        self.metrics["baseline"]["mae"] = 0.0
        self.assertEqual(len(self.decide()["reasons"]), 2)

    def test_every_failed_criterion_has_its_own_reason(self):
        self.checks.append(CheckResult("check_uniqueness", STOP, "duplicados"))
        self.estimates = self.estimates.iloc[:-1]
        self.metrics["procedure"]["mape_pct"] = 50.0
        self.metrics["procedure"]["mae"] = 4000.0
        self.assertEqual(len(self.decide()["reasons"]), 4)


if __name__ == "__main__":
    unittest.main()
