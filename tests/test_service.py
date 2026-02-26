from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from task_cli.service import TaskNotFoundError, TaskService
from task_cli.store import TaskStore


class TaskServiceIdRecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = Path(self.temp_dir.name) / "tasks.json"
        self.store = TaskStore(self.db_path)
        self.service = TaskService(self.store)

    def test_delete_then_add_reuses_deleted_id(self) -> None:
        first = self.service.add_todo("A")
        second = self.service.add_todo("B")
        self.assertEqual(first["id"], 1)
        self.assertEqual(second["id"], 2)

        self.service.delete_task(1)
        third = self.service.add_todo("C")
        self.assertEqual(third["id"], 1)

    def test_multiple_gaps_always_reuse_smallest_id(self) -> None:
        created = [self.service.add_todo(f"T{i}") for i in range(1, 6)]
        self.assertEqual([item["id"] for item in created], [1, 2, 3, 4, 5])

        self.service.delete_task(4)
        self.service.delete_task(2)

        next_one = self.service.add_todo("Next-1")
        next_two = self.service.add_todo("Next-2")
        self.assertEqual(next_one["id"], 2)
        self.assertEqual(next_two["id"], 4)

    def test_cross_category_id_reuse(self) -> None:
        todo = self.service.add_todo("待办")
        self.assertEqual(todo["id"], 1)

        daily = self.service.add_daily("每日")
        self.assertEqual(daily["id"], 2)

        self.service.delete_task(1)
        reused = self.service.add_daily("每日2")
        self.assertEqual(reused["id"], 1)

    def test_delete_nonexistent_id_keeps_free_ids_unchanged(self) -> None:
        self.service.add_todo("A")
        before = self.store.load()["free_ids"]

        with self.assertRaises(TaskNotFoundError):
            self.service.delete_task(999)

        after = self.store.load()["free_ids"]
        self.assertEqual(before, after)

    def test_migration_rebuilds_free_ids_when_missing(self) -> None:
        legacy = {
            "version": 1,
            "next_id": 6,
            "todos": [
                {
                    "id": 1,
                    "name": "A",
                    "created_at": "2026-02-26T10:00:00",
                    "done": False,
                    "done_at": None,
                },
                {
                    "id": 4,
                    "name": "B",
                    "created_at": "2026-02-26T11:00:00",
                    "done": False,
                    "done_at": None,
                },
            ],
            "daily_tasks": [
                {
                    "id": 2,
                    "name": "D",
                    "created_at": "2026-02-26T12:00:00",
                    "completion_dates": [],
                }
            ],
        }
        self.db_path.write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")

        loaded = self.store.load()
        self.assertEqual(loaded["version"], 2)
        self.assertEqual(loaded["next_id"], 6)
        self.assertEqual(loaded["free_ids"], [3, 5])

        self.store.save(loaded)
        persisted = json.loads(self.db_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["version"], 2)
        self.assertEqual(persisted["free_ids"], [3, 5])

    def test_repeated_delete_and_add_remains_predictable(self) -> None:
        a = self.service.add_todo("A")
        b = self.service.add_todo("B")
        c = self.service.add_daily("C")
        self.assertEqual([a["id"], b["id"], c["id"]], [1, 2, 3])

        self.service.delete_task(2)
        reused_b = self.service.add_daily("B2")
        self.assertEqual(reused_b["id"], 2)

        self.service.delete_task(1)
        reused_a = self.service.add_todo("A2")
        self.assertEqual(reused_a["id"], 1)

        data = self.store.load()
        used_ids = sorted(
            int(item["id"])
            for bucket in ("todos", "daily_tasks")
            for item in data[bucket]
        )
        self.assertEqual(used_ids, [1, 2, 3])
        self.assertEqual(data["free_ids"], [])

    def test_done_todo_removes_task_and_recycles_id(self) -> None:
        todo = self.service.add_todo("一次性任务")
        self.assertEqual(todo["id"], 1)

        result = self.service.mark_done(1)
        self.assertEqual(result["kind"], "todo")
        self.assertEqual(result["id"], 1)

        data = self.store.load()
        self.assertEqual(data["todos"], [])
        self.assertEqual(data["free_ids"], [1])

        reused = self.service.add_todo("新任务")
        self.assertEqual(reused["id"], 1)


if __name__ == "__main__":
    unittest.main()
