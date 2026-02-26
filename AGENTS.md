# Repository Guidelines

## Project Structure & Module Organization
This repository is a small Python CLI package for task management.

- `task_cli/`: application code.
- `task_cli/main.py`: CLI entrypoint and `argparse` command tree.
- `task_cli/service.py`: core task logic, validation, and domain errors.
- `task_cli/store.py`: JSON persistence, schema normalization, and migration to `version = 2`.
- `task_cli/render.py`: terminal output formatting.
- `tests/`: `unittest` suites (`test_cli.py`, `test_service.py`).
- `build/` and `task_cli.egg-info/`: generated artifacts; do not edit manually.

## Build, Test, and Development Commands
- `uv tool install --from . task-cli`: install the CLI tool from this repo.
- `python3 -m venv .venv && source .venv/bin/activate`: create and activate a local environment.
- `python3 -m pip install -e .`: install editable package for development.
- `task -h`: verify CLI entrypoint and command help.
- `python3 -m unittest discover -s tests -v`: run full test suite.

## Coding Style & Naming Conventions
- Target Python `>=3.10`; use 4-space indentation and UTF-8 files.
- Keep module/function names `snake_case`; classes/exceptions `PascalCase`.
- Preserve type hints and `from __future__ import annotations` style used across modules.
- Keep CLI-facing messages in Chinese to match existing user output.
- Do not rename persisted JSON keys (`version`, `next_id`, `free_ids`, `todos`, `daily_tasks`) without migration coverage.

## Testing Guidelines
- Use `unittest` for all new tests.
- Name tests `test_<behavior>` and keep one behavior per test method.
- For filesystem/state tests, use `tempfile.TemporaryDirectory()` and isolated paths.
- For CLI tests, run via `python -m task_cli.main` and assert both return code and output (`stdout`/`stderr`).
- Any behavior change in ID allocation, deletion, or migration should include regression tests.

## Runtime Behavior Requirements
- After a task is completed successfully. Must trigger a desktop notification via `notify-send`.

## Commit & Pull Request Guidelines
- Follow the existing commit pattern: `<type>: <short summary>` (examples in history: `feat:`, `docs:`, `chore:`).
- Keep commits focused and atomic; avoid mixing refactors with behavior changes.
- PRs should include what changed and why.
- PRs should include how to test (exact command plus result).
- PRs should call out schema/storage impact when touching `store.py` or task data format.
