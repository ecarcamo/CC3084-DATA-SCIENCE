import unittest
from unittest.mock import patch

import pandas as pd

from app.components import predictions
from app.theme import COLORS
from docs.scripts.preview_predictions import build_app

GRAPH_OUTPUTS = [{"id": "predictions-graph", "property": "figure"}, {"id": "predictions-note", "property": "children"}]


def graph_request(series_key, model_keys, start, end, changed):
    return {
        "output": "..predictions-graph.figure...predictions-note.children..",
        "outputs": GRAPH_OUTPUTS,
        "changedPropIds": [changed],
        "inputs": [
            {"id": "predictions-series", "property": "value", "value": series_key},
            {"id": "predictions-models", "property": "value", "value": model_keys},
            {"id": "predictions-dates", "property": "start_date", "value": start},
            {"id": "predictions-dates", "property": "end_date", "value": end},
        ],
        "state": [],
    }


class PredictionComponentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = build_app()
        cls.client = cls.app.server.test_client()

    def test_every_series_compares_at_least_three_models_on_shared_dates(self):
        for series_key in predictions.LABELS.index:
            options, selected = predictions.model_options(series_key)
            self.assertGreaterEqual(len(options), 3)
            self.assertEqual(len(selected), predictions.DEFAULT_MODEL_COUNT)
            figure, note = predictions.build_figure(series_key, [option["value"] for option in options], None, None)
            self.assertEqual(len(figure.data), len(options) + 1)
            dates = [list(trace.x) for trace in figure.data]
            self.assertTrue(all(trace_dates == dates[0] for trace_dates in dates))
            self.assertEqual(len(dates[0]), 63)
            self.assertEqual(pd.Timestamp(dates[0][0]), pd.Timestamp("2021-04-01"))
            self.assertEqual(pd.Timestamp(dates[0][-1]), pd.Timestamp("2026-06-01"))
            self.assertIn("63 meses", note)
            self.assertIn("no son un pronóstico", note)

    def test_observed_and_estimates_differ_by_label_style_and_color(self):
        figure, _ = predictions.build_figure("total", ["sarima", "ses", "prophet"], None, None)
        observed, *estimates = figure.data
        self.assertEqual(observed.name, predictions.OBSERVED_NAME)
        self.assertEqual(observed.line.dash, "solid")
        self.assertEqual(observed.line.color, COLORS["observed"])
        self.assertEqual([trace.name for trace in estimates], ["Estimado · SARIMA", "Estimado · SES", "Estimado · Prophet"])
        self.assertEqual(len({trace.line.dash for trace in estimates}), 3)
        self.assertNotIn("solid", {trace.line.dash for trace in estimates})
        self.assertNotIn(COLORS["observed"], {trace.line.color for trace in estimates})
        self.assertTrue(figure.layout.showlegend)

    def test_plotted_values_come_from_existing_files(self):
        figure, _ = predictions.build_figure("via_aerea", ["holt_winters"], "2024-01-01", "2024-12-31")
        observed = predictions.model_results.load_observations("via_aerea").loc["2024"]
        estimated = predictions.model_results.load_predictions("via_aerea", "holt_winters").loc["2024"]
        self.assertEqual(list(figure.data[0].y), observed.tolist())
        self.assertEqual(list(figure.data[1].y), estimated.tolist())

    def test_only_dates_shared_by_observations_and_every_model_are_plotted(self):
        dates = pd.date_range("2024-01-01", periods=4, freq="MS")
        observed = pd.Series([100.0, 200.0, 300.0, 400.0], index=dates, name="observed")
        forecasts = {
            "ses": pd.Series([90.0, 180.0, 310.0], index=dates[:3], name="predicted"),
            "sarima": pd.Series([210.0, 290.0, 420.0], index=dates[1:], name="predicted"),
        }
        with patch.object(predictions.model_results, "load_observations", return_value=observed), patch.object(
            predictions.model_results, "load_predictions", side_effect=lambda series, model: forecasts[model]
        ):
            figure, note = predictions.build_figure("total", ["ses", "sarima"], None, None)
        self.assertEqual([pd.Timestamp(date) for date in figure.data[0].x], list(dates[1:3]))
        self.assertEqual(list(figure.data[1].y), [210.0, 290.0])
        self.assertEqual(list(figure.data[2].y), [180.0, 310.0])
        self.assertIn("2 meses", note)

    def test_missing_month_breaks_lines_instead_of_interpolating(self):
        dates = pd.to_datetime(["2024-01-01", "2024-03-01"])
        frame = pd.DataFrame({"observed": [10.0, 40.0], "ses": [8.0, 50.0]}, index=dates)
        with patch.object(predictions.model_results, "align_models", return_value=frame):
            figure, _ = predictions.build_figure("total", ["ses"], None, None)
        self.assertEqual(list(figure.data[0].y), [10.0, None, 40.0])
        self.assertEqual(list(figure.data[1].y), [8.0, None, 50.0])
        self.assertFalse(figure.data[1].connectgaps)

    def test_unavailable_selections_show_messages_without_inventing_data(self):
        cases = [
            ("total", [], None, None, predictions.NO_MODELS_MESSAGE),
            ("total", ["ses"], "2009-01-01", "2010-12-31", predictions.EMPTY_MESSAGE),
            ("total", ["desconocido"], None, None, "Seleccione un modelo disponible."),
            ("total", ["ses"], "2025-01-01", "2024-01-01", "La fecha inicial"),
        ]
        for series_key, model_keys, start, end, message in cases:
            figure, note = predictions.build_figure(series_key, model_keys, start, end)
            self.assertFalse(figure.data)
            self.assertIn(message, figure.layout.annotations[0].text)
            self.assertIn(message, note)

    def test_missing_model_file_is_reported(self):
        with patch.object(predictions.model_results, "available_models", return_value=["ses", "sarima"]):
            figure, note = predictions.build_figure("total", ["ses", "prophet"], None, None)
        self.assertFalse(figure.data)
        self.assertIn("No hay estimaciones de Prophet", note)

    def test_series_change_keeps_selected_models_that_remain_available(self):
        with patch.object(predictions.model_results, "available_models", return_value=["ses", "prophet"]):
            options, selected = predictions.model_options("total", ["sarima", "prophet", "ses"])
        self.assertEqual([option["value"] for option in options], ["ses", "prophet"])
        self.assertEqual(selected, ["ses", "prophet"])

    def test_preview_serves_g1_and_g6_identifiers(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        layout = self.client.get("/_dash-layout").get_data(as_text=True)
        for identifier in [
            "series-selector", "granularity-selector", "date-range", "time-series-graph",
            "predictions-series", "predictions-models", "predictions-dates", "predictions-graph", "predictions-note",
        ]:
            self.assertIn(f'"{identifier}"', layout)
        self.assertEqual(len(self.client.get("/_dash-dependencies").get_json()), 3)

    def test_models_and_period_update_the_figure_through_http(self):
        responses = [
            graph_request("total", ["sarima", "holt_winters", "ses"], "2021-04-01", "2026-06-30", "predictions-models.value"),
            graph_request("total", ["sarima", "holt_winters", "ses", "prophet"], "2021-04-01", "2026-06-30", "predictions-models.value"),
            graph_request("total", ["sarima", "holt_winters", "ses"], "2025-01-01", "2025-12-31", "predictions-dates.start_date"),
            graph_request("pais_honduras", ["sarima", "holt_winters", "ses"], "2025-01-01", "2025-12-31", "predictions-series.value"),
        ]
        figures = []
        for payload in responses:
            response = self.client.post("/_dash-update-component", json=payload)
            self.assertEqual(response.status_code, 200)
            figures.append(response.get_json()["response"]["predictions-graph"]["figure"])
        self.assertEqual(len(figures[0]["data"]), 4)
        self.assertEqual(len(figures[1]["data"]), 5)
        self.assertEqual(len(figures[2]["data"][0]["y"]), 12)
        self.assertNotEqual(figures[2]["data"][0]["y"], figures[3]["data"][0]["y"])

    def test_series_change_updates_model_options_through_http(self):
        response = self.client.post("/_dash-update-component", json={
            "output": "..predictions-models.options...predictions-models.value..",
            "outputs": [{"id": "predictions-models", "property": "options"}, {"id": "predictions-models", "property": "value"}],
            "changedPropIds": ["predictions-series.value"],
            "inputs": [{"id": "predictions-series", "property": "value", "value": "via_maritima"}],
            "state": [{"id": "predictions-models", "property": "value", "value": ["prophet", "ses"]}],
        })
        self.assertEqual(response.status_code, 200)
        result = response.get_json()["response"]["predictions-models"]
        self.assertEqual(len(result["options"]), 5)
        self.assertEqual(result["value"], ["ses", "prophet"])


if __name__ == "__main__":
    unittest.main()
