import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from pipeline.checks import (
    OK,
    STOP,
    WARNING,
    check_columns_and_types,
    check_dates_and_coverage,
    check_uniqueness,
    has_stop,
    run_checks,
    write_quality_report,
)
from pipeline.config import load_config
from tests.synthetic_source import build_source


class ChecksTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config("config/pipeline.yaml")
        self.source = build_source(self.config)

    def without_month(self, year, month):
        return self.source.loc[~(self.source["Año"].eq(year) & self.source["Mes cod"].eq(month))]

    def test_healthy_source_passes_every_check(self):
        results = run_checks(self.source, self.config)
        self.assertEqual(
            [result.name for result in results],
            ["check_columns_and_types", "check_dates_and_coverage", "check_uniqueness"],
        )
        self.assertEqual({result.status for result in results}, {OK})
        self.assertFalse(has_stop(results))

    def test_missing_required_column_stops(self):
        result = check_columns_and_types(self.source.drop(columns="Frontera"), self.config)
        self.assertEqual(result.status, STOP)
        self.assertEqual(result.details["missing_required"], ["Frontera"])

    def test_value_column_as_text_stops(self):
        self.source["Viajero"] = self.source["Viajero"].astype(str)
        result = check_columns_and_types(self.source, self.config)
        self.assertEqual(result.status, STOP)
        self.assertIn("Viajero", result.details["incompatible_types"])

    def test_missing_optional_column_warns(self):
        result = check_columns_and_types(self.source.drop(columns="MCEO"), self.config)
        self.assertEqual(result.status, WARNING)
        self.assertEqual(result.details["missing_optional"], ["MCEO"])

    def test_month_thirteen_stops(self):
        self.source.loc[0, "Mes cod"] = 13
        result = check_dates_and_coverage(self.source, self.config)
        self.assertEqual(result.status, STOP)
        self.assertEqual(result.details["invalid_rows"], 1)

    def test_missing_month_in_fit_period_stops(self):
        result = check_dates_and_coverage(self.without_month(2024, 5), self.config)
        self.assertEqual(result.status, STOP)
        self.assertEqual(result.details["missing_in_fit"], ["2024-05"])

    def test_month_with_only_excluded_types_counts_as_missing(self):
        mask = self.source["Año"].eq(2024) & self.source["Mes cod"].eq(3)
        self.source.loc[mask, "Tipo de Viajero"] = "Viajero"
        result = check_dates_and_coverage(self.source, self.config)
        self.assertEqual(result.status, STOP)
        self.assertEqual(result.details["missing_in_fit"], ["2024-03"])

    def test_source_ending_before_expected_period_stops(self):
        result = check_dates_and_coverage(self.without_month(2026, 6), self.config)
        self.assertEqual(result.status, STOP)
        self.assertEqual(result.details["last_period"], "2026-05")

    def test_missing_month_before_fit_period_only_warns(self):
        results = run_checks(self.without_month(2015, 4), self.config)
        coverage = results[1]
        self.assertEqual(coverage.status, WARNING)
        self.assertEqual(coverage.details["missing_before_fit"], ["2015-04"])
        self.assertFalse(has_stop(results))

    def test_duplicated_key_stops_with_count_and_examples(self):
        duplicated = pd.concat([self.source, self.source.iloc[[0]]], ignore_index=True)
        result = check_uniqueness(duplicated, self.config)
        self.assertEqual(result.status, STOP)
        self.assertEqual(result.details["duplicated_keys"], 1)
        self.assertEqual(result.details["examples"][0]["Año"], 2009)

    def test_examples_are_limited_to_five(self):
        duplicated = pd.concat([self.source, self.source.iloc[:8]], ignore_index=True)
        result = check_uniqueness(duplicated, self.config)
        self.assertEqual(result.details["duplicated_keys"], 8)
        self.assertEqual(len(result.details["examples"]), 5)

    def test_run_checks_halts_after_first_stop(self):
        results = run_checks(self.source.drop(columns="Año"), self.config)
        self.assertEqual(len(results), 1)
        self.assertTrue(has_stop(results))

    def test_quality_report_contains_run_and_every_check(self):
        results = run_checks(self.without_month(2015, 4), self.config)
        with TemporaryDirectory() as folder:
            path = Path(folder) / self.config["outputs"]["quality_report_file"]
            write_quality_report(results, path, "run-prueba")
            report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(report["run_id"], "run-prueba")
        self.assertTrue(report["generated_at"])
        self.assertEqual(report["status"], WARNING)
        self.assertEqual([check["status"] for check in report["checks"]], [OK, WARNING, OK])
        self.assertEqual(set(report["checks"][0]), {"name", "status", "message", "details"})


if __name__ == "__main__":
    unittest.main()
