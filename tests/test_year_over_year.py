import math
import unittest
from unittest.mock import patch

import pandas as pd

from app import data
from app.components import year_over_year
from app.main import app


def monthly(values, start="2023-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="MS"), dtype=float)


class YearOverYearTests(unittest.TestCase):
    def test_variation_matches_manual_calculation_from_source(self):
        source = data.load_series("total")
        frame = year_over_year.year_over_year(data.monthly_series("total"))
        manual = (source[pd.Timestamp("2025-01-01")] / source[pd.Timestamp("2024-01-01")] - 1) * 100
        self.assertTrue(math.isclose(frame.loc["2025-01-01", "variation"], manual))
        self.assertTrue(math.isclose(manual, -8.0646854, rel_tol=1e-6))

    def test_first_year_has_no_base_and_is_not_zero(self):
        frame = year_over_year.year_over_year(data.monthly_series("total"))
        first_year = frame.loc["2009"]
        self.assertTrue(first_year["variation"].isna().all())
        self.assertEqual(set(first_year["reason"]), {"missing_previous"})

    def test_zero_and_missing_bases_are_explained_instead_of_filled(self):
        values = [0, 10, None, 40] + [5] * 8 + [7, 20, 30, None] + [5] * 8
        with patch.object(data, "load_series", return_value=monthly(values)):
            frame = year_over_year.year_over_year(data.monthly_series("total"))
            figure, note = year_over_year.build_figure("total", "2024-01-01", "2024-12-01")
        self.assertEqual(frame.loc["2024-01-01", "reason"], "zero_previous")
        self.assertEqual(frame.loc["2024-02-01", "variation"], 100)
        self.assertEqual(frame.loc["2024-03-01", "reason"], "missing_previous")
        self.assertEqual(frame.loc["2024-04-01", "reason"], "missing_current")
        self.assertEqual(len(figure.data[0].x), 9)
        self.assertEqual(len(figure.data[1].x), 3)
        self.assertEqual(list(figure.data[1].y), [0, 0, 0])
        self.assertIn("3 meses no se pueden calcular", note)
        self.assertIn("registró cero viajeros", note)

    def test_previous_month_is_matched_by_date_not_by_position(self):
        dates = pd.to_datetime(["2023-01-01", "2023-03-01", "2024-01-01", "2024-02-01", "2024-03-01"])
        source = pd.Series([10.0, 20.0, 15.0, 99.0, 30.0], index=dates)
        frame = year_over_year.year_over_year(source)
        self.assertEqual(frame.loc["2024-01-01", "variation"], 50)
        self.assertEqual(frame.loc["2024-02-01", "reason"], "missing_previous")
        self.assertEqual(frame.loc["2024-03-01", "variation"], 50)

    def test_real_zero_bases_in_maritime_series_are_not_computed(self):
        frame = year_over_year.year_over_year(data.monthly_series("via_maritima"))
        zero_bases = frame[frame["reason"] == "zero_previous"]
        self.assertGreater(len(zero_bases), 0)
        self.assertTrue(zero_bases["variation"].isna().all())

    def test_bars_plot_the_computed_values(self):
        figure, note = year_over_year.build_figure("via_aerea", "2025-01-01", "2025-12-31")
        frame = year_over_year.year_over_year(data.monthly_series("via_aerea")).loc["2025"]
        self.assertEqual(len(figure.data), 1)
        self.assertEqual(list(figure.data[0].y), frame["variation"].tolist())
        self.assertIn("Vía Aérea · enero de 2025 a diciembre de 2025. 12 meses", note)
        self.assertIn("Todos los meses del rango tienen una base válida", note)

    def test_unavailable_selections_show_messages_without_bars(self):
        for key, start, end, expected in [
            ("total", "2009-01-01", "2009-12-31", "ningún mes"),
            ("total", "2025-01-01", "2024-12-31", "fecha inicial"),
            ("total", "fecha", "2024-12-31", "rango de fechas válido"),
            ("unknown", "2025-01-01", "2025-12-31", "serie disponible"),
        ]:
            figure, note = year_over_year.build_figure(key, start, end)
            self.assertFalse(figure.data)
            self.assertIn(expected, note)

    def test_callback_changes_figure_over_http(self):
        client = app.server.test_client()
        results = []
        for key in ["total", "pais_honduras"]:
            response = client.post("/_dash-update-component", json={
                "output": "..yoy-graph.figure...yoy-note.children..",
                "outputs": [{"id": "yoy-graph", "property": "figure"}, {"id": "yoy-note", "property": "children"}],
                "changedPropIds": ["yoy-series.value"],
                "inputs": [
                    {"id": "yoy-series", "property": "value", "value": key},
                    {"id": "yoy-dates", "property": "start_date", "value": "2024-01-01"},
                    {"id": "yoy-dates", "property": "end_date", "value": "2024-12-31"},
                ],
                "state": [],
            })
            self.assertEqual(response.status_code, 200)
            results.append(response.get_json()["response"]["yoy-graph"]["figure"]["data"][0]["y"])
        self.assertNotEqual(results[0], results[1])


if __name__ == "__main__":
    unittest.main()
