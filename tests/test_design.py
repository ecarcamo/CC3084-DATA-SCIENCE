import math
import unittest
from unittest.mock import patch

import pandas as pd

from app import data
from app.components import annual_comparison, seasonality
from app.theme import COLORS, FONT_FAMILY
from docs.scripts.preview_design import build_app


def graph_request(prefix, series_key, years, changed):
    return {
        "output": f"..{prefix}-graph.figure...{prefix}-note.children..",
        "outputs": [{"id": f"{prefix}-graph", "property": "figure"}, {"id": f"{prefix}-note", "property": "children"}],
        "changedPropIds": [changed],
        "inputs": [
            {"id": f"{prefix}-series", "property": "value", "value": series_key},
            {"id": f"{prefix}-years", "property": "value", "value": years},
        ],
        "state": [],
    }


def identifiers(component):
    found = [component.id] if getattr(component, "id", None) else []
    children = getattr(component, "children", [])
    for child in children if isinstance(children, list) else [children]:
        if hasattr(child, "children") or getattr(child, "id", None):
            found.extend(identifiers(child))
    return found


class MonthlyDataTests(unittest.TestCase):
    def test_current_sources_have_unique_monthly_coverage_and_valid_values(self):
        for key in data.load_labels().index:
            series = data.monthly_series(key)
            self.assertEqual(len(series), 210)
            self.assertEqual(series.index.min(), pd.Timestamp("2009-01-01"))
            self.assertEqual(series.index.max(), pd.Timestamp("2026-06-01"))
            self.assertFalse(series.isna().any())
            self.assertEqual(len(pd.date_range(series.index.min(), series.index.max(), freq="MS").difference(series.index)), 0)

    def test_invalid_values_remain_missing_and_zero_remains_valid(self):
        source = pd.Series([0, None, float("inf"), -1, "bad", 10], index=pd.date_range("2024-01-01", periods=6, freq="MS"))
        with patch.object(data, "load_series", return_value=source):
            series = data.monthly_series("total")
        self.assertEqual(series.iloc[0], 0)
        self.assertTrue(series.iloc[1:5].isna().all())
        self.assertEqual(series.iloc[5], 10)

    def test_repeated_months_are_rejected_instead_of_counting_as_complete_years(self):
        dates = list(pd.date_range("2024-01-01", periods=11, freq="MS")) + [pd.Timestamp("2024-01-01")]
        with patch.object(data, "load_series", return_value=pd.Series(10.0, index=dates)):
            with self.assertRaisesRegex(ValueError, "meses repetidos"):
                data.monthly_series("total")

    def test_invalid_dates_and_non_month_start_dates_are_rejected(self):
        for dates in [[pd.NaT], ["invalid"], [pd.Timestamp("2024-01-15")]]:
            with patch.object(data, "load_series", return_value=pd.Series([10], index=dates)):
                with self.assertRaises(ValueError):
                    data.monthly_series("total")

    def test_unsorted_months_are_sorted_and_absent_months_are_not_zero(self):
        source = pd.Series([30, 10], index=pd.to_datetime(["2024-03-01", "2024-01-01"]))
        with patch.object(data, "load_series", return_value=source):
            selected = data.select_years(data.monthly_series("total"), [2024, 2024])
        self.assertEqual(len(selected), 12)
        self.assertEqual(selected.iloc[0], 10)
        self.assertTrue(pd.isna(selected.iloc[1]))
        self.assertEqual(selected.iloc[2], 30)

    def test_invalid_ranges_and_unknown_series_are_rejected(self):
        series = data.monthly_series("total")
        for years in [None, [], [2024], [2025, 2024], [2008, 2024], [2024, 2027], ["2024", "2025"]]:
            with self.assertRaises(ValueError):
                data.select_years(series, years)
        with self.assertRaisesRegex(ValueError, "serie disponible"):
            data.monthly_series("../unknown")


class DesignComponentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = build_app()
        cls.client = cls.app.server.test_client()

    def test_heatmap_orders_months_and_years_and_plots_source_values(self):
        for key in data.load_labels().index:
            figure, note = seasonality.build_figure(key, [2024, 2025])
            heatmap = figure.data[0]
            self.assertEqual(heatmap.type, "heatmap")
            self.assertEqual(list(heatmap.x), list(range(1, 13)))
            self.assertEqual(list(heatmap.y), [2024, 2025])
            self.assertEqual(list(heatmap.z[0]), data.load_series(key).loc["2024"].tolist())
            self.assertEqual(figure.layout.yaxis.autorange, "reversed")
            self.assertEqual(heatmap.colorbar.title.text, "Viajeros por mes")
            self.assertEqual(heatmap.zmin, 0)
            self.assertEqual(heatmap.colorscale[-1][1], COLORS["observed"])
            self.assertIn("24 meses con dato válido", note)
            self.assertIn("no demuestra sus causas", note)

    def test_heatmap_distinguishes_absent_invalid_and_zero_months(self):
        source = pd.Series([0, float("inf"), 30], index=pd.to_datetime(["2024-01-01", "2024-02-01", "2024-04-01"]))
        with patch.object(data, "load_series", return_value=source):
            figure, note = seasonality.build_figure("total", [2024, 2024])
        self.assertEqual(figure.data[0].z[0][0], 0)
        self.assertIsNone(figure.data[0].z[0][1])
        self.assertIsNone(figure.data[0].z[0][2])
        missing = figure.data[1]
        self.assertEqual(missing.marker.symbol, "x")
        self.assertNotIn(1, missing.x)
        self.assertIn(2, missing.x)
        self.assertIn(3, missing.x)
        self.assertIn("10 sin dato válido", note)

    def test_partial_2026_is_visible_in_heatmap_but_not_in_annual_totals(self):
        heatmap, heatmap_note = seasonality.build_figure("total", [2026, 2026])
        self.assertEqual(len([value for value in heatmap.data[0].z[0] if value is not None]), 6)
        self.assertIn("6 sin dato válido", heatmap_note)
        annual, note = annual_comparison.build_figure("total", [2026, 2026])
        self.assertFalse(annual.data)
        self.assertEqual(annual.layout.annotations[0].text.replace("<br>", " "), annual_comparison.EMPTY_MESSAGE)
        self.assertIn("2026: 6 de 12 meses válidos", note)
        self.assertIn("Se excluyó 1 año incompleto", note)

    def test_every_annual_total_matches_its_twelve_months_for_every_series(self):
        for key in data.load_labels().index:
            figure, note = annual_comparison.build_figure(key, [2009, 2026])
            bars = figure.data[0]
            self.assertEqual(list(bars.x), list(range(2009, 2026)))
            monthly = data.load_series(key)
            for year, total in zip(bars.x, bars.y):
                self.assertTrue(math.isclose(total, monthly.loc[str(year)].sum(), rel_tol=1e-12))
            self.assertEqual(figure.layout.yaxis.rangemode, "tozero")
            self.assertEqual(bars.marker.color, COLORS["observed"])
            self.assertIn("2026: 6 de 12 meses válidos", note)

    def test_year_with_twelve_months_including_a_zero_is_complete(self):
        source = pd.Series([0] + [10] * 11, index=pd.date_range("2024-01-01", periods=12, freq="MS"))
        with patch.object(data, "load_series", return_value=source):
            figure, note = annual_comparison.build_figure("total", [2024, 2024])
        self.assertEqual(list(figure.data[0].y), [110])
        self.assertIn("No se excluyeron años incompletos", note)

    def test_missing_or_invalid_month_excludes_year_without_filling_it(self):
        original = pd.Series(10.0, index=pd.date_range("2024-01-01", periods=12, freq="MS"))
        for source in [original.drop(original.index[5]), original.mask(original.index.month == 6), original.where(original.index.month != 6, float("inf"))]:
            with patch.object(data, "load_series", return_value=source):
                figure, note = annual_comparison.build_figure("total", [2024, 2024])
            self.assertFalse(figure.data)
            self.assertIn("2024: 11 de 12 meses válidos", note)

    def test_entire_absent_year_is_explained(self):
        dates = pd.date_range("2023-01-01", periods=12, freq="MS").append(pd.date_range("2025-01-01", periods=12, freq="MS"))
        with patch.object(data, "load_series", return_value=pd.Series(10.0, index=dates)):
            figure, note = annual_comparison.build_figure("total", [2023, 2025])
        self.assertEqual(list(figure.data[0].x), [2023, 2025])
        self.assertIn("2024: 0 de 12 meses válidos", note)

    def test_unavailable_selections_have_messages_and_no_traces(self):
        for component in [seasonality, annual_comparison]:
            for key, years in [("unknown", [2024, 2025]), ("total", [2025, 2024]), ("total", None)]:
                figure, note = component.build_figure(key, years)
                self.assertFalse(figure.data)
                self.assertTrue(note)
                self.assertTrue(all(len(line) <= 32 for line in figure.layout.annotations[0].text.split("<br>")))
            with patch.object(data, "load_series", return_value=pd.Series(float("nan"), index=pd.date_range("2024-01-01", periods=12, freq="MS"))):
                figure, note = component.build_figure("total", [2024, 2024])
                self.assertFalse(figure.data)
                self.assertIn("No hay", note)

    def test_duplicate_months_produce_actionable_messages(self):
        source = pd.Series([10, 20], index=pd.to_datetime(["2024-01-01", "2024-01-01"]))
        for component in [seasonality, annual_comparison]:
            with patch.object(data, "load_series", return_value=source):
                figure, note = component.build_figure("total", [2024, 2024])
            self.assertFalse(figure.data)
            self.assertIn("meses repetidos", note)

    def test_year_options_follow_each_series_coverage(self):
        source = pd.Series([10, 20], index=pd.to_datetime(["2019-02-01", "2022-06-01"]))
        for component in [seasonality, annual_comparison]:
            with patch.object(data, "load_series", return_value=source):
                first, last, marks, selected = component.year_options("total")
            self.assertEqual((first, last), (2019, 2022))
            self.assertEqual(selected, [2019, 2022])
            self.assertEqual(marks, {2019: "2019", 2022: "2022"})

    def test_preview_has_unique_ids_and_does_not_duplicate_shared_callbacks(self):
        ids = identifiers(self.app.layout)
        self.assertEqual(len(ids), len(set(ids)))
        for identifier in ["seasonality-graph", "annual-graph", "predictions-graph", "errors-graph", "deviations-graph"]:
            self.assertIn(identifier, ids)
        response = self.client.get("/_dash-layout")
        self.assertEqual(response.status_code, 200)
        dependencies = self.client.get("/_dash-dependencies").get_json()
        linked = [item for item in dependencies if item["output"] == "series-selector.value"]
        self.assertEqual(len(linked), 1)
        self.assertEqual(linked[0]["inputs"], [{"id": "ranking-graph", "property": "clickData"}])

    def test_both_graph_callbacks_change_visible_data_for_series_and_year_filters(self):
        for prefix in ["seasonality", "annual"]:
            results = []
            for key, years, changed in [
                ("total", [2024, 2025], f"{prefix}-years.value"),
                ("via_aerea", [2024, 2025], f"{prefix}-series.value"),
                ("via_aerea", [2025, 2025], f"{prefix}-years.value"),
            ]:
                response = self.client.post("/_dash-update-component", json=graph_request(prefix, key, years, changed))
                self.assertEqual(response.status_code, 200)
                body = response.get_json()["response"]
                results.append(body[f"{prefix}-graph"]["figure"]["data"][0])
                self.assertTrue(body[f"{prefix}-note"]["children"])
            field = "z" if prefix == "seasonality" else "y"
            self.assertNotEqual(results[0][field], results[1][field])
            self.assertEqual(len(results[2][field]), 1)

    def test_both_year_range_callbacks_use_source_coverage(self):
        for prefix in ["seasonality", "annual"]:
            properties = ["min", "max", "marks", "value"]
            response = self.client.post("/_dash-update-component", json={
                "output": ".." + "...".join(f"{prefix}-years.{prop}" for prop in properties) + "..",
                "outputs": [{"id": f"{prefix}-years", "property": prop} for prop in properties],
                "changedPropIds": [f"{prefix}-series.value"],
                "inputs": [{"id": f"{prefix}-series", "property": "value", "value": "via_aerea"}],
                "state": [],
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["response"][f"{prefix}-years"]["value"], [2009, 2026])

    def test_new_graphs_reuse_shared_typography(self):
        for component in [seasonality, annual_comparison]:
            figure, note = component.build_figure("total", [2024, 2025])
            self.assertEqual(figure.layout.template.layout.font.family, FONT_FAMILY)
            self.assertIn("total", note.lower())


if __name__ == "__main__":
    unittest.main()
