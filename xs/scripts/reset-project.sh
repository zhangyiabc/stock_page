#!/bin/bash
# 完全重置小说项目：清除所有生成数据，部署最新配置，准备重新初始化
# 用法: bash scripts/reset-project.sh
#
# 此脚本会：
# 1. 停止 Gateway
# 2. 将最新配置和 agent workspace 文件部署到 ~/.openclaw/
# 3. 清除所有生成的内容数据（正文、大纲、角色、世界观、记忆等）
# 4. 重置 sessions
# 5. 重新注册 cron jobs
# 6. 重启 Gateway
#
# 注意：此脚本不会删除 agent 配置文件（SOUL.md、AGENTS.md 等），只清除生成的数据

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OPENCLAW_DIR="$HOME/.openclaw"

echo "=== 小说项目完全重置 ==="
echo ""
echo "项目源目录: $PROJECT_DIR"
echo "OpenClaw 目录: $OPENCLAW_DIR"
echo ""

# 安全确认
read -p "⚠️  此操作将清除所有已生成的小说内容（正文、大纲、角色、世界观等）。确认继续？[y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "已取消。"
  exit 0
fi

echo ""

# Step 1: 停止 Gateway
echo "[1/7] 停止 Gateway..."
openclaw gateway stop 2>/dev/null || echo "  Gateway 未运行，跳过"

# Step 2: 部署最新配置
echo "[2/7] 部署最新配置到 $OPENCLAW_DIR..."
mkdir -p "$OPENCLAW_DIR"

# 复制 openclaw.json
cp "$PROJECT_DIR/openclaw.json" "$OPENCLAW_DIR/openclaw.json"
echo "  ✓ openclaw.json"

# 同步所有 workspace 目录（只同步配置文件，不含生成数据）
for ws in workspace-coordinator workspace-planner workspace-writer workspace-editor workspace-memory; do
  if [ -d "$PROJECT_DIR/$ws" ]; then
    # 使用 rsync 同步配置文件，排除生成的数据
    rsync -av --delete \
      --exclude='novel/vol*/' \
      --exclude='novel/metadata.md' \
      --exclude='memory/characters/*.md' \
      --include='memory/characters/' \
      --exclude='memory/world/*.md' \
      --exclude='memory/world/timelines/' \
      --include='memory/world/' \
      --exclude='memory/plot/*.md' \
      --exclude='memory/plot/chapters/' \
      --exclude='memory/plot/foreshadowing/' \
      --include='memory/plot/' \
      --exclude='memory/style/style-guide.md' \
      --exclude='memory/style/vocabulary.md' \
      --include='memory/style/' \
      --exclude='memory/review/*' \
      --include='memory/review/' \
      --exclude='memory/daily/*' \
      --include='memory/daily/' \
      "$PROJECT_DIR/$ws/" "$OPENCLAW_DIR/$ws/" \
      --quiet
    echo "  ✓ $ws"
  fi
done

# 同步 shared-skills
if [ -d "$PROJECT_DIR/shared-skills" ]; then
  rsync -av --delete "$PROJECT_DIR/shared-skills/" "$OPENCLAW_DIR/shared-skills/" --quiet
  echo "  ✓ shared-skills"
fi

# 同步 prose
if [ -d "$PROJECT_DIR/prose" ]; then
  rsync -av --delete "$PROJECT_DIR/prose/" "$OPENCLAW_DIR/prose/" --quiet
  echo "  ✓ prose"
fi

# Step 3: 清除生成的数据
echo "[3/7] 清除所有生成的内容数据..."

# memory-keeper workspace: 清除所有生成的记忆数据
MEM_DIR="$OPENCLAW_DIR/workspace-memory/memory"
rm -f "$MEM_DIR/characters/"*.md 2>/dev/null
rm -f "$MEM_DIR/world/"*.md 2>/dev/null
rm -rf "$MEM_DIR/world/timelines/" 2>/dev/null
rm -f "$MEM_DIR/plot/"*.md 2>/dev/null
rm -rf "$MEM_DIR/plot/chapters/" 2>/dev/null
rm -rf "$MEM_DIR/plot/foreshadowing/" 2>/dev/null
rm -f "$MEM_DIR/style/style-guide.md" 2>/dev/null
rm -f "$MEM_DIR/style/vocabulary.md" 2>/dev/null
echo "  ✓ memory-keeper 数据已清除"

