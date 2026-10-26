import unittest
from unittest.mock import patch

import pandas as pd

from app.components import model_deviations, model_errors
from docs.scripts.preview_model_results import build_app


class ModelComponentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = build_app()
        cls.client = cls.app.server.test_client()

    def test_live_sources_support_every_series_and_metric(self):
        for series_key in model_errors.LABELS.index:
            for metric in model_errors.METRICS:
                figure, note = model_errors.build_figure(series_key, metric)
                self.assertEqual(len(figure.data[0].x), 5)
                self.assertIn("63 meses coincidentes", note)
            for model_key in model_deviations.model_results.available_models(series_key):
                figure, note = model_deviations.build_figure(series_key, model_key, None, None)
                self.assertEqual(len(figure.data[0].y), 63)
                self.assertEqual(figure.layout.shapes[0].y0, 0)

    def test_empty_period_and_invalid_model_produce_messages(self):
        for model, first, last in [("ses", "2009-01-01", "2010-01-01"), (None, None, None)]:
            figure, note = model_deviations.build_figure("total", model, first, last)
            self.assertFalse(figure.data)
            self.assertTrue(figure.layout.annotations[0].text)
        figure, note = model_errors.build_figure("total", "desconocida")
        self.assertFalse(figure.data)
        self.assertIn("Seleccione", note)

    def test_missing_month_breaks_the_deviation_line(self):
        dates = pd.to_datetime(["2024-01-01", "2024-03-01"])
        frame = pd.DataFrame({"observed": [10.0, 40.0], "predicted": [8.0, 50.0], "error": [2.0, -10.0]}, index=dates)
        with patch.object(model_deviations.model_results, "align_observations", return_value=frame):
            figure, note = model_deviations.build_figure("total", "ses", None, None)
        self.assertEqual(list(figure.data[0].y), [2.0, None, -10.0])
        self.assertFalse(figure.data[0].connectgaps)

    def test_preview_serves_both_components_and_their_callbacks(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        layout = self.client.get("/_dash-layout").get_data(as_text=True)
        for identifier in ["errors-series", "errors-metric", "errors-graph", "deviations-series", "deviations-model", "deviations-dates", "deviations-graph"]:
            self.assertIn(identifier, layout)
        self.assertEqual(len(self.client.get("/_dash-dependencies").get_json()), 3)

    def test_error_metric_changes_through_http(self):
        values = []
        for metric in ["mae", "mape"]:
            response = self.client.post("/_dash-update-component", json={
                "output": "..errors-graph.figure...errors-note.children..",
                "outputs": [{"id": "errors-graph", "property": "figure"}, {"id": "errors-note", "property": "children"}],
                "changedPropIds": ["errors-metric.value"],
                "inputs": [{"id": "errors-series", "property": "value", "value": "total"}, {"id": "errors-metric", "property": "value", "value": metric}],
                "state": [],
            })
            self.assertEqual(response.status_code, 200)
            values.append(response.get_json()["response"]["errors-graph"]["figure"]["data"][0]["x"])
        self.assertNotEqual(values[0], values[1])

    def test_period_filter_updates_deviations_through_http(self):
        response = self.client.post("/_dash-update-component", json={
            "output": "..deviations-graph.figure...deviations-note.children..",
            "outputs": [{"id": "deviations-graph", "property": "figure"}, {"id": "deviations-note", "property": "children"}],
            "changedPropIds": ["deviations-dates.start_date"],
            "inputs": [
                {"id": "deviations-series", "property": "value", "value": "total"},
                {"id": "deviations-model", "property": "value", "value": "ses"},
                {"id": "deviations-dates", "property": "start_date", "value": "2025-01-01"},
                {"id": "deviations-dates", "property": "end_date", "value": "2025-12-31"},
            ],
            "state": [],
        })
        self.assertEqual(response.status_code, 200)
        figure = response.get_json()["response"]["deviations-graph"]["figure"]
        self.assertEqual(len(figure["data"][0]["y"]), 12)


if __name__ == "__main__":
    unittest.main()
