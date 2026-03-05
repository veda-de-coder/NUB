import os
import shutil
import tempfile
import unittest
from pathlib import Path
from nub.init import init_repo, vcs_dir, objects_dir
from nub.config import set_identity
from nub.tree import snapshot
from nub.commit import create_commit
from nub.refs import write_ref, create_branch, branch_exists, list_branches
from nub.rollback import rollback_by_steps

class TestNUB(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.repo_dir = self.test_dir / "repo"
        self.repo_dir.mkdir()
        init_repo(self.repo_dir)
        self.vd = vcs_dir(self.repo_dir)
        self.od = objects_dir(self.repo_dir)
        set_identity(self.vd, "Tester", "tester@example.com")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_init_repo(self):
        self.assertTrue((self.repo_dir / ".vcs").is_dir())

    def test_snap_and_rollback(self):
        # Snap 1
        (self.repo_dir / "file1.txt").write_text("v1")
        th1 = snapshot(self.repo_dir, self.od)
        ch1 = create_commit(self.od, th1, "T", "t@e.com", "K", "m1", "main")
        write_ref(self.vd, "main", ch1)

        # Snap 2
        (self.repo_dir / "file2.txt").write_text("v2")
        th2 = snapshot(self.repo_dir, self.od)
        ch2 = create_commit(self.od, th2, "T", "t@e.com", "K", "m2", "main", ch1)
        write_ref(self.vd, "main", ch2)

        self.assertTrue((self.repo_dir / "file2.txt").exists())

        # Rollback
        rollback_by_steps(self.repo_dir, self.vd, self.od, 1)

        self.assertTrue((self.repo_dir / "file1.txt").exists())
        self.assertFalse((self.repo_dir / "file2.txt").exists())

    def test_untracked_files_preserved(self):
        # Snap 1
        (self.repo_dir / "tracked.txt").write_text("tracked")
        th1 = snapshot(self.repo_dir, self.od)
        ch1 = create_commit(self.od, th1, "T", "t@e.com", "K", "m1", "main")
        write_ref(self.vd, "main", ch1)

        # Snap 2
        (self.repo_dir / "tracked2.txt").write_text("tracked2")
        th2 = snapshot(self.repo_dir, self.od)
        ch2 = create_commit(self.od, th2, "T", "t@e.com", "K", "m2", "main", ch1)
        write_ref(self.vd, "main", ch2)

        # Create TRULY untracked file (created after the latest snap)
        untracked = self.repo_dir / "untracked.txt"
        untracked.write_text("survive")

        # Rollback
        rollback_by_steps(self.repo_dir, self.vd, self.od, 1)

        self.assertTrue(untracked.exists())
        self.assertEqual(untracked.read_text(), "survive")
        self.assertTrue((self.repo_dir / "tracked.txt").exists())
        self.assertFalse((self.repo_dir / "tracked2.txt").exists())

    def test_flow_management(self):
        create_branch(self.vd, "feature")
        self.assertTrue(branch_exists(self.vd, "feature"))
        self.assertIn("feature", list_branches(self.vd))

if __name__ == "__main__":
    unittest.main()