# coordinator workspace: 清除正文和进度
COORD_DIR="$OPENCLAW_DIR/workspace-coordinator"
rm -rf "$COORD_DIR/novel/vol"*/ 2>/dev/null
rm -f "$COORD_DIR/novel/metadata.md" 2>/dev/null
echo "  ✓ coordinator 正文已清除"

# 重置 progress.md 为空模板
cat > "$COORD_DIR/memory/plot/progress.md" << 'PROGRESS_EOF'
# 写作进度

## 当前状态

- 当前卷：-
- 最新章节：-
- 总字数：0
- 最后更新：-

## 进行中任务

（无）

## 卷章索引

| 卷 | 章节范围 | 字数 | 状态 | 审校结果 |
|---|---|---|---|---|

## 质量趋势

| 章节 | 爽点 | 钩子 | 节奏 | 情绪 | AI味 | 一致性 | 总评 |
|---|---|---|---|---|---|---|---|

## 近期计划

（待初始化后填写）

## 风险提醒

（无）
PROGRESS_EOF
echo "  ✓ progress.md 已重置"

# editor workspace: 清除审校报告和日志
rm -rf "$OPENCLAW_DIR/workspace-editor/memory/review/"* 2>/dev/null
rm -rf "$OPENCLAW_DIR/workspace-editor/memory/daily/"* 2>/dev/null
echo "  ✓ editor 报告已清除"

# 所有 workspace: 清除 daily 日志
for ws in workspace-coordinator workspace-planner workspace-writer workspace-memory; do
  rm -rf "$OPENCLAW_DIR/$ws/memory/daily/"* 2>/dev/null
done
echo "  ✓ 所有 daily 日志已清除"

# 确保必要的目录结构存在
mkdir -p "$MEM_DIR/characters"
mkdir -p "$MEM_DIR/world/timelines"
mkdir -p "$MEM_DIR/plot/chapters"
mkdir -p "$MEM_DIR/plot/foreshadowing"
mkdir -p "$MEM_DIR/style"
mkdir -p "$COORD_DIR/novel/vol1"
mkdir -p "$COORD_DIR/memory/plot"
mkdir -p "$COORD_DIR/memory/daily"
mkdir -p "$OPENCLAW_DIR/workspace-editor/memory/review"
mkdir -p "$OPENCLAW_DIR/workspace-editor/memory/daily"
mkdir -p "$OPENCLAW_DIR/workspace-writer/memory/daily"
mkdir -p "$OPENCLAW_DIR/workspace-planner/memory/daily"
mkdir -p "$OPENCLAW_DIR/workspace-memory/memory/daily"
echo "  ✓ 目录结构已就绪"

# Step 4: 重置 sessions
echo "[4/7] 重置 OpenClaw sessions..."
openclaw sessions reset --all 2>/dev/null || echo "  sessions 重置跳过（Gateway 未运行时无法执行，启动后发送 /new 即可）"

# Step 5: 清除旧 cron jobs
echo "[5/7] 清除旧 cron jobs..."
if [ -f "$OPENCLAW_DIR/cron/jobs.json" ]; then
  # 获取所有 job ID 并逐个删除
  openclaw cron list 2>/dev/null | grep -oP '"jobId":\s*"\K[^"]+' | while read -r job_id; do
    openclaw cron remove "$job_id" 2>/dev/null || true
  done
  echo "  ✓ 旧 cron jobs 已清除"
else
  echo "  无旧 cron jobs"
fi

# Step 6: 重启 Gateway
echo "[6/7] 启动 Gateway..."
echo "  请手动执行: openclaw gateway --port 18789"
echo "  Gateway 启动后再执行下一步"
echo ""
read -p "  Gateway 已启动？按回车继续..."

# Step 7: 注册新 cron jobs
echo "[7/7] 注册新 cron jobs..."
bash "$PROJECT_DIR/scripts/setup-cron-jobs.sh"

echo ""
echo "=== 重置完成 ==="
echo ""
echo "下一步："
echo "  1. 在对话中发送 /new 开始新 session"
echo "  2. 运行 /prose run init-project.prose 初始化小说项目"
echo "  3. 初始化完成后运行 /prose run write-chapter.prose 开始写第一章"
