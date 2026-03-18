# 工具使用指南

## read

两种场景：

**被 coordinator 调度审校时（sub-agent）：**
- 正文和上下文通过 task 传入，一般不需要自己读文件
- 如需补充信息，可通过 memory_search 查询
- 审校时读取 `skills/review-checklist/SKILL.md` 获取完整检查清单

**Cron 任务自动执行时（独立运行）：**
- 读取 memory-keeper workspace 下的数据文件：
  - `memory/plot/chapter-log.md` — 章节摘要索引（确定最近完成章节）
  - `memory/plot/chapters/vol{N}-chapters.md` — 卷章节摘要
  - `memory/characters/*.md` — 角色档案
  - `memory/plot/foreshadowing.md` — 活跃伏笔表
  - `memory/world/timeline.md` — 时间线索引
- 读取 coordinator workspace 下的正文章节

## write

**被 coordinator 调度审校时：**
- 审校报告作为**返回结果**提交给 coordinator，不写入文件
- 修订版正文（如有）也通过返回结果提交

**Cron 任务自动执行时：**
- 一致性巡检报告写入自己 workspace 下的 `memory/daily/YYYY-MM-DD.md`
- 伏笔审计报告写入自己 workspace 下的 `memory/review/foreshadow-audit-YYYY-MM-DD.md`
- 这些报告是 editor 的工作产物，不需要写到 memory-keeper

## memory_search

- 搜索角色设定以验证一致性
- 搜索世界观规则以检查合规性
- 搜索历史章节中的描述以比对
