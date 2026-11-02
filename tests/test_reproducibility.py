import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from pipeline.config import ROOT, load_config
from pipeline.reproducibility import compare_runs
from pipeline.run import run_pipeline
from tests.synthetic_source import build_source, write_config


class ReproducibilityTests(unittest.TestCase):
    def test_two_full_runs_produce_the_same_estimates_and_metrics(self):
        config = load_config("config/pipeline.yaml")
        with TemporaryDirectory(dir=ROOT) as folder:
            config_path, raw_config = write_config(Path(folder), build_source(config))
            with patch("pipeline.run.publish"), patch("pipeline.run.log_run", return_value="mlflow-run"):
                first = run_pipeline(config_path)
                second = run_pipeline(config_path)
            result = compare_runs(first, second, config)
            self.assertTrue(result["reproducible"], result["differences"])
            self.assertLessEqual(result["max_relative_difference"], result["relative_tolerance"])
            estimates = second / raw_config["outputs"]["estimates_file"]
            changed = pd.read_csv(estimates)
            changed.loc[0, "value"] *= 1.01
            changed.to_csv(estimates, index=False)
            result = compare_runs(first, second, config)
        self.assertFalse(result["reproducible"])
        self.assertEqual(len(result["differences"]), 1)
        self.assertTrue(result["differences"][0].startswith("value 2026-07"))


if __name__ == "__main__":
    unittest.main()
