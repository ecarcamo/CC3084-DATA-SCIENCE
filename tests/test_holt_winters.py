import json
import unittest

import numpy as np
import pandas as pd

from pipeline.config import load_config
from pipeline.model import fit_and_forecast, model_parameters
from pipeline.stages import prepare_series
from tests.synthetic_source import build_source


class HoltWintersTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config("config/pipeline.yaml")
        self.series = prepare_series(build_source(self.config), self.config)

    def test_forecast_has_one_finite_row_per_forecast_month(self):
        forecast = fit_and_forecast(self.series, self.config)
        self.assertEqual(list(forecast.columns), ["period", "value"])
        self.assertEqual(
            list(forecast["period"]), ["2026-07", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12"]
        )
        self.assertTrue(np.isfinite(forecast["value"]).all())

    def test_fit_ignores_months_outside_fit_period(self):
        expected = fit_and_forecast(self.series, self.config)
        altered = self.series.copy()
        altered.loc["2015-01-01":"2016-12-01"] = np.nan
        altered.loc[pd.Timestamp("2026-07-01")] = 1_000_000
        pd.testing.assert_frame_equal(fit_and_forecast(altered.asfreq("MS"), self.config), expected)

    def test_missing_month_in_fit_period_is_not_filled_with_zero(self):
        self.series.loc["2024-03-01"] = np.nan
        with self.assertRaisesRegex(ValueError, "2024-03"):
            fit_and_forecast(self.series, self.config)

    def test_parameters_are_complete_serializable_and_reproducible(self):
        parameters = model_parameters(self.series, self.config)
        for key in ("procedure", "procedure_version", "fit_start", "fit_end", "seed", "fitted"):
            self.assertIn(key, parameters)
        self.assertEqual(parameters["fit_start"], "2023-01")
        self.assertEqual(parameters["fit_end"], "2026-06")
        self.assertEqual(parameters["seed"], 42)
        self.assertEqual(len(parameters["fitted"]["initial_seasons"]), 12)
        self.assertEqual(json.loads(json.dumps(parameters)), model_parameters(self.series, self.config))


if __name__ == "__main__":
    unittest.main()
