# task

一个纯命令行的任务管理工具，支持两类任务：

- 每日任务：每天都会出现，完成状态按当天计算。
- 待办任务：一次性任务，完成后保持已完成。

## 环境要求

- Python 3.10+

## 安装（推荐）

在项目根目录执行：

```bash
uv tool install --from . task-cli
```

验证安装：

```bash
task -h
```

如果提示找不到 `task`，请将 `~/.local/bin` 加入 `PATH`：

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## 备选安装（虚拟环境）

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
task -h
```

说明：在 Arch Linux 等启用 PEP 668 的系统中，`python3 -m pip install --user ...` 可能被禁止，优先使用上面的 `uv tool` 或虚拟环境方案。

## 快速开始

```bash
task
task add 买牛奶
task daily add 晨跑
task list
task done 1
task delete 1
task list --all
task daily --all
```

## 命令说明

```bash
task                     # 显示帮助 + 今日摘要
task list [--all]        # 查看每日任务 + 待办列表
task daily [--all]       # 仅查看每日任务
task daily add <任务名>   # 添加每日任务
task add <任务名>         # 添加待办任务
task done <id>           # 完成任务
task delete <id>         # 删除任务（硬删除）
```

## 关键行为

- 同一分类下不允许重名任务。
- `task done <id>` 对每日任务只标记“今天已完成”，明天会自动恢复未完成。
- `task delete <id>` 为永久删除，无回收站。
- 删除后会回收 ID。
- 新任务优先使用全局最小可用 ID（每日 + 待办共用 ID 池）。

## 数据文件

- 默认路径：`~/.task/tasks.json`
- 当前数据版本：`version = 2`
- 包含字段：`next_id`、`free_ids`、`todos`、`daily_tasks`

示例：

```json
{
  "version": 2,
  "next_id": 8,
  "free_ids": [2, 5],
  "todos": [],
  "daily_tasks": []
}
```

## 测试

```bash
python3 -m unittest discover -s tests -v
```
