from __future__ import annotations

from bisect import bisect_left
from datetime import date, datetime
from typing import Any

from task_cli.store import TaskStore


class TaskError(Exception):
    pass


class DuplicateTaskError(TaskError):
    pass


class TaskNotFoundError(TaskError):
    pass


class InvalidTaskError(TaskError):
    pass


class TaskAlreadyDoneError(TaskError):
    pass


def _today_str(given: date | None = None) -> str:
    return (given or date.today()).isoformat()


def _now_str(given: datetime | None = None) -> str:
    return (given or datetime.now()).replace(microsecond=0).isoformat()


def _normalize_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise InvalidTaskError("任务名称不能为空。")
    return cleaned


def _sort_entries(entries: list[dict[str, Any]]) -> None:
    entries.sort(key=lambda entry: (entry["completed"], entry["id"]))


class TaskService:
    def __init__(self, store: TaskStore) -> None:
        self.store = store

    def _allocate_id(self, data: dict[str, Any]) -> int:
        free_ids = data["free_ids"]
        if free_ids:
            return free_ids.pop(0)
        task_id = data["next_id"]
        data["next_id"] += 1
        return task_id

    def _insert_free_id(self, data: dict[str, Any], task_id: int) -> None:
        free_ids = data["free_ids"]
        index = bisect_left(free_ids, task_id)
        if index >= len(free_ids) or free_ids[index] != task_id:
            free_ids.insert(index, task_id)

    def _ensure_unique_name(self, items: list[dict[str, Any]], name: str) -> None:
        if any(str(item.get("name", "")) == name for item in items):
            raise DuplicateTaskError("同一分类下已存在同名任务。")

    @staticmethod
    def _to_entry(item: dict[str, Any], completed: bool) -> dict[str, Any]:
        return {
            "id": int(item.get("id", 0)),
            "name": str(item.get("name", "")),
            "completed": completed,
        }

    def add_todo(self, name: str) -> dict[str, Any]:
        task_name = _normalize_name(name)
        data = self.store.load()
        todos = data["todos"]
        self._ensure_unique_name(todos, task_name)

        task_id = self._allocate_id(data)
        new_task = {
            "id": task_id,
            "name": task_name,
            "created_at": _now_str(),
            "done": False,
            "done_at": None,
        }
        todos.append(new_task)
        self.store.save(data)
        return new_task

    def add_daily(self, name: str) -> dict[str, Any]:
        task_name = _normalize_name(name)
        data = self.store.load()
        daily_tasks = data["daily_tasks"]
        self._ensure_unique_name(daily_tasks, task_name)

        task_id = self._allocate_id(data)
        new_task = {
            "id": task_id,
            "name": task_name,
            "created_at": _now_str(),
            "completion_dates": [],
        }
        daily_tasks.append(new_task)
        self.store.save(data)
        return new_task

    def list_tasks(self, include_completed: bool, today: date | None = None) -> dict[str, Any]:
        data = self.store.load()
        today_value = _today_str(today)

        daily_entries: list[dict[str, Any]] = []
        for item in data["daily_tasks"]:
            completion_dates = item.get("completion_dates")
            done_today = today_value in completion_dates if isinstance(completion_dates, list) else False
            entry = self._to_entry(item, done_today)
            if include_completed or not done_today:
                daily_entries.append(entry)

        todo_entries: list[dict[str, Any]] = []
        for item in data["todos"]:
            done = bool(item.get("done", False))
            entry = self._to_entry(item, done)
            if include_completed or not done:
                todo_entries.append(entry)

        _sort_entries(daily_entries)
        _sort_entries(todo_entries)
        return {"date": today_value, "daily": daily_entries, "todos": todo_entries}

    def list_daily(self, include_completed: bool, today: date | None = None) -> dict[str, Any]:
        listed = self.list_tasks(include_completed=include_completed, today=today)
        return {"date": listed["date"], "daily": listed["daily"]}

    def mark_done(self, task_id: int, today: date | None = None) -> dict[str, Any]:
        if task_id <= 0:
            raise InvalidTaskError("ID 必须是正整数。")
        data = self.store.load()
        today_value = _today_str(today)

        for index, item in enumerate(data["todos"]):
            if int(item.get("id", 0)) != task_id:
                continue
            removed = data["todos"].pop(index)
            self._insert_free_id(data, task_id)
            self.store.save(data)
            return {"kind": "todo", "id": task_id, "name": str(removed.get("name", ""))}

        for item in data["daily_tasks"]:
            if int(item.get("id", 0)) != task_id:
                continue
            completion_dates = item.get("completion_dates")
            if not isinstance(completion_dates, list):
                completion_dates = []
                item["completion_dates"] = completion_dates
            if today_value in completion_dates:
                raise TaskAlreadyDoneError("该每日任务今天已完成。")
            completion_dates.append(today_value)
            self.store.save(data)
            return {"kind": "daily", "id": task_id, "name": str(item.get("name", ""))}

        raise TaskNotFoundError("未找到该任务 ID。")

    def delete_task(self, task_id: int) -> dict[str, Any]:
        if task_id <= 0:
            raise InvalidTaskError("ID 必须是正整数。")
        data = self.store.load()

        for index, item in enumerate(data["todos"]):
            if int(item.get("id", 0)) != task_id:
                continue
            removed = data["todos"].pop(index)
            self._insert_free_id(data, task_id)
            self.store.save(data)
            return {"kind": "todo", "id": task_id, "name": str(removed.get("name", ""))}

        for index, item in enumerate(data["daily_tasks"]):
            if int(item.get("id", 0)) != task_id:
                continue
            removed = data["daily_tasks"].pop(index)
            self._insert_free_id(data, task_id)
            self.store.save(data)
            return {"kind": "daily", "id": task_id, "name": str(removed.get("name", ""))}

        raise TaskNotFoundError("未找到该任务 ID。")

    def today_summary(self, today: date | None = None, limit: int = 5) -> dict[str, Any]:
        listed = self.list_tasks(include_completed=False, today=today)
        pending_items: list[dict[str, Any]] = []
        for item in listed["daily"]:
            pending_items.append({"kind": "daily", "id": item["id"], "name": item["name"]})
        for item in listed["todos"]:
            pending_items.append({"kind": "todo", "id": item["id"], "name": item["name"]})
        pending_items.sort(key=lambda item: item["id"])
        return {
            "date": listed["date"],
            "pending_daily": len(listed["daily"]),
            "pending_todo": len(listed["todos"]),
            "pending_items": pending_items[:limit],
        }
