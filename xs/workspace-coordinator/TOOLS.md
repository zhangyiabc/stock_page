# 工具使用指南

## sessions_spawn

你的主要工具。用于调度其他 Agent 执行任务。

调度规范：
- 每次 spawn 必须在 task 中包含足够的上下文信息
- 需要并行的任务可以同时 spawn 多个 Agent
- 关注子任务返回的结果，综合后向用户汇报

## read / write

- 读写 `novel/` 目录下的章节正文文件
- 读写 `memory/plot/progress.md` 进度文件
- 格式：`novel/vol{N}/chapter-{NNN}.md`

## memory_search

当需要快速查找设定、角色或历史信息时使用。优先通过 memory-keeper Agent 查询完整上下文。

## lobster

使用 Lobster 执行标准化的写作流水线。参见 `skills/novel-write/SKILL.md`。
