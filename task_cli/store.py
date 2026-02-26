from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULT_VERSION = 2


def default_data_path() -> Path:
    return Path.home() / ".task" / "tasks.json"


def default_state() -> dict[str, Any]:
    return {
        "version": DEFAULT_VERSION,
        "next_id": 1,
        "free_ids": [],
        "todos": [],
        "daily_tasks": [],
    }


def _coerce_positive_int(value: Any) -> int | None:
    try:
        converted = int(value)
    except (TypeError, ValueError):
        return None
    if converted <= 0:
        return None
    return converted


def _extract_used_ids(data: dict[str, Any]) -> set[int]:
    used_ids: set[int] = set()
    for key in ("todos", "daily_tasks"):
        items = data.get(key)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            task_id = _coerce_positive_int(item.get("id"))
            if task_id is not None:
                used_ids.add(task_id)
    return used_ids


def normalize_state(raw: dict[str, Any]) -> dict[str, Any]:
    state = default_state()

    todos = raw.get("todos")
    daily_tasks = raw.get("daily_tasks")
    state["todos"] = todos if isinstance(todos, list) else []
    state["daily_tasks"] = daily_tasks if isinstance(daily_tasks, list) else []

    used_ids = _extract_used_ids(state)
    max_used = max(used_ids, default=0)

    next_id = _coerce_positive_int(raw.get("next_id"))
    if next_id is None:
        next_id = max_used + 1 if max_used else 1
    if next_id <= max_used:
        next_id = max_used + 1

    # Keep free_ids decision-complete and deterministic from used IDs + next_id.
    free_ids = sorted(set(range(1, next_id)) - used_ids)

    state["version"] = DEFAULT_VERSION
    state["next_id"] = next_id
    state["free_ids"] = free_ids
    return state


class TaskStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_data_path()

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return default_state()

        with self.path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
        if not isinstance(raw_data, dict):
            return default_state()
        return normalize_state(raw_data)

    def save(self, data: dict[str, Any]) -> None:
        normalized = normalize_state(data)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(normalized, file, indent=2, ensure_ascii=False)
            file.write("\n")
        os.replace(temp_path, self.path)

