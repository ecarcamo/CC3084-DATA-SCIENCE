import json
import shutil
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.approved import load_approved
from pipeline import publish as publication
from pipeline.config import load_config
from pipeline.publish import latest_approved, publish, restore
from tests.test_approved_contract import SAMPLE_DIR, assert_approved_version

OLD_ID = "20260701T120000000000Z_a1b2c3d4"
NEW_ID = "20260801T120000000000Z_e5f6a7b8"


def run_id(folder):
    return json.loads((folder / "run.json").read_text(encoding="utf-8"))["run_id"]


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(self.enterContext(TemporaryDirectory()))
        self.config = load_config("config/pipeline.yaml")
        self.approved = self.folder / "approved" / "current"
        self.history = self.folder / "approved" / "history"
        self.config["outputs"]["approved_dir"] = self.approved
        self.config["outputs"]["history_dir"] = self.history
        self.candidate = self.folder / "candidates" / NEW_ID
        shutil.copytree(SAMPLE_DIR / "current", self.candidate)

    def install_old_version(self):
        shutil.copytree(SAMPLE_DIR / "history" / OLD_ID, self.approved)

    def assert_no_leftovers(self):
        self.assertEqual([path.name for path in self.approved.parent.iterdir() if path.name.startswith(".")], [])

    def test_first_publication_installs_candidate_without_history(self):
        self.assertIsNone(latest_approved(self.config))
        self.assertEqual(publish(self.candidate, self.config), NEW_ID)
        self.assertEqual(latest_approved(self.config), self.approved)
        assert_approved_version(self, self.approved, self.config)
        self.assertFalse(self.history.exists())
        self.assert_no_leftovers()

    def test_publication_archives_current_version_under_its_own_run_id(self):
        self.install_old_version()
        self.assertEqual(publish(self.candidate, self.config), NEW_ID)
        self.assertEqual(run_id(self.approved), NEW_ID)
        self.assertEqual([path.name for path in self.history.iterdir()], [OLD_ID])
        assert_approved_version(self, self.history / OLD_ID, self.config)
        assert_approved_version(self, self.approved, self.config)
        self.assertTrue(self.candidate.is_dir())
        self.assert_no_leftovers()

    def test_incomplete_candidate_is_rejected_before_touching_the_current_version(self):
        self.install_old_version()
        (self.candidate / "metrics.json").unlink()
        with self.assertRaisesRegex(FileNotFoundError, "metrics.json"):
            publish(self.candidate, self.config)
        self.assertEqual(run_id(self.approved), OLD_ID)
        self.assertFalse(self.history.exists())

    def test_failed_copy_keeps_the_previous_version_complete(self):
        self.install_old_version()
        original = shutil.copy2

        def failing_copy(source, target):
            if Path(source).name == "run.json":
                raise OSError("Disco lleno.")
            return original(source, target)

        with patch.object(publication.shutil, "copy2", side_effect=failing_copy), self.assertRaises(OSError):
            publish(self.candidate, self.config)
        assert_approved_version(self, self.approved, self.config)
        self.assertEqual(run_id(self.approved), OLD_ID)
        self.assert_no_leftovers()

    def test_failed_swap_restores_the_previous_version(self):
        self.install_old_version()
        original = Path.rename

        def failing_rename(path, target):
            if Path(target) == self.approved and path.name.endswith(".tmp"):
                raise PermissionError("Archivo en uso.")
            return original(path, target)

        with patch.object(Path, "rename", failing_rename), self.assertRaises(PermissionError):
            publish(self.candidate, self.config)
        assert_approved_version(self, self.approved, self.config)
        self.assertEqual(run_id(self.approved), OLD_ID)
        self.assert_no_leftovers()

    def test_incomplete_current_version_is_not_overwritten(self):
        self.install_old_version()
        (self.approved / "observed.csv").unlink()
        with self.assertRaisesRegex(ValueError, "incompleta"):
            publish(self.candidate, self.config)
        self.assertTrue((self.approved / "run.json").is_file())

    def test_restore_moves_current_to_history_and_the_dashboard_reads_the_restored_version(self):
        self.install_old_version()
        publish(self.candidate, self.config)
        self.assertEqual(load_approved(self.approved)["run"]["run_id"], NEW_ID)
        self.assertEqual(restore(OLD_ID, self.config), OLD_ID)
        assert_approved_version(self, self.approved, self.config)
        self.assertEqual(load_approved(self.approved)["run"]["run_id"], OLD_ID)
        self.assertEqual(sorted(path.name for path in self.history.iterdir()), [OLD_ID, NEW_ID])
        assert_approved_version(self, self.history / NEW_ID, self.config)
        self.assertEqual(restore(NEW_ID, self.config), NEW_ID)
        self.assertEqual(run_id(self.approved), NEW_ID)
        self.assert_no_leftovers()

    def test_restore_rejects_unknown_versions_and_paths_outside_history(self):
        self.install_old_version()
        publish(self.candidate, self.config)
        for version_id in ["no-existe", "..", "../current", "", OLD_ID + "/.."]:
            with self.subTest(version_id=version_id), self.assertRaises(ValueError):
                restore(version_id, self.config)
        self.assertEqual(run_id(self.approved), NEW_ID)

    def test_restore_command_reports_the_installed_version(self):
        self.install_old_version()
        publish(self.candidate, self.config)
        output, errors = StringIO(), StringIO()
        with patch.object(publication, "load_config", return_value=self.config), \
                redirect_stdout(output), redirect_stderr(errors):
            self.assertEqual(publication.main(["--restore", OLD_ID]), 0)
            self.assertEqual(publication.main(["--restore", "no-existe"]), 1)
        self.assertIn(f"Versión restaurada: {OLD_ID}.", output.getvalue())
        self.assertIn("No existe la versión no-existe", errors.getvalue())
        self.assertEqual(run_id(self.approved), OLD_ID)


if __name__ == "__main__":
    unittest.main()
