import os
import shutil
import tempfile
import subprocess
import unittest
from pathlib import Path

class TestNUBIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.repo_dir = self.test_dir / "repo"
        self.repo_dir.mkdir()
        # Path to nub.cmd
        self.nub_cmd = Path(__file__).parent / "nub.cmd"
        self.env = os.environ.copy()
        # Make sure NUB is in PYTHONPATH
        self.env["PYTHONPATH"] = str(Path(__file__).parent)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def run_nub(self, *args, cwd=None):
        if cwd is None:
            cwd = self.repo_dir
        result = subprocess.run(
            ["python", str(Path(__file__).parent / "nub" / "cli.py"), *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            env=self.env
        )
        if result.returncode != 0:
            print(f"DEBUG: nub {' '.join(args)} failed with return code {result.returncode}")
            print(f"DEBUG: STDOUT: {result.stdout}")
            print(f"DEBUG: STDERR: {result.stderr}")
        return result

    def test_full_workflow(self):
        # 1. Start
        res = self.run_nub("start")
        self.assertEqual(res.returncode, 0)
        self.assertIn("Initialised empty NUB repository", res.stdout)

        # 2. Auth
        res = self.run_nub("auth", "--name", "Integration User", "--email", "int@example.com")
        self.assertEqual(res.returncode, 0)
        self.assertIn("Identity Locked", res.stdout)

        # 3. Snap
        (self.repo_dir / "test.txt").write_text("v1")
        res = self.run_nub("snap", "-m", "Initial Snap")
        self.assertEqual(res.returncode, 0)
        self.assertIn("Snapped", res.stdout)

        # 4. Past
        res = self.run_nub("past")
        self.assertEqual(res.returncode, 0)
        self.assertIn("Initial Snap", res.stdout)

        # 5. Now
        res = self.run_nub("now")
        self.assertEqual(res.returncode, 0)
        self.assertIn("Flow   : main", res.stdout)

        # 6. Flow create/switch
        res = self.run_nub("flow", "create", "dev")
        self.assertEqual(res.returncode, 0)
        res = self.run_nub("flow", "switch", "dev")
        self.assertEqual(res.returncode, 0)
        self.assertIn("Switched to flow 'dev'", res.stdout)

        # 7. Map
        res = self.run_nub("map")
        self.assertEqual(res.returncode, 0)
        self.assertIn("test.txt", res.stdout)

if __name__ == "__main__":
    unittest.main()
