---
name: novel-common
description: 小说创作项目的通用工具和约定。所有 Agent 共享的基础规范。
user-invocable: false
metadata: {"openclaw": {"emoji": "📚", "always": true}}
---

# 小说创作通用规范

## 数据归属原则

**所有持久化数据统一由 memory-keeper 管理，存储在 memory-keeper 的 workspace 下。** 其他 Agent 不在自己的 workspace 下维护数据副本。

| Agent | 读数据方式 | 写数据方式 | 禁止操作 |
|---|---|---|---|
| **memory-keeper** | 直接读自己 workspace 下的文件 | 直接写自己 workspace 下的文件 | — |
| **planner** | 从 task 传入的上下文中读取 | 作为返回结果输出，由 memory-keeper 持久化 | **禁止写入任何 memory/ 文件，禁止调用 sessions_spawn** |
| **writer** | 从 task 传入的上下文中读取 | 正文由 coordinator 写入 `novel/` 目录 | 禁止写入 memory/ 文件 |
| **editor** | 从 task 传入的上下文中读取 | 审校报告作为返回结果输出 | 禁止写入 memory/ 文件（Cron 任务除外） |
| **coordinator** | 调度各 agent，汇总结果 | 写入 `novel/` 正文 + 更新 `progress.md` | 禁止自行编排步骤替代 prose 流水线 |

这样做的原因：避免同一数据在多个 workspace 下出现不同版本（数据分裂），保证 memory-keeper 的数据始终是唯一权威源。

## 文件路径约定

以下路径均相对于**对应 Agent 自己的 workspace**：

### 小说正文（存储在 coordinator workspace 下）

- 路径格式：`novel/vol{卷号}/chapter-{三位数章节号}-{章名}.md`
- 示例：`novel/vol1/chapter-001-出山.md`、`novel/vol3/chapter-087-龙虎风云.md`
- 章节号全局递增，不按卷重置（第二卷第一章是 chapter-031 而不是 chapter-001）
- 每卷一个子目录，卷号用阿拉伯数字

**目录结构示例：**
```
workspace-coordinator/novel/
├── vol1/
│   ├── chapter-001-出山.md               # 第1章 出山
│   ├── chapter-002-故人相逢.md           # 第2章 故人相逢
│   ├── chapter-003-夜雨.md               # 第3章 夜雨
│   └── ...chapter-030-风暴前夕.md        # 第30章 风暴前夕
├── vol2/
│   ├── chapter-031-破镜.md               # 第31章 破镜
│   └── ...
├── vol10/
│   └── chapter-280-终结.md
└── metadata.md                            # 全书元数据（卷章对照、总字数统计）
```

**命名规则：**
- 章节号固定三位数字，不足补零：`001`, `002`, ..., `999`
- 如超过999章，扩展为四位：`chapter-1000-xxx.md`
- 章名部分直接使用中文章名
- 如果章名较长，可适当缩写：「第一百章 风起云涌天下乱」→ `chapter-100-风起云涌.md`

### 记忆文件（memory-keeper workspace 下）

**索引文件（入口）：**
- 角色索引：`memory/characters/character-index.md`
- 章节摘要索引：`memory/plot/chapter-log.md`
- 伏笔索引 + 活跃表：`memory/plot/foreshadowing.md`
- 时间线索引：`memory/world/timeline.md`

**分片文件（按卷存储，避免单文件过大）：**
- 卷章节摘要：`memory/plot/chapters/vol{N}-chapters.md`
- 卷伏笔详情：`memory/plot/foreshadowing/vol{N}-planted.md`
- 伏笔归档：`memory/plot/foreshadowing/archived.md`
- 卷时间线：`memory/world/timelines/vol{N}-timeline.md`

**角色文件：**
- 角色档案：`memory/characters/{角色名拼音小写}.md`
- 角色状态日志归档：`memory/characters/{角色名拼音小写}-history.md`（主文件超50条时）
- 人物关系：`memory/characters/relationships.md`

**设定文件（通常不分片）：**
- 世界观：`memory/world/worldbuilding.md`
- 力量体系：`memory/world/magic-system.md`
- 地理：`memory/world/geography.md`
- 势力：`memory/world/factions.md`
- 历史：`memory/world/history.md`

