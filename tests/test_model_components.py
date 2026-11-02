import os
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app import model_results
from app.approved import APPROVED_DIR_VARIABLE, load_approved
from app.components import model_errors
from app.theme import COLORS
from docs.scripts.preview_model_results import build_app
from tests.test_approved_contract import SAMPLE_DIR


class ValidationMetricTests(unittest.TestCase):
    def setUp(self):
        self.version = load_approved(SAMPLE_DIR / "current")

    def with_scores(self, procedure, baseline):
        metrics = self.version["metrics"]
        return {**self.version, "metrics": {
            **metrics, "procedure": {**metrics["procedure"], **procedure}, "baseline": {**metrics["baseline"], **baseline},
        }}

    def test_each_metric_compares_procedure_and_baseline_from_metrics_json(self):
        metrics = self.version["metrics"]
        for metric in model_errors.METRICS:
            with self.subTest(metric=metric):
                figure, note = model_errors.build_figure(self.version, metric)
                bars = figure.data[0]
                self.assertEqual(list(bars.x), [metrics["procedure"][metric], metrics["baseline"][metric]])
                self.assertEqual(list(bars.y), ["Holt-Winters (versión aprobada)", "Referencia estacional"])
                self.assertEqual(list(bars.marker.color), [COLORS["forecast"], COLORS["muted"]])
                self.assertIn("12 meses evaluados entre julio de 2025 y junio de 2026", note)
        _, note = model_errors.build_figure(self.version, "mape_pct")
        self.assertIn("Los meses registrados en cero no entran en este porcentaje.", note)

    def test_missing_scores_are_explained_instead_of_plotted(self):
        figure, note = model_errors.build_figure(self.with_scores({"mape_pct": None}, {"mape_pct": None}), "mape_pct")
        self.assertFalse(figure.data)
        self.assertIn("no hay meses evaluados con valor registrado distinto de cero", note)
        figure, _ = model_errors.build_figure(self.with_scores({}, {"mape_pct": None}), "mape_pct")
        self.assertEqual(list(figure.data[0].y), ["Holt-Winters (versión aprobada)"])
        figure, note = model_errors.build_figure(self.version, "desconocida")
        self.assertFalse(figure.data)
        self.assertIn("Seleccione", note)

    def test_missing_version_hides_the_chart(self):
        figure, _, content, unavailable = model_errors.build_view(None, "mae")
        self.assertFalse(figure.data)
        self.assertEqual((content, unavailable), (model_errors.HIDDEN, model_errors.SHOWN))


class ValidationCallbackTests(unittest.TestCase):
    def setUp(self):
        self.client = build_app().server.test_client()
        folder = Path(self.enterContext(TemporaryDirectory())) / "current"
        shutil.copytree(SAMPLE_DIR / "current", folder)
        self.enterContext(patch.dict(os.environ, {APPROVED_DIR_VARIABLE: str(folder)}))
        model_results._cache.update(key=None, version=None)

    def test_metric_changes_through_http(self):
        values = []
        for metric in ["mae", "mape_pct"]:
            response = self.client.post("/_dash-update-component", json={
                "output": "..errors-graph.figure...errors-note.children...errors-content.style...errors-unavailable.style..",
                "outputs": [{"id": "errors-graph", "property": "figure"}, {"id": "errors-note", "property": "children"},
                            {"id": "errors-content", "property": "style"}, {"id": "errors-unavailable", "property": "style"}],
                "changedPropIds": ["errors-metric.value"],
                "inputs": [{"id": "errors-metric", "property": "value", "value": metric}],
                "state": [],
            })
            self.assertEqual(response.status_code, 200)
            values.append(response.get_json()["response"]["errors-graph"]["figure"]["data"][0]["x"])
        self.assertEqual(values, [[250.0, 400.0], [2.0, 3.5]])


if __name__ == "__main__":
    unittest.main()
