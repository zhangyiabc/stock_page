# 小说写作机器人 —— 基于 OpenClaw 的多 Agent 协作系统

基于 [OpenClaw](https://docs.openclaw.ai/) 搭建的长篇小说（100万字+）自动化写作系统。通过 5 个专职 Agent 分工协作，配合持久化记忆体系和标准化流水线，实现从世界观构建到逐章写作的完整创作流程。

---

## 目录

- [架构总览](#架构总览)
- [Agent 职责说明](#agent-职责说明)
  - [Coordinator（总调度）](#coordinatord总调度)
  - [Planner（策划大师）](#planner策划大师)
  - [Writer（写手）](#writer写手)
  - [Editor（编辑）](#editor编辑)
  - [Memory-keeper（记忆管家）](#memory-keeper记忆管家)
- [Agent 间通信方式](#agent-间通信方式)
  - [调度机制：Sub-Agent](#调度机制sub-agent)
  - [数据传递格式](#数据传递格式)
  - [嵌套调度](#嵌套调度)
  - [并行执行](#并行执行)
  - [Announce 回报机制](#announce-回报机制)
- [使用方式](#使用方式)
  - [环境准备](#环境准备)
  - [初始化小说项目](#初始化小说项目)
  - [写一章](#写一章)
  - [批量写作](#批量写作)
  - [修订章节](#修订章节)
  - [查看进度](#查看进度)
  - [手动操作](#手动操作)
- [文件目录结构](#文件目录结构)
- [长篇连续性保障机制](#长篇连续性保障机制)
- [定时任务（Cron）](#定时任务cron)
- [配置说明](#配置说明)

---

## 架构总览

```
  用户（Telegram / WhatsApp / Discord / WebChat）
       │
       ▼
  ┌─────────────┐
  │ Coordinator  │  总调度（唯一对外接口）
  │   📋        │
  └──────┬──────┘
         │ sessions_spawn（Sub-Agent 调度）
         │
    ┌────┼─────────┬──────────────┐
    ▼    ▼         ▼              ▼
┌───────┐ ┌──────┐ ┌──────┐ ┌────────────┐
│Planner│ │Writer│ │Editor│ │Memory-keeper│
│  🏗️   │ │  ✍️  │ │  🔍  │ │    🗄️      │
└───────┘ └──────┘ └──────┘ └────────────┘
    │         │        │           │
    └─────────┴────────┴───────────┘
                    │
              ┌─────┴──────┐
              │  文件系统    │
              │ (Memory +   │
              │  Novel 正文) │
              └────────────┘
```

**核心原则**：用户只和 Coordinator 对话，其余 Agent 通过 Sub-Agent 机制在后台运行，互不干扰。

---

## Agent 职责说明

### Coordinator（总调度）

| 属性 | 值 |
|---|---|
| Agent ID | `coordinator` |
| 模型 | `qwen/qwen3-max-2026-01-23`（Qwen3-Max，1T+ MoE，自适应工具调用，强调度编排能力） |
| Workspace | `workspace-coordinator/` |
| 对外通道 | Telegram / WhatsApp / Discord（所有 bindings 指向它） |

**职责：**

1. **用户交互入口**：接收用户的所有消息，理解创作意图
2. **任务拆分与分发**：将用户需求拆解为子任务，通过 `sessions_spawn` 分发给其他 Agent
3. **结果汇总**：收集各 Agent 的输出，综合后向用户汇报
4. **进度管理**：维护 `memory/plot/progress.md`，追踪写作进度
5. **正文存档**：将审校通过的正文保存到 `novel/` 目录

**不做的事：**
- 不直接写小说正文（交给 Writer）
- 不做世界观/大纲设计（交给 Planner）
- 不做审校（交给 Editor）
- 不管理设定数据（交给 Memory-keeper）

---

### Planner（策划大师）

| 属性 | 值 |
|---|---|
| Agent ID | `planner` |
| 模型 | `qwen/qwen3.5-plus`（397B MoE，1M 上下文，深度推理 + 创意能力，适合大纲设计） |
| Workspace | `workspace-planner/` |
| 调度方式 | 由 Coordinator 通过 Sub-Agent 调度 |

**职责：**

1. **总大纲设计**：设计小说整体故事弧线（卷结构、核心冲突、高潮节点）
2. **世界观构建**：设计地理、政治、力量体系、社会结构等设定
3. **章节大纲**：为每章产出场景级大纲（3-5个场景、情绪节奏、伏笔处理）
4. **人物弧线**：规划角色成长轨迹和转变节点
5. **伏笔网络**：设计全书的伏笔埋设和回收计划

**输出产物：**
- 总大纲 → 存入 `memory/plot/master-outline.md`
- 卷大纲 → 存入 `memory/plot/arc-{卷名}.md`
- 章节大纲 → 直接传递给 Writer

---

### Writer（写手）

| 属性 | 值 |
|---|---|
| Agent ID | `writer` |
| 模型 | `openrouter/moonshotai/kimi-k2.5`（1T MoE，256K 上下文，强创作和文本产出能力） |
| Workspace | `workspace-writer/` |
| 调度方式 | 由 Coordinator 通过 Sub-Agent 调度 |

**职责：**

1. **正文写作**：根据章节大纲和设定约束撰写完整章节
2. **场景渲染**：将大纲骨架转化为有血有肉的文字
3. **对话创作**：为不同角色写出有区分度的对话
4. **风格执行**：严格遵循 `style-guide.md` 中的文风规范

**写作规则：**
- 展示而非讲述（Show, don't tell）
- 每个场景至少调动两种感官
- 禁止水字数、AI 腔、辞藻堆砌
- 严格遵守设定，不自创规则
- 骨架不能改（细节可以发挥）

---

### Editor（编辑）

| 属性 | 值 |
|---|---|
| Agent ID | `editor` |
| 模型 | `zai/glm-5`（744B MoE，200K 上下文，agentic 能力强，细致分析和创意写作优秀） |
| Workspace | `workspace-editor/` |
| 调度方式 | Sub-Agent 调度 + Cron 定时任务 |

**职责：**

1. **章节审校**（每章写完后）：
   - 人物性格/外貌/对话风格一致性
   - 时间线和空间逻辑正确性
   - 世界观设定合规性
   - 伏笔处理合理性
   - 文笔质量和节奏控制
   - 与前一章的衔接自然度

2. **每日一致性巡检**（Cron 每天凌晨 3 点）：
   - 交叉验证最近章节与角色档案
   - 检查时间线冲突
   - 输出问题报告

3. **每周伏笔审计**（Cron 每周日凌晨 4 点）：
   - 遍历伏笔追踪表
   - 标记超期（>20 章）未回收伏笔为高风险
   - 输出审计报告

**审校严重程度分级：**
- 🔴 严重：设定/逻辑硬伤、人物行为矛盾（必须修复）
- 🟡 中等：节奏/张力问题、伏笔处理不当（建议修复）
- 🟢 轻微：文笔润色（可选修复）

---

### Memory-keeper（记忆管家）

| 属性 | 值 |
|---|---|
| Agent ID | `memory-keeper` |
| 模型 | `minimax/MiniMax-M2.5`（原生 Agent 模型，工具调用 SOTA，成本极低，适合高频数据操作） |
| Workspace | `workspace-memory/` |
| 调度方式 | 由 Coordinator 通过 Sub-Agent 调度 |

**职责：**

1. **上下文查询**：当其他 Agent 需要信息时，精确检索并组装上下文包
2. **章节归档**：每章完成后执行标准归档流程
   - 提取 500 字章节摘要 → `chapter-log.md`
   - 更新角色状态文件 → `characters/*.md`
   - 管理伏笔 → `foreshadowing.md`
   - 更新时间线 → `timeline.md`
3. **设定管理**：维护所有世界观和角色设定文件的准确性

**管理的数据文件：**

```
memory/
├── characters/           # 角色数据
│   ├── character-index.md    # 角色总索引
│   ├── relationships.md      # 人物关系图谱
│   └── {角色名拼音}.md       # 各角色档案
├── world/                # 世界设定
│   ├── worldbuilding.md      # 世界观总纲
│   ├── magic-system.md       # 力量体系
│   ├── geography.md          # 地理设定
│   ├── factions.md           # 势力组织
│   ├── history.md            # 背景历史
│   └── timeline.md           # 故事内时间线
├── plot/                 # 剧情数据
│   ├── master-outline.md     # 总大纲
│   ├── arc-{卷名}.md         # 卷大纲
│   ├── chapter-log.md        # 已完成章节摘要
│   └── foreshadowing.md      # 伏笔追踪表
└── style/                # 风格数据
    ├── style-guide.md        # 文风指南
    └── vocabulary.md         # 专属用语表
```

---

## Agent 间通信方式

### 调度机制：Sub-Agent

所有 Agent 之间的通信都通过 OpenClaw 的 **Sub-Agent 机制**（`sessions_spawn` 工具）实现。

```
Coordinator 调用 sessions_spawn:
  ┌───────────────────────────────────────┐
  │ sessions_spawn({                      │
  │   agentId: "memory-keeper",           │
  │   task: "为第15章写作准备上下文...",     │
  │   model: "sonnet",                    │
  │   runTimeoutSeconds: 1800             │
  │ })                                    │
  └───────────────────────────────────────┘
         │
         ▼
  Memory-keeper 在独立 session 中执行任务
         │
         ▼
  通过 Announce 机制将结果回报给 Coordinator
```

**关键特性：**
- **非阻塞**：`sessions_spawn` 立即返回 `runId`，不阻塞调用方
- **独立 session**：每个子任务有独立的 session key `agent:<id>:subagent:<label>`
- **隔离性**：各 Agent workspace 完全隔离，不共享 session 上下文
- **超时保护**：`runTimeoutSeconds: 1800`（30 分钟），防止卡死

### 数据传递格式

Agent 之间通过 `sessions_spawn` 的 `task` 字段传递上下文。采用标记分隔的结构化格式：

```markdown
=== 角色状态 ===
- 张三：目前身处古墓第三层，受了轻伤...
- 李四：在城外等候，不知张三已进入古墓...

=== 世界设定 ===
- 古墓共五层，每层有不同机关...
- 禁止使用火系能力（会引发坍塌）...

=== 近章摘要 ===
- 第13章：张三发现古墓入口...
- 第14章：张三独自进入，遇到第一个机关...

=== 伏笔清单 ===
- #023 [活跃] 古墓壁画上的神秘符文 → 计划第18章揭示含义
- #019 [活跃] 李四的真实身份 → 计划第20章揭露

=== 大纲规划 ===
- 第15章要点：张三到达第三层，触发核心机关，发现古墓真正的秘密...
```

### 嵌套调度

系统配置了 `maxSpawnDepth: 2`，支持两级调度：

```
Coordinator (depth 0)
  └─ spawn → Planner (depth 1, 编排者角色)
                └─ spawn → Writer (depth 2, 叶子节点)
```

| 深度 | 角色 | 可以再 spawn？ |
|---|---|---|
| 0 | Coordinator（主 Agent） | 始终可以 |
| 1 | 子 Agent（可作为编排者） | 当 `maxSpawnDepth >= 2` 时可以 |
| 2 | 叶子 Agent | 不可以 |

### 并行执行

多个独立任务可以同时 spawn，最多 8 个并发（`maxConcurrent: 8`）：

```
Coordinator
  ├─ spawn → Memory-keeper (查询上下文)  ──┐
  │                                        ├─ 并行执行
  └─ spawn → Planner (设计章节大纲)      ──┘
```

每个 Agent session 最多 5 个活跃子任务（`maxChildrenPerAgent: 5`）。

### Announce 回报机制

子任务完成后，通过 Announce 将结果回报给调用方：

```
子 Agent 完成任务
       │
       ▼
  Announce 消息（包含）:
  ├── Status: completed successfully / failed / timed out
  ├── Result: 子 Agent 的回复文本
  ├── Token 用量统计
  ├── 运行时长
  └── Session key（可用于追溯历史）
       │
       ▼
  Coordinator 收到 Announce，继续下一步
```

---

## 使用方式

### 环境准备

```bash
# 1. 安装 OpenClaw
curl -fsSL https://openclaw.ai/install.sh | bash

# 2. 运行初始化向导
openclaw onboard --install-daemon

# 3. 将配置文件复制到 OpenClaw 配置目录（或设置环境变量）
cp openclaw.json ~/.openclaw/openclaw.json
# 或者
export OPENCLAW_CONFIG_PATH=/path/to/xiaoshuo/openclaw.json

# 4. 启用 OpenProse 插件
openclaw plugins enable open-prose

# 5. 连接消息渠道（按需选择）
openclaw channels login --channel telegram
openclaw channels login --channel whatsapp

# 6. 启动 Gateway
openclaw gateway --port 18789

# 7. 验证 Agent 配置
openclaw agents list --bindings

# 8. 注册定时任务（Cron Jobs）
# OpenClaw 的 cron jobs 通过 CLI 注册，不是在 openclaw.json 中定义
bash scripts/setup-cron-jobs.sh

# 验证 cron 任务
openclaw cron list
```

### 初始化小说项目

在消息渠道中向机器人发送以下命令：

```
/prose run init-project.prose
```

系统会依次询问：
1. 小说名称
2. 小说类型（玄幻/科幻/悬疑/历史/都市）
3. 核心设定/故事前提
4. 目标总字数

**流程：** Planner 设计世界观 → Planner 设计角色 → Planner 设计总大纲 → Memory-keeper 将所有设定写入文件 → 完成

或者直接对话：

```
用户：我想写一本玄幻小说，讲述一个废柴少年逆天改命的故事，目标100万字
```

Coordinator 会自动理解意图并调度整个初始化流程。

### 写一章

**方式 1：OpenProse 流水线**

```
/prose run write-chapter.prose
```

**方式 2：自然语言对话**

```
用户：写第15章，主角进入古墓发现了壁画上的秘密
```

**方式 3：使用内置 Skill**

Coordinator 会自动识别并调用 `novel-write` skill，执行标准 5 步流水线：

```
Memory-keeper 查询上下文
       ↓
Planner 产出章节大纲
       ↓
Writer 撰写正文
       ↓
Editor 审校
       ↓
Memory-keeper 归档（摘要 + 角色更新 + 伏笔登记）
```

### 批量写作

连续写多章：

```
/prose run batch-write.prose
```

输入起始和结束章节号，系统会按顺序完成每章的完整流水线。

或自然语言：

```
用户：从第10章写到第15章
```

### 修订章节

```
/prose run revise-chapter.prose
```

或自然语言：

```
用户：修改第8章，把主角和反派的对话改得更紧张一些，增加心理博弈的描写
```

系统会读取原文 → Writer 按要求修订 → Editor 审校修订版 → Memory-keeper 更新相关记录。

### 查看进度

```
用户：现在进度怎么样了
用户：写到哪了
```

Coordinator 读取 `memory/plot/progress.md`，汇报当前状态：
- 当前卷和最新章节
- 总字数
- 待处理任务
- 风险提醒（伏笔超期、角色断线等）

### 手动操作

```bash
# 查看所有 session
openclaw sessions --json

# 查看 Agent 列表和绑定
openclaw agents list --bindings

# 查看消息渠道状态
openclaw channels status --probe

# 手动触发一致性检查
openclaw cron run consistency-check

# 手动压缩 session 上下文
# 在对话中发送：
/compact

# 重置 session（开始新对话）
/new

# 查看当前上下文使用情况
/status
/context list
```

---

## 文件目录结构

```
xiaoshuo/
├── openclaw.json                          # Gateway 主配置
├── .gitignore
├── README.md                              # 本文件
│
├── prose/                                 # OpenProse 流水线
│   ├── init-project.prose                 #   项目初始化
│   ├── write-chapter.prose                #   标准写章
│   ├── batch-write.prose                  #   批量写作
│   └── revise-chapter.prose               #   章节修订
│
├── shared-skills/                         # 所有 Agent 共享的 Skill
│   └── novel-common/
│       └── SKILL.md                       #   通用规范（路径/格式/编号）
│
├── workspace-coordinator/                 # Coordinator Agent
│   ├── AGENTS.md                          #   操作指南
│   ├── SOUL.md                            #   人格设定
│   ├── IDENTITY.md                        #   名称标识
│   ├── USER.md                            #   用户信息
│   ├── TOOLS.md                           #   工具使用规范
│   ├── MEMORY.md                          #   长期记忆
│   ├── memory/
│   │   └── plot/
│   │       └── progress.md                #   写作进度
│   ├── novel/                             #   小说正文存储
│   │   └── vol{N}/chapter-{NNN}.md        #   各章正文
│   └── skills/
│       └── novel-write/
│           └── SKILL.md                   #   写作流水线 Skill
│
├── workspace-planner/                     # Planner Agent
│   ├── AGENTS.md / SOUL.md / IDENTITY.md / TOOLS.md / MEMORY.md
│   └── memory/
│       ├── plot/                          #   大纲相关
│       └── daily/                         #   工作日志
│
├── workspace-writer/                      # Writer Agent
│   ├── AGENTS.md / SOUL.md / IDENTITY.md / TOOLS.md / MEMORY.md
│   └── memory/
│       └── daily/
│
├── workspace-editor/                      # Editor Agent
│   ├── AGENTS.md / SOUL.md / IDENTITY.md / TOOLS.md / MEMORY.md
│   └── memory/
│       ├── review/
│       │   └── foreshadowing-report.md    #   伏笔审计报告
│       └── daily/
│
└── workspace-memory/                      # Memory-keeper Agent
    ├── AGENTS.md / SOUL.md / IDENTITY.md / TOOLS.md / MEMORY.md
    └── memory/
        ├── characters/                    #   角色数据
        │   ├── character-index.md
        │   ├── relationships.md
        │   └── {角色名拼音}.md
        ├── world/                         #   世界设定
        │   ├── worldbuilding.md
        │   ├── magic-system.md
        │   ├── geography.md
        │   ├── factions.md
        │   ├── history.md
        │   └── timeline.md
        ├── plot/                          #   剧情数据
        │   ├── master-outline.md
        │   ├── arc-{卷名}.md
        │   ├── chapter-log.md
        │   └── foreshadowing.md
        └── style/                         #   风格数据
            ├── style-guide.md
            └── vocabulary.md
```

---

## 长篇连续性保障机制

本系统设计目标支撑 **300 万字以上**（约 300~400 章，10~15 卷）的超长篇创作。LLM 的上下文窗口（即使 200K tokens）也装不下全文，因此核心设计原则是 **"永远不需要一次性加载全文"**。

### 1. 分片存储架构（核心设计）

所有会随章节线性增长的数据文件都采用 **按卷分片** 存储，避免单文件膨胀：

| 数据类型 | 存储方式 | 300章时的单文件大小 |
|---|---|---|
| 章节摘要 | 按卷分片 `chapters/vol{N}-chapters.md` | ~5万字/卷（可控） |
| 伏笔 | 活跃表 + 归档分离 + 按卷详情 | 活跃表 <100 条（精简） |
| 时间线 | 按卷分片 `timelines/vol{N}-timeline.md` | ~100条/卷（可控） |
| 角色状态日志 | 主文件保留最近 50 条，超出归档 | <50条（固定上限） |

**不分片的文件**（天然不会过大）：世界观、力量体系、地理、势力等设定文件。

### 2. 分层记忆（永不丢失）

所有关键信息都持久化到 Markdown 文件，不依赖 session 历史：

| 记忆层 | 内容 | 文件 |
|---|---|---|
| 设定层 | 世界观、力量体系、地理 | `memory/world/*.md` |
| 角色层 | 人物档案、关系、状态 | `memory/characters/*.md` |
| 剧情层 | 大纲、章节摘要、伏笔 | `memory/plot/**/*.md` |
| 风格层 | 文风、用语 | `memory/style/*.md` |

### 3. 按需加载上下文

每章写作前，Memory-keeper 只从对应分片中加载当前需要的信息（约 1 万字），与总字数无关：

| 上下文项 | 来源 | 大小 |
|---|---|---|
| 当前卷大纲 | `arc-{卷名}.md` | ~2000 字 |
| 最近 3~5 章摘要 | `chapters/vol{N}-chapters.md` 末尾 | ~2500 字 |
| 相关角色档案 | `characters/{name}.md` 的当前状态段 | ~1000-3000 字 |
| 活跃伏笔 | `foreshadowing.md` 活跃表 | ~500 字 |
| 相关设定要点 | `world/*.md` 相关段落 | ~1000 字 |
| **合计** | | **~1 万字** |

无论小说写到 50 万字还是 500 万字，每次写章的上下文加载量始终稳定在 ~1 万字。

### 4. 自动 Memory Flush

Session 接近上下文窗口上限时，OpenClaw 自动触发 Memory Flush，提醒 Agent 将关键信息写入文件：

```json
"memoryFlush": {
  "enabled": true,
  "softThresholdTokens": 8000
}
```

### 5. Vector 语义搜索

通过 QMD + Hybrid Search（BM25 + 向量搜索）实现对所有 memory 分片文件的语义检索，即使不记得准确措辞也能跨卷找到相关内容。

### 6. Compaction（上下文压缩）

长对话自动触发 Compaction（使用 `glm-4.7` 做压缩），将旧历史压缩为摘要，保持 session 可用。

### 7. 每章归档闭环

每章完成后的归档流程确保信息不丢失：

```
正文保存 → 卷分片摘要追加 → 角色状态更新（覆盖写当前状态）
→ 伏笔登记（活跃表 + 卷详情）→ 卷时间线追加 → 全局索引更新
```

### 8. 规模极限估算

| 规模 | 章数 | 卷数 | 分片文件总数 | 角色文件数 | 是否可支撑 |
|---|---|---|---|---|---|
| 100 万字 | ~120 章 | ~4 卷 | ~15 个 | ~30 个 | 完全没问题 |
| 300 万字 | ~350 章 | ~12 卷 | ~40 个 | ~80 个 | 可以支撑 |
| 500 万字 | ~600 章 | ~20 卷 | ~65 个 | ~120 个 | 可以支撑，需关注索引文件大小 |
| 1000 万字 | ~1200 章 | ~40 卷 | ~125 个 | ~200+ | 需要二级分片（按部/篇） |

**理论上限约 500~800 万字**。超过此规模需要在"卷"之上再引入"部/篇"层级的分片。

---

## 定时任务（Cron）

> **注意：** OpenClaw 的 cron jobs 通过 `openclaw cron add` CLI 命令注册，存储在 `~/.openclaw/cron/jobs.json`。  
> `openclaw.json` 中的 `cron` 字段仅控制全局开关（enabled、maxConcurrentRuns 等），不定义具体 job。  
> 首次部署时运行 `bash scripts/setup-cron-jobs.sh` 完成注册。

| 任务 | 执行 Agent | 时间 | 内容 |
|---|---|---|---|
| 一致性巡检 | Editor | 每天 03:00 | 检查最近章节的人设/时间线/设定矛盾 |
| 伏笔审计 | Editor | 每周日 04:00 | 标记超期伏笔，生成审计报告 |
| 进度汇总 | Coordinator | 每天 22:00 | 统计当日写作进展，更新进度文件 |

常用操作：
```bash
openclaw cron list                    # 查看所有任务
openclaw cron run <jobId>             # 手动触发
openclaw cron runs --id <jobId>       # 查看运行历史
openclaw cron edit <jobId> --message "新提示词"  # 修改任务
```

---

## 配置说明

### 模型选择策略

| Agent | 模型 | Provider | 理由 |
|---|---|---|---|
| **Coordinator** | qwen3-max-2026-01-23 | 通义千问 | 1T+ MoE，自适应工具调用（Search/Memory/Code），原生 Agent 调度编排能力，256K 上下文 |
| **Planner** | qwen3.5-plus | 通义千问 | 397B MoE，**1M 上下文**（可一次性分析整卷内容），深度推理 + 创意能力顶尖，适合长篇故事架构设计 |
| **Writer** | kimi-k2.5 | Moonshot | 1T MoE，原生多模态，强文本创作和产出能力，Agent Swarm 架构（可并行生成多场景），256K 上下文 |
| **Editor** | glm-5 | 智谱 | 744B MoE，agentic 工程能力最强的开源模型之一，创意写作高质量，200K 上下文，适合细致审校分析 |
| **Memory-keeper** | MiniMax-M2.5 | MiniMax | 原生 Agent 模型，工具调用 SOTA（τ²-Bench 87.4），**成本仅为同级 1/10~1/20**，高频数据操作极具性价比 |
| **Compaction** | glm-4.7 | 智谱 | 编程/工具调用能力强（SWE-bench 73.8%），200K 上下文，做上下文压缩摘要性价比高 |
| **Sub-agent 默认** | MiniMax-M2.5 | MiniMax | 子任务频繁，成本控制关键；M2.5 每秒 100 token，4 个 Agent 连续工作一年约 1 万美元 |

#### 备选模型（未分配但可灵活调用）

| 模型 | 特点 | 适用场景 |
|---|---|---|
| qwen3-coder-next | 80B MoE（仅 3B 激活），Apache 2.0 开源，极轻量 | 本地部署做轻量任务、辅助代码生成 |
| qwen3-coder-plus | 480B MoE（35B 激活），编程 SOTA，256K~1M 上下文 | 可替代 glm-4.7 做 compaction，或处理需要代码的工具任务 |

### 关键配置参数

```json
{
  "subagents": {
    "maxSpawnDepth": 2,
    "maxChildrenPerAgent": 5,
    "maxConcurrent": 8,
    "runTimeoutSeconds": 1800,
    "model": "minimax/MiniMax-M2.5"
  },
  "compaction": {
    "model": "zai/glm-4.7"
  },
  "session": {
    "idleMinutes": 480,
    "pruneAfter": "90d"
  },
  "memory": {
    "backend": "qmd",
    "hybrid": true
  }
}
```

### 环境变量

使用前需设置以下 API Key 环境变量：

```bash
export QWEN_API_KEY="sk-..."        # 通义千问（qwen3.5-plus, qwen3-max, qwen3-coder-*）
export ZAI_API_KEY="sk-..."         # 智谱 Z.AI（glm-5, glm-4.7）
export MINIMAX_API_KEY="sk-..."     # MiniMax（MiniMax-M2.5）
# kimi-k2.5 通过 OpenRouter 访问，需要 OpenRouter API Key
export OPENROUTER_API_KEY="sk-..."  # OpenRouter（kimi-k2.5）
```

### 消息渠道

当前配置了三个渠道绑定，均指向 Coordinator：

- **Telegram**：推荐日常使用，支持长消息
- **WhatsApp**：移动端方便
- **Discord**：支持线程绑定

可在 `openclaw.json` 的 `bindings` 中按需调整。
