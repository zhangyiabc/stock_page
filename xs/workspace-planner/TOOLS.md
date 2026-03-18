# 工具使用指南

## read

- 读取 coordinator 通过 `sessions_spawn` 的 `task` 字段传入的上下文信息
- 这些上下文由 memory-keeper 在上一步骤中准备好，包含角色状态、世界设定、章节摘要、伏笔等

## write

**重要：planner 不直接写入持久化数据文件。**

所有大纲、设定等持久化数据统一由 memory-keeper 管理，存储在 memory-keeper 的 workspace 下。

planner 的输出方式：
- 你的大纲、设计方案作为**返回结果**提交给 coordinator
- coordinator 会将你的输出传递给 writer（执行写作）和 memory-keeper（持久化存储）
- memory-keeper 负责将大纲写入 `memory/plot/master-outline.md`、`memory/plot/arc-{卷名}.md` 等文件

唯一例外：planner 可以在自己的 workspace 下写**临时草稿**（如需要多轮迭代的复杂设计），文件名以 `draft-` 开头，这些文件不被视为权威数据源。

## memory_search

- 查询已有设定和前文信息
- 检索人物关系和世界观细节
- 当 task 中传入的上下文不够时使用
