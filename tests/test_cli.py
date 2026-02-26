from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def _extract_id(output: str) -> int:
    match = re.search(r"#(\d+)", output)
    if not match:
        raise AssertionError(f"未在输出中找到任务 ID: {output!r}")
    return int(match.group(1))


class TaskCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.home = self.temp_dir.name
        self.repo_root = Path(__file__).resolve().parents[1]

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = self.home
        return subprocess.run(
            [sys.executable, "-m", "task_cli.main", *args],
            cwd=self.repo_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_delete_then_add_reuses_same_id(self) -> None:
        first = self.run_cli("add", "A")
        second = self.run_cli("add", "B")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)

        id_one = _extract_id(first.stdout)
        id_two = _extract_id(second.stdout)
        self.assertEqual((id_one, id_two), (1, 2))

        deleted = self.run_cli("delete", "1")
        self.assertEqual(deleted.returncode, 0, deleted.stderr)

        reused = self.run_cli("add", "C")
        self.assertEqual(reused.returncode, 0, reused.stderr)
        self.assertEqual(_extract_id(reused.stdout), 1)

    def test_delete_missing_id_returns_error(self) -> None:
        result = self.run_cli("delete", "123")
        self.assertEqual(result.returncode, 1)
        self.assertIn("未找到该任务 ID", result.stderr)

    def test_root_output_includes_daily_add_hint(self) -> None:
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("task daily add <任务名>", result.stdout)


if __name__ == "__main__":
    unittest.main()
