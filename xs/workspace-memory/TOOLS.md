# 工具使用指南

## read

你最常用的工具。用于精确读取你自己 workspace 下的持久化文件：
- `memory/characters/{name}.md` — 角色档案
- `memory/characters/character-index.md` — 角色索引
- `memory/characters/relationships.md` — 人物关系
- `memory/world/*.md` — 世界设定文件
- `memory/plot/master-outline.md` — 总大纲
- `memory/plot/chapter-log.md` — 章节摘要索引
- `memory/plot/foreshadowing.md` — 伏笔追踪表
- `memory/style/style-guide.md` — 文风指南（唯一权威源）
- `memory/style/vocabulary.md` — 专属词汇表

**⚠ 注意：章节正文（`novel/` 目录）存储在 coordinator 的 workspace 下，你无法通过 read 访问。归档时需要的正文通过 task 的 context 传入，直接从 context 中读取。**

## write

用于更新上述所有 `memory/` 下的文件。注意：
- 更新角色文件时保留完整结构，只修改变化的字段
- 追加章节摘要时追加到文件末尾，不覆盖已有内容
- 更新伏笔表时保持 ID 递增
- **⚠ 不要将正文内容保存到 memory/ 目录下**，正文由 coordinator 写入 `novel/` 目录

## memory_search

语义搜索，用于：
- 根据描述查找相关角色（"那个会火焰术的老者"）
- 根据事件查找相关章节（"主角第一次使用飞剑"）
- 查找与特定设定相关的所有引用

## exec

必要时用于统计字数等简单操作。
