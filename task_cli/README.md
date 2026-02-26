# task_cli 开发说明

`task_cli` 是 `task` 命令的实现包，负责参数解析、业务逻辑、存储和输出。

## 代码结构

- `main.py`：CLI 入口，argparse 命令树，异常转中文错误输出。
- `service.py`：核心业务逻辑（add/list/done/delete/summary）。
- `store.py`：JSON 持久化、状态规范化、版本迁移、原子写入。
- `render.py`：列表与摘要的终端渲染。

## 数据模型

默认文件：`~/.task/tasks.json`

```json
{
  "version": 2,
  "next_id": 1,
  "free_ids": [],
  "todos": [],
  "daily_tasks": []
}
```

字段含义：

- `next_id`：高水位 ID（当 `free_ids` 为空时分配并自增）。
- `free_ids`：可复用 ID 池（升序、唯一、正整数）。
- `todos`：待办任务数组。
- `daily_tasks`：每日任务数组（含 `completion_dates`）。

## ID 分配与回收规则

1. 新增任务且 `free_ids` 非空：取最小值。
2. 新增任务且 `free_ids` 为空：取 `next_id` 并 `next_id += 1`。
3. 删除任务：从对应列表移除任务，并将该 ID 插回 `free_ids`（有序去重）。

## 迁移策略（兼容旧数据）

- 读取时统一调用 `normalize_state`。
- 若旧文件没有 `free_ids`，会根据 `used_ids` 与 `next_id` 自动重建。
- 旧 `version` 会在保存时写回 `version: 2`。

## 行为约定

- 每日任务完成状态按“当天日期”判断。
- `done` 对每日任务仅影响今天。
- `done` 对待办任务为“完成即删除”，不持久化待办完成状态。
- 同分类重名任务会抛出错误。
- 错误统一返回码 `1`，并打印中文错误信息。

## 本地开发

推荐（使用 uv）：

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

备选（标准 venv）：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

## 卸载（开发环境）

```bash
source .venv/bin/activate
python3 -m pip uninstall task-cli
deactivate
```

如需清理本地虚拟环境目录，可额外执行：

```bash
rm -rf .venv
```

运行测试：

```bash
python3 -m unittest discover -s tests -v
```
