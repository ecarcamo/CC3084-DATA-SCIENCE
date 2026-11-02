import os
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from app import approved, model_results
from app.approved import APPROVED_DIR_VARIABLE, load_approved
from app.components import predictions
from app.theme import COLORS
from docs.scripts.preview_predictions import build_app
from tests.test_approved_contract import SAMPLE_DIR

OUTPUTS = [
    ("predictions-graph", "figure"), ("predictions-note", "children"), ("predictions-details", "children"),
    ("predictions-warning", "children"), ("predictions-content", "style"), ("predictions-unavailable", "style"),
]


def history_request(months):
    return {
        "output": ".." + "...".join(f"{identifier}.{prop}" for identifier, prop in OUTPUTS) + "..",
        "outputs": [{"id": identifier, "property": prop} for identifier, prop in OUTPUTS],
        "changedPropIds": ["predictions-history.value"],
        "inputs": [{"id": "predictions-history", "property": "value", "value": months}],
        "state": [],
    }


def text(children):
    if isinstance(children, (list, tuple)):
        return "".join(text(child) for child in children)
    if hasattr(children, "children"):
        return text(children.children)
    return "" if children is None else str(children)


class PredictionViewTests(unittest.TestCase):
    def setUp(self):
        self.version = load_approved(SAMPLE_DIR / "current")

    def test_observed_and_estimated_come_from_the_same_version_with_distinct_styles(self):
        figure = predictions.build_figure(self.version, 0)
        observed, estimated = figure.data
        self.assertEqual(observed.name, predictions.KIND_STYLES["observado"]["name"])
        self.assertEqual((observed.line.dash, observed.line.color), ("solid", COLORS["observed"]))
        self.assertEqual(estimated.name, predictions.KIND_STYLES["estimado"]["name"])
        self.assertEqual((estimated.line.dash, estimated.line.color), ("dot", COLORS["forecast"]))
        self.assertEqual(list(observed.y), self.version["observed"]["value"].astype(float).tolist())
        self.assertEqual(list(estimated.y), self.version["estimates"]["value"].astype(float).tolist())
        self.assertEqual(pd.Timestamp(estimated.x[0]), pd.Timestamp("2026-07-01"))
        self.assertEqual(pd.Timestamp(estimated.x[-1]), pd.Timestamp("2026-12-01"))
        self.assertEqual(figure.layout.yaxis.title.text, "Visitantes por mes")
        self.assertIn("visitantes por mes", estimated.hovertemplate)

    def test_history_filter_only_trims_the_observed_line(self):
        for months, shown in [(12, 12), (24, 18), (0, 18), ("invalido", 18)]:
            with self.subTest(months=months):
                observed, estimated = predictions.build_figure(self.version, months).data
                self.assertEqual(len(observed.y), shown)
                self.assertEqual(len(estimated.y), 6)
        self.assertIn("12 meses registrados de julio de 2025 a junio de 2026", predictions.build_note(self.version, 12))

    def test_details_show_update_date_version_procedure_and_validation_metric(self):
        details = text(predictions.build_details(self.version))
        for expected in [
            "Actualizado el 1 de agosto de 2026, 12:00 UTC", "20260801T120000000000Z_e5f6a7b8", "Holt-Winters",
            "hw-1.0", "se alejó 2,0 % de lo registrado (error porcentual medio, MAPE)",
            "12 meses evaluados entre julio de 2025 y junio de 2026",
        ]:
            self.assertIn(expected, details)
        note = predictions.build_note(self.version, 24)
        self.assertIn("Guatemala", note)
        self.assertIn("6 meses estimados de julio de 2026 a diciembre de 2026", note)

    def test_validation_falls_back_to_mae_when_mape_is_missing(self):
        metrics = {**self.version["metrics"], "procedure": {"name": "holt_winters", "mae": 1234.6, "rmse": 1, "mape_pct": None}}
        self.assertIn("se alejó 1.235 visitantes por mes de lo registrado (error absoluto medio, MAE)",
                      predictions.validation_summary(metrics, "visitantes por mes"))

    def test_warning_explains_scope_and_months_without_coverage(self):
        warning = text(predictions.build_warning(self.version))
        self.assertIn("de julio de 2026 a diciembre de 2026", warning)
        self.assertIn("no tiene meses sin registro", warning)
        self.assertIn("MLflow", warning)
        observed = self.version["observed"].copy()
        observed = observed[observed["period"] != "2025-03"]
        observed.loc[observed["period"] == "2025-05", "value"] = None
        warning = text(predictions.build_warning({**self.version, "observed": observed}))
        self.assertIn("2 meses del historial no tienen registro (marzo de 2025, mayo de 2025)", warning)
        figure = predictions.build_figure({**self.version, "observed": observed}, 0)
        self.assertIsNone(figure.data[0].y[2])
        self.assertFalse(figure.data[0].connectgaps)

    def test_missing_version_shows_a_message_instead_of_an_empty_graph(self):
        figure, note, details, warning, content, unavailable = predictions.build_view(None, 24)
        self.assertFalse(figure.data)
        self.assertEqual(content, predictions.HIDDEN)
        self.assertEqual(unavailable, predictions.SHOWN)
        content, unavailable = predictions.build_view(self.version, 24)[4:]
        self.assertEqual((content, unavailable), (predictions.SHOWN, predictions.HIDDEN))


class PredictionCallbackTests(unittest.TestCase):
    def setUp(self):
        self.client = build_app().server.test_client()
        self.folder = Path(self.enterContext(TemporaryDirectory())) / "current"
        self.enterContext(patch.dict(os.environ, {APPROVED_DIR_VARIABLE: str(self.folder)}))
        model_results._cache.update(key=None, version=None)

    def update(self, months):
        response = self.client.post("/_dash-update-component", json=history_request(months))
        self.assertEqual(response.status_code, 200)
        return response.get_json()["response"]

    def test_filter_changes_do_not_reread_files_or_refit_the_model(self):
        shutil.copytree(SAMPLE_DIR / "current", self.folder)
        with patch.object(model_results.approved, "load_approved", wraps=approved.load_approved) as loader, \
                patch("pipeline.model.fit_and_forecast") as fit:
            lengths = [len(self.update(months)["predictions-graph"]["figure"]["data"][0]["y"]) for months in [12, 24, 0]]
        self.assertEqual(lengths, [12, 18, 18])
        self.assertEqual(loader.call_count, 1)
        fit.assert_not_called()

    def test_callback_reports_unavailable_version_without_errors(self):
        body = self.update(24)
        self.assertEqual(body["predictions-content"]["style"], predictions.HIDDEN)
        self.assertEqual(body["predictions-unavailable"]["style"], predictions.SHOWN)


if __name__ == "__main__":
    unittest.main()
