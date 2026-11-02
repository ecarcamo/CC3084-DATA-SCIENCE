import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.approved import APPROVED_DIR_VARIABLE, approved_dir, load_approved
from pipeline.config import ROOT, load_config

SAMPLE_DIR = ROOT / "tests" / "fixtures" / "approved_sample" / "current"


class ApprovedVersionTests(unittest.TestCase):
    def test_sample_version_is_loaded(self):
        approved = load_approved(SAMPLE_DIR)
        self.assertEqual(set(approved), {"estimates", "observed", "metrics", "quality_report", "run"})
        self.assertEqual(set(approved["estimates"]["kind"]), {"estimado"})
        self.assertEqual(set(approved["observed"]["kind"]), {"observado"})
        self.assertEqual(set(approved["estimates"]["run_id"]), {approved["run"]["run_id"]})
        self.assertIn("mae", approved["metrics"]["procedure"])

    def test_missing_version_returns_none(self):
        with TemporaryDirectory() as folder:
            self.assertIsNone(load_approved(Path(folder) / "current"))
            self.assertIsNone(load_approved(folder))

    def test_environment_variable_overrides_configured_folder(self):
        with patch.dict(os.environ, {APPROVED_DIR_VARIABLE: str(SAMPLE_DIR)}):
            self.assertEqual(approved_dir(), SAMPLE_DIR)
            self.assertIsNotNone(load_approved())
        with patch.dict(os.environ, {APPROVED_DIR_VARIABLE: ""}):
            self.assertEqual(approved_dir(), load_config("config/pipeline.yaml")["outputs"]["approved_dir"])


if __name__ == "__main__":
    unittest.main()
