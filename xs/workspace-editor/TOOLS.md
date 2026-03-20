# 工具使用指南

## read

两种场景：

**被 coordinator 调度审校时（sub-agent）：**
- ⚠ **正文和大纲已通过 task 的 context 传入**，直接从 context 中读取，**不要用 read 工具去查找正文文件**
- 正文存储在 coordinator 的 workspace 下（你无法直接访问），所以用 read 工具去找正文文件一定会失败
- 如需补充角色/设定信息，优先使用 `memory_search`，不要猜测文件路径
- 审校时读取 `skills/review-checklist/SKILL.md` 获取完整检查清单

**Cron 任务自动执行时（独立运行）：**
- 使用 `memory_search` 搜索 memory-keeper 管理的数据
- 读取自己 workspace 下的技能文件

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
