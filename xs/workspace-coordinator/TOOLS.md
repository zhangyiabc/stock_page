# 工具使用指南

## sessions_spawn

你的主要工具。用于调度其他 Agent 执行任务。

调度规范：
- 每次 spawn 必须在 task 中包含足够的上下文信息
- 需要并行的任务可以同时 spawn 多个 Agent（如 Step 1 的 memory-keeper + planner 并行）
- 关注子任务返回的结果，综合后向用户汇报

## read

**你的 read 工具只能读取自己 workspace 下的文件**。可以读取：
- `novel/` 目录下的正文文件
- `memory/plot/progress.md`（你自己的进度文件）
- `skills/` 目录下的技能文件

**以下数据存储在 memory-keeper 的 workspace 中，你的 read 无法访问**：
- `memory/characters/`、`memory/plot/chapter-log.md`、`memory/plot/foreshadowing.md`
- `memory/world/`、`memory/style/`
- 需要这些信息时，必须 spawn memory-keeper 查询

## write

coordinator 的 write 权限**严格限定**在以下三类文件，不可越界：

| 允许写入 | 路径 | 用途 |
|---|---|---|
| 章节正文 | `novel/vol{N}/chapter-{NNN}-{章名}.md` | 保存 writer 最终产出 |
| 元数据索引 | `novel/metadata.md` | 章节状态索引 |
| 进度追踪 | `memory/plot/progress.md` | 断点信息、卷章索引、质量趋势 |

`progress.md` 更新内容：
- **断点信息**：每完成一个流水线步骤，更新"进行中任务"区段的 step 字段
- **卷章索引**：归档完成后追加新章节信息
- **质量趋势**：从审校报告提取六维评分，追加到质量趋势表
- 流水线完成后清空"进行中任务"区段

**⚠ 禁止写入以下文件——这些全部由 memory-keeper 负责：**
- `memory/characters/` 下的任何角色文件
- `memory/plot/` 下除 `progress.md` 以外的文件（大纲、章节摘要、伏笔等）
- `memory/world/` 下的任何世界设定文件
- `memory/style/` 下的任何文风/词汇文件
- **即使 memory-keeper 调用失败或超时，也不要自己"补救"去写这些文件**——应该重试 memory-keeper 或向用户报告问题
- **会话压缩（compaction）提示保存数据时，只将信息写入 `progress.md`，不要写入其他 memory/ 文件**

写章节时必须通过 prose 流水线执行（`write-chapter.prose` / `batch-write.prose`），不要自行编排 sessions_spawn 调用来替代流水线。

## memory_search

⚠ `memory_search` 搜索的是你自己 workspace 下的数据。要搜索角色、设定、伏笔等信息，**必须 spawn memory-keeper 查询**，不要直接用 memory_search。

## lobster

使用 Lobster 执行标准化的写作流水线。参见 `skills/novel-write/SKILL.md`。
