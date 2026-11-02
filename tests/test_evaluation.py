import unittest

import numpy as np
import pandas as pd

from pipeline.config import load_config
from pipeline.evaluation import MAPE_ZERO_RULE, error_metrics, evaluate, hidden_month_forecasts
from pipeline.stages import prepare_series
from tests.synthetic_source import build_source

EVALUATION_PERIODS = [f"2025-{month:02d}" for month in range(7, 13)] + [f"2026-{month:02d}" for month in range(1, 7)]


class HiddenMonthTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config("config/pipeline.yaml")
        self.series = prepare_series(build_source(self.config), self.config)

    def test_evaluated_periods_follow_evaluation_window_in_order(self):
        self.assertEqual(evaluate(self.series, self.config)["evaluated_periods"], EVALUATION_PERIODS)

    def test_each_month_is_estimated_only_with_previous_months(self):
        expected = hidden_month_forecasts(self.series, self.config)
        altered = self.series.copy()
        altered.loc["2026-01-01":] *= 3
        forecasts = hidden_month_forecasts(altered, self.config)
        pd.testing.assert_series_equal(
            forecasts.loc[:"2026-01", "procedure"], expected.loc[:"2026-01", "procedure"]
        )
        self.assertFalse(np.allclose(forecasts.loc["2026-02":, "procedure"], expected.loc["2026-02":, "procedure"]))

    def test_months_without_observed_value_are_not_evaluated(self):
        self.series.loc["2026-06-01"] = np.nan
        self.config["periods"]["evaluation_end"] = "2026-08"
        self.assertEqual(evaluate(self.series, self.config)["evaluated_periods"], EVALUATION_PERIODS[:-1])


class MetricTests(unittest.TestCase):
    def test_metrics_match_manual_calculation_and_exclude_zero_from_mape(self):
        metrics = error_metrics(pd.Series([0.0, 100.0, 200.0]), pd.Series([10.0, 110.0, 180.0]))
        self.assertAlmostEqual(metrics["mae"], 40 / 3)
        self.assertAlmostEqual(metrics["rmse"], np.sqrt(200))
        self.assertAlmostEqual(metrics["mape_pct"], 10.0)

    def test_mape_is_null_when_every_observed_value_is_zero(self):
        metrics = error_metrics(pd.Series([0.0, 0.0]), pd.Series([5.0, 15.0]))
        self.assertEqual(metrics["mae"], 10.0)
        self.assertIsNone(metrics["mape_pct"])

    def test_metrics_are_null_without_evaluated_months(self):
        empty = pd.Series(dtype=float)
        self.assertEqual(error_metrics(empty, empty), {"mae": None, "rmse": None, "mape_pct": None})

    def test_evaluation_reports_procedure_metrics_and_zero_rule(self):
        config = load_config("config/pipeline.yaml")
        metrics = evaluate(prepare_series(build_source(config), config), config)
        self.assertEqual(set(metrics["procedure"]), {"name", "mae", "rmse", "mape_pct"})
        self.assertEqual(metrics["procedure"]["name"], "holt_winters")
        self.assertGreaterEqual(metrics["procedure"]["rmse"], metrics["procedure"]["mae"])
        self.assertEqual(metrics["mape_zero_rule"], MAPE_ZERO_RULE)


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config("config/pipeline.yaml")
        self.series = prepare_series(build_source(self.config), self.config)

    def test_baseline_repeats_value_from_twelve_months_before(self):
        forecasts = hidden_month_forecasts(self.series, self.config)
        expected = self.series.shift(12).loc["2025-07-01":"2026-06-01"].to_numpy()
        np.testing.assert_allclose(forecasts["baseline"].to_numpy(), expected)

    def test_month_without_baseline_is_excluded_for_both_procedures(self):
        self.series.loc["2022-08-01"] = np.nan
        self.config["baseline"]["lag_months"] = 36
        forecasts = hidden_month_forecasts(self.series, self.config)
        self.assertEqual(list(forecasts.index), [period for period in EVALUATION_PERIODS if period != "2025-08"])
        self.assertFalse(forecasts.isna().any().any())

    def test_metrics_compare_both_procedures_on_same_months(self):
        metrics = evaluate(self.series, self.config)
        self.assertEqual(list(metrics), ["procedure", "baseline", "evaluated_periods", "mape_zero_rule"])
        self.assertEqual(metrics["baseline"]["name"], "seasonal_naive")
        self.assertAlmostEqual(metrics["baseline"]["mae"], 24.0)
        self.assertAlmostEqual(metrics["baseline"]["rmse"], 24.0)


if __name__ == "__main__":
    unittest.main()
