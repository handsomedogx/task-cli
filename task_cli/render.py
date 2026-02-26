from __future__ import annotations

from typing import Any


def _status_mark(completed: bool) -> str:
    return "[x]" if completed else "[ ]"


def _render_entries(entries: list[dict[str, Any]]) -> list[str]:
    if not entries:
        return ["暂无任务。"]
    return [f"{_status_mark(item['completed'])} {item['id']} {item['name']}" for item in entries]


def render_list(data: dict[str, Any]) -> str:
    lines: list[str] = ["每日任务"]
    lines.extend(_render_entries(data["daily"]))
    lines.append("")
    lines.append("待办列表")
    lines.extend(_render_entries(data["todos"]))
    return "\n".join(lines)


def render_daily(data: dict[str, Any]) -> str:
    lines: list[str] = ["每日任务"]
    lines.extend(_render_entries(data["daily"]))
    return "\n".join(lines)


def render_root(help_text: str, summary: dict[str, Any]) -> str:
    lines = [help_text.rstrip(), "", f"今日摘要（{summary['date']}）"]
    lines.append(f"每日任务未完成: {summary['pending_daily']}")
    lines.append(f"待办任务未完成: {summary['pending_todo']}")
    lines.append("")
    lines.append("接下来可做:")
    if summary["pending_items"]:
        for item in summary["pending_items"]:
            task_type = "每日" if item["kind"] == "daily" else "待办"
            lines.append(f"- [{task_type}] {item['id']} {item['name']}")
    else:
        lines.append("- 当前没有未完成任务。")
    lines.append("")
    lines.append("常用命令:")
    lines.append("- 添加每日任务: task daily add <任务名>")
    lines.append("- 添加待办任务: task add <任务名>")
    lines.append("- 查看任务列表: task list")
    lines.append("- 完成任务: task done <id>")
    return "\n".join(lines)
