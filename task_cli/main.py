from __future__ import annotations

import argparse
import sys

from task_cli.render import render_daily, render_list, render_root
from task_cli.service import (
    DuplicateTaskError,
    InvalidTaskError,
    TaskAlreadyDoneError,
    TaskError,
    TaskNotFoundError,
    TaskService,
)
from task_cli.store import TaskStore


def _parse_positive_id(raw: str) -> int:
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise InvalidTaskError("ID 必须是正整数。") from exc
    if parsed <= 0:
        raise InvalidTaskError("ID 必须是正整数。")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task",
        description="记录每日任务和待办列表的命令行工具",
    )
    subparsers = parser.add_subparsers(dest="command")

    parser_list = subparsers.add_parser("list", help="查看所有任务（每日 + 待办）")
    parser_list.add_argument("--all", action="store_true", dest="show_all", help="显示已完成任务")

    parser_daily = subparsers.add_parser("daily", help="查看或管理每日任务")
    parser_daily.add_argument("--all", action="store_true", dest="show_all", help="显示已完成每日任务")
    daily_subparsers = parser_daily.add_subparsers(dest="daily_command")
    parser_daily_add = daily_subparsers.add_parser("add", help="添加每日任务")
    parser_daily_add.add_argument("name", nargs="+", help="任务名称")

    parser_add = subparsers.add_parser("add", help="添加待办任务")
    parser_add.add_argument("name", nargs="+", help="任务名称")

    parser_done = subparsers.add_parser("done", help="完成任务")
    parser_done.add_argument("id", help="任务 ID")

    parser_delete = subparsers.add_parser("delete", help="删除任务")
    parser_delete.add_argument("id", help="任务 ID")

    return parser


def _run(args: argparse.Namespace, parser: argparse.ArgumentParser, service: TaskService) -> int:
    command = args.command
    if command is None:
        print(render_root(parser.format_help(), service.today_summary()))
        return 0

    if command == "list":
        print(render_list(service.list_tasks(include_completed=args.show_all)))
        return 0

    if command == "daily":
        if args.daily_command == "add":
            task_name = " ".join(args.name)
            created = service.add_daily(task_name)
            print(f"已添加每日任务 #{created['id']}：{created['name']}")
            return 0
        print(render_daily(service.list_daily(include_completed=args.show_all)))
        return 0

    if command == "add":
        task_name = " ".join(args.name)
        created = service.add_todo(task_name)
        print(f"已添加待办任务 #{created['id']}：{created['name']}")
        return 0

    if command == "done":
        task_id = _parse_positive_id(args.id)
        result = service.mark_done(task_id)
        if result["kind"] == "daily":
            print(f"已完成今日每日任务 #{result['id']}：{result['name']}")
        else:
            print(f"已完成待办任务 #{result['id']}：{result['name']}")
        return 0

    if command == "delete":
        task_id = _parse_positive_id(args.id)
        result = service.delete_task(task_id)
        if result["kind"] == "daily":
            print(f"已删除每日任务 #{result['id']}：{result['name']}")
        else:
            print(f"已删除待办任务 #{result['id']}：{result['name']}")
        return 0

    raise InvalidTaskError("未知命令。")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = TaskService(TaskStore())
    try:
        return _run(args, parser, service)
    except (DuplicateTaskError, TaskNotFoundError, InvalidTaskError, TaskAlreadyDoneError, TaskError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

