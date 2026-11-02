import unittest

import numpy as np
import pandas as pd

from pipeline.config import load_config
from pipeline.evaluation import evaluate, hidden_month_forecasts
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


if __name__ == "__main__":
    unittest.main()
