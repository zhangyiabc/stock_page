# 工具使用指南

## read

读取参考文件：
- 前一章正文（当 task 上下文中未包含时）

**写作风格指南和禁用词汇表**由 memory-keeper 统一管理（唯一权威源：`memory-keeper workspace/memory/style/style-guide.md`），通过 task 上下文传入。writer workspace 下不维护副本，避免数据分裂。

其他数据（角色状态、世界设定、伏笔等）同样由 memory-keeper 准备好，通过 task 上下文传入。

## write

**重要：writer 不直接写入最终正文文件。**

- 你的正文作为**返回结果**提交给 coordinator
- coordinator 负责将最终正文写入 `novel/vol{N}/chapter-{NNN}-{章名}.md`
- 你可以在 workspace 下写临时草稿用于自检

## memory_search

- 查询角色的说话方式和性格特征
- 查询特定场景的环境描写参考
- 查询专有名词的正确写法
