import tempfile
import unittest
from pathlib import Path

from biomed_ref_pipeline.workspace import WORKSPACE_DIRS, init_workspace


class WorkspaceTests(unittest.TestCase):
    def test_init_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            created = init_workspace(Path(tmp) / "project", project_name="Test Project")
            self.assertEqual(len(created), len(WORKSPACE_DIRS))
            self.assertTrue((Path(tmp) / "project" / "README.md").exists())
            self.assertTrue((Path(tmp) / "project" / "biomed_ref_pipeline.toml").exists())
            self.assertTrue((Path(tmp) / "project" / "06_citation_plan").is_dir())


if __name__ == "__main__":
    unittest.main()
