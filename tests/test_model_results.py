import math
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from app import model_results


class ModelResultsTests(unittest.TestCase):
    def test_real_sources_offer_five_models_on_the_same_dates(self):
        for series_key in model_results.data.load_labels().index:
            frame = model_results.align_models(series_key)
            self.assertEqual(len(frame), 63)
            self.assertEqual(len(frame.attrs["models"]), 5)
            self.assertEqual(frame.index.min(), pd.Timestamp("2021-04-01"))
            self.assertEqual(frame.index.max(), pd.Timestamp("2026-06-01"))

    def test_errors_use_only_the_shared_valid_dates(self):
        observed = pd.Series([100.0, 200.0, 0.0, 400.0], index=pd.date_range("2024-01-01", periods=4, freq="MS"), name="observed")
        forecasts = {
            "ses": pd.Series([90.0, 180.0, 10.0], index=observed.index[:3], name="predicted"),
            "sarima": pd.Series([150.0, 20.0, 999.0], index=observed.index[1:], name="predicted"),
        }
        with patch.object(model_results, "load_observations", return_value=observed), patch.object(
            model_results, "load_predictions", side_effect=lambda series, model: forecasts[model]
        ):
            errors = model_results.calculate_errors("total", ["ses", "sarima"])
        self.assertEqual(errors.loc["ses", "count"], 2)
        self.assertEqual(errors.loc["sarima", "count"], 2)
        self.assertAlmostEqual(errors.loc["ses", "mae"], 15)
        self.assertAlmostEqual(errors.loc["ses", "rmse"], math.sqrt(250))
        self.assertAlmostEqual(errors.loc["ses", "mape"], 10)
        self.assertAlmostEqual(errors.loc["sarima", "mae"], 35)
        self.assertAlmostEqual(errors.loc["sarima", "mape"], 25)
        self.assertEqual(errors.loc["ses", "mape_excluded"], 1)

    def test_all_zero_observations_leave_mape_undefined(self):
        dates = pd.date_range("2024-01-01", periods=2, freq="MS")
        observed = pd.Series([0.0, 0.0], index=dates, name="observed")
        predicted = pd.Series([10.0, 20.0], index=dates, name="predicted")
        with patch.object(model_results, "load_observations", return_value=observed), patch.object(
            model_results, "load_predictions", return_value=predicted
        ):
            errors = model_results.calculate_errors("total", ["ses"])
        self.assertTrue(pd.isna(errors.loc["ses", "mape"]))
        self.assertEqual(errors.loc["ses", "mae"], 15)
        self.assertEqual(errors.loc["ses", "mape_excluded"], 2)

    def test_missing_values_are_removed_without_becoming_zero(self):
        dates = pd.date_range("2024-01-01", periods=3, freq="MS")
        observed = pd.Series([100.0, float("nan"), 300.0], index=dates, name="observed")
        predicted = pd.Series([80.0, 120.0, float("nan")], index=dates, name="predicted")
        with patch.object(model_results, "load_observations", return_value=observed), patch.object(
            model_results, "load_predictions", return_value=predicted
        ):
            frame = model_results.align_observations("total", "ses")
        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.iloc[0]["error"], 20)

    def test_duplicate_dates_and_nonfinite_values_are_rejected(self):
        cases = [
            "fecha,prediccion\n2024-01-01,10\n2024-01-01,20\n",
            "fecha,prediccion\n2024-01-01,inf\n",
            "fecha,prediccion\n2024-01-01,texto\n",
            "fecha,prediccion\nfecha_invalida,10\n",
            "fecha,prediccion\n2024-01-15,10\n",
        ]
        with TemporaryDirectory() as folder, patch.object(model_results, "PREDICTIONS_DIR", Path(folder)):
            path = Path(folder) / "total_ses.csv"
            for content in cases:
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")
                    with self.assertRaises(model_results.ModelDataError):
                        model_results.load_predictions("total", "ses")

    def test_metric_keys_must_be_unique(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "metrics.csv"
            path.write_text("serie,modelo,mae,rmse,mape\ntotal,ses,1,1,1\ntotal,ses,2,2,2\n", encoding="utf-8")
            with patch.object(model_results, "METRICS_FILE", path), self.assertRaises(model_results.ModelDataError):
                model_results.load_metrics()

    def test_real_sample_matches_independent_scalar_arithmetic(self):
        observed = pd.read_csv(model_results.data.SERIES_DIR / "serie_total.csv").set_index("fecha")["viajeros"]
        predicted = pd.read_csv(model_results.PREDICTIONS_DIR / "total_ses.csv").set_index("fecha")["prediccion"]
        dates = sorted(set(observed.index) & set(predicted.index))
        distances = [abs(float(observed[date]) - float(predicted[date])) for date in dates]
        errors = model_results.calculate_errors("total", ["ses"])
        self.assertAlmostEqual(errors.loc["ses", "mae"], sum(distances) / len(distances))
        self.assertAlmostEqual(errors.loc["ses", "rmse"], math.sqrt(sum(value * value for value in distances) / len(distances)))

    def test_invalid_keys_and_empty_or_reversed_periods(self):
        self.assertTrue(model_results.align_observations("total", "ses", "2009-01-01", "2010-01-01").empty)
        for series, model, start, end in [
            ("../total", "ses", None, None), ("total", "../ses", None, None),
            ("total", "ses", "2026-01-01", "2025-01-01"), ("total", "ses", "incorrecta", None),
        ]:
            with self.subTest(series=series, model=model, start=start), self.assertRaises(model_results.ModelDataError):
                model_results.align_observations(series, model, start, end)


if __name__ == "__main__":
    unittest.main()