**其他：**
- 总大纲：`memory/plot/master-outline.md`
- 卷大纲：`memory/plot/arc-{卷名}.md`
- 文风指南：`memory/style/style-guide.md`（唯一权威源，由 memory-keeper 管理。writer 不维护副本，通过 task 上下文获取）
- 词汇表：`memory/style/vocabulary.md`
- 进度：coordinator workspace 下 `memory/plot/progress.md`

**daily/ 目录所有权：**

每个 Agent 只写自己 workspace 下的 `memory/daily/` 目录，内容各不相同：

| Agent | daily/ 写入内容 |
|---|---|
| coordinator | 每日进度汇总（Cron 产出） |
| editor | 每日一致性巡检报告（Cron 产出） |
| memory-keeper | 数据变更日志（归档操作的详细记录） |
| planner / writer | 不写 daily/（无此需求） |

## 章节正文文件格式

文件名示例：`chapter-001-chushan.md`，文件内容格式如下：

```markdown
# 第1章 出山

（正文内容）

---
<!-- metadata -->
<!-- chapter: 001 -->
<!-- title: 出山 -->
<!-- volume: 1 -->
<!-- words: XXXX -->
<!-- date: YYYY-MM-DD -->
<!-- outline_version: {大纲版本} -->
<!-- reviewed: true/false -->
```

- 文件内的 `# 第X章 {章节标题}` 使用中文章名
- metadata 中的 `title` 字段也记录中文章名，用于程序化检索
- 文件名中的章名与内容中的章名必须一致

## 伏笔 ID 规范

- 格式：`#` + 三位递增数字，如 `#001`、`#042`、`#128`
- 全局唯一，不复用已废弃的 ID

## 角色编号规范

- 格式：`C` + 三位递增数字，如 `C001`、`C015`
- 在 `character-index.md` 中统一管理

## 章节摘要规范

每章归档时产出的摘要必须包含：
1. 主要情节事件（按发生顺序）
2. 角色状态变化
3. 新伏笔和回收的伏笔
4. 故事内时间推进
5. 不超过500字

## Agent 间数据传递约定

通过 `sessions_spawn` 的 `task` 字段传递的上下文数据，使用以下标记分隔：

```
=== 角色状态 ===
（内容）

=== 世界设定 ===
（内容）

=== 近章摘要 ===
（内容）

=== 伏笔清单 ===
（内容）

=== 大纲规划 ===
（内容）

=== 文风指南 ===
（内容）

=== 专有名词 ===
（内容）
```

## OpenProse 流水线与 Workspace 配置的关系

`prose/` 目录下的 `.prose` 文件定义了自动化流水线。其中每个 `agent` 块的 `prompt` 是**补充性质的简短角色提示**，不替代 workspace 下的 SOUL.md / AGENTS.md / TOOLS.md 配置。

优先级关系：
- **Workspace 配置**（SOUL.md + AGENTS.md + TOOLS.md + Skills）= Agent 的核心人格和行为规范，始终生效
- **Prose agent prompt** = 当前流水线中的补充指令，对特定任务做额外强调

因此：
- Prose 中的 agent prompt 应保持简短（1-2句），只强调该流水线最关键的要求
- 详细的规则、清单、格式模板等不应放在 prose prompt 中（已在 workspace 配置里）
- 如果 prose prompt 与 workspace 配置冲突，以 workspace 配置为准

**⚠ Prose 流水线是强制执行路径。** 写章节时 coordinator 必须通过对应的 prose 流水线执行，不得自行编排步骤或改变执行顺序。批量写作时必须逐章串行（每章走完完整流水线后才开始下一章），禁止先统一规划再统一写作。

## 断点恢复机制

写作流水线每完成一个关键步骤后，coordinator 应更新 `progress.md` 的"进行中任务"区段，记录当前步骤状态。如果流水线因故中断（API 超时、模型不可用等），可以从断点恢复而不需要重头开始。

断点步骤标记：`context` → `outline` → `draft` → `review` → `rewrite` → `archive`
