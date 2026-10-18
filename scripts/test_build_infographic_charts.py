import unittest

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

import build_infographic_charts as charts


class InfographicChartsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        charts.configure_style()
        cls.total = charts.load_series("total")
        cls.forecast = charts.fit_forecast(cls.total)

    def test_reference_seasonality(self):
        factors = charts.seasonal_factors(self.total)
        self.assertEqual(factors.idxmax(), 12)
        self.assertEqual(factors.idxmin(), 9)
        np.testing.assert_allclose(factors.loc[[12, 9]], [1.372, 0.802], atol=0.0005, rtol=0)

    def test_forecast_matches_saved_predictions_and_intervals(self):
        saved = pd.read_csv(
            charts.INPUT / "resultados" / "predicciones" / "total_ses.csv",
            parse_dates=["fecha"],
        ).set_index("fecha")["prediccion"]
        self.assertEqual(len(self.forecast), 63)
        self.assertEqual(self.forecast.index[0], pd.Timestamp("2021-04-01"))
        self.assertEqual(self.forecast.index[-1], pd.Timestamp("2026-06-01"))
        pd.testing.assert_index_equal(self.forecast.index, saved.index, check_names=False)
        np.testing.assert_allclose(self.forecast["forecast"], saved, atol=0.01, rtol=0)
        np.testing.assert_allclose(self.forecast["forecast"], 105145, atol=1, rtol=0)
        np.testing.assert_allclose(
            self.forecast.iloc[0][["lower_80", "upper_80", "lower_95", "upper_95"]],
            [69000, 160000, 55000, 200000], rtol=0.02,
        )
        np.testing.assert_allclose(
            self.forecast.iloc[-1][["lower_95", "upper_80", "upper_95"]],
            [640, 2950000, 17300000], rtol=0.03,
        )
        for level in (80, 95):
            self.assertTrue(self.forecast[f"upper_{level}"].is_monotonic_increasing)
            self.assertTrue(self.forecast[f"lower_{level}"].is_monotonic_decreasing)
        self.assertTrue((self.forecast["lower_95"] < self.forecast["lower_80"]).all())
        self.assertTrue((self.forecast["upper_95"] > self.forecast["upper_80"]).all())

    def test_model_metrics_match_predictions(self):
        metrics = pd.read_csv(charts.INPUT / "resultados" / "metricas_modelos.csv")
        actual = self.total.loc["2021-04":"2026-06"].to_numpy()
        for row in metrics.loc[metrics["serie"].eq("total")].itertuples():
            with self.subTest(model=row.modelo):
                prediction = pd.read_csv(
                    charts.INPUT / "resultados" / "predicciones" / f"total_{row.modelo}.csv"
                )["prediccion"].to_numpy()
                error = actual - prediction
                self.assertAlmostEqual(np.mean(np.abs(error)), row.mae, places=6)
                self.assertAlmostEqual(np.sqrt(np.mean(error ** 2)), row.rmse, places=6)

    def test_chart_sizes_fonts_and_text_bounds(self):
        figures = [
            charts.panorama(self.total), charts.seasonality(self.total),
            charts.route_comparison(), charts.models(),
            charts.forecast_chart(self.total, self.forecast),
        ]
        for filename, figure in zip(charts.SIZES, figures):
            with self.subTest(chart=filename):
                np.testing.assert_allclose(figure.get_size_inches(), charts.SIZES[filename])
                self.assertEqual(figure.dpi, 300)
                figure.canvas.draw()
                renderer = figure.canvas.get_renderer()
                width, height = figure.bbox.size
                texts = list(figure.texts)
                for axis in figure.axes:
                    texts.extend(axis.texts)
                    for locations, labels, limits in (
                        (axis.get_xticks(), axis.get_xticklabels(), axis.get_xlim()),
                        (axis.get_yticks(), axis.get_yticklabels(), axis.get_ylim()),
                    ):
                        texts.extend(label for location, label in zip(locations, labels)
                                     if min(limits) <= location <= max(limits))
                for text in texts:
                    if not text.get_visible() or not text.get_text():
                        continue
                    self.assertGreaterEqual(text.get_fontsize(), 11, text.get_text())
                    bounds = text.get_window_extent(renderer)
                    self.assertGreaterEqual(bounds.x0, -1, text.get_text())
                    self.assertGreaterEqual(bounds.y0, -1, text.get_text())
                    self.assertLessEqual(bounds.x1, width + 1, text.get_text())
                    self.assertLessEqual(bounds.y1, height + 1, text.get_text())
                with Image.open(charts.OUTPUT / filename) as image:
                    expected = tuple(int(size * 300) for size in charts.SIZES[filename])
                    self.assertEqual(image.size, expected)
                    self.assertAlmostEqual(image.info["dpi"][0], 300, places=1)
            plt.close(figure)

    def test_bars_start_at_zero_and_forecast_limit_is_explicit(self):
        for figure, horizontal in (
            (charts.seasonality(self.total), False),
            (charts.route_comparison(), True),
            (charts.models(), True),
        ):
            for axis in figure.axes:
                for bar in axis.patches:
                    self.assertEqual(bar.get_x() if horizontal else bar.get_y(), 0)
            plt.close(figure)
        figure = charts.forecast_chart(self.total, self.forecast)
        self.assertEqual(figure.axes[0].get_ylim(), (0, 700000))
        self.assertTrue(any("17 M" in text.get_text() for text in figure.texts))
        plt.close(figure)


if __name__ == "__main__":
    unittest.main()
