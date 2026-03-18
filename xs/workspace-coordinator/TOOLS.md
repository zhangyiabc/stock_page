# 工具使用指南

## sessions_spawn

你的主要工具。用于调度其他 Agent 执行任务。

调度规范：
- 每次 spawn 必须在 task 中包含足够的上下文信息
- 需要并行的任务可以同时 spawn 多个 Agent（如 Step 1 的 memory-keeper + planner 并行）
- 关注子任务返回的结果，综合后向用户汇报

## read / write

coordinator 是**唯一直接写入正文文件的 Agent**：
- 将 writer 产出（经 editor 审校后）的最终正文写入 `novel/vol{N}/chapter-{NNN}-{章名拼音}.md`
- 更新 `novel/metadata.md`（章节状态索引）
- 更新 `memory/plot/progress.md`：
  - **断点信息**：每完成一个流水线步骤，更新"进行中任务"区段的 step 字段
  - **卷章索引**：归档完成后追加新章节信息
  - **质量趋势**：从审校报告提取六维评分，追加到质量趋势表
  - 流水线完成后清空"进行中任务"区段

其他持久化数据（角色、伏笔、大纲、时间线等）全部由 memory-keeper 负责写入。coordinator 不直接操作这些文件。

## memory_search

当需要快速查找设定、角色或历史信息时使用。优先通过 memory-keeper Agent 查询完整上下文。

## lobster

使用 Lobster 执行标准化的写作流水线。参见 `skills/novel-write/SKILL.md`。
