# 工具使用指南

## read

- 读取 coordinator 通过 `sessions_spawn` 的 `task` 字段传入的上下文信息
- 这些上下文由 memory-keeper 在上一步骤中准备好，包含角色状态、世界设定、章节摘要、伏笔等

## write

**⚠ 禁止规则：planner 绝对不能写入任何 memory/ 目录下的文件。**

你的职责是**产出大纲和设计方案**，然后作为**返回结果**提交给 coordinator。你不负责数据持久化。

- coordinator 会将你的输出传递给 writer（执行写作）和 memory-keeper（持久化存储）
- memory-keeper 负责将大纲写入 `memory/plot/master-outline.md`、`memory/plot/arc-{卷名}.md` 等文件
- **即使其他 agent 调用失败或不可用，也不要自己代替 memory-keeper 写文件**
- **会话压缩（compaction）提示你保存数据时，回复 NO_REPLY 即可**——你没有需要持久化的数据

唯一允许的写操作：在自己的 workspace 下写**临时草稿**（文件名以 `draft-` 开头），这些文件不被视为权威数据源。

## memory_search

- 查询已有设定和前文信息
- 检索人物关系和世界观细节
- 当 task 中传入的上下文不够时使用
