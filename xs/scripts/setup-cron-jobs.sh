#!/bin/bash
# 注册小说写作系统的定时任务
# 用法: bash scripts/setup-cron-jobs.sh
#
# OpenClaw 的 cron jobs 通过 CLI 创建，存储在 ~/.openclaw/cron/jobs.json
# 不是在 openclaw.json 中定义的。openclaw.json 中的 cron 字段只控制全局开关。
#
# 参考文档: https://docs.openclaw.ai/automation/cron-jobs

set -e

echo "=== 注册小说写作系统定时任务 ==="
echo ""

# 1. 每日一致性巡检（凌晨 3 点，editor 执行）
echo "[1/3] 注册每日一致性巡检..."
openclaw cron add \
  --name "consistency-check" \
  --cron "0 3 * * *" \
  --tz "Asia/Shanghai" \
  --agent editor \
  --session isolated \
  --message "执行每日一致性检查：从 memory-keeper workspace 读取 memory/plot/chapter-log.md 确定最近完成章节，从对应卷分片 memory/plot/chapters/ 读取摘要，读取 memory/characters/ 下相关角色文件，检查最近写完的章节是否存在人物性格矛盾、时间线错误、设定冲突。将发现的问题写入自己 workspace 的 memory/daily/ 下以今天日期命名的文件。" \
  --announce

# 2. 每周伏笔审计（每周日凌晨 4 点，editor 执行）
echo "[2/3] 注册每周伏笔审计..."
openclaw cron add \
  --name "foreshadowing-audit" \
  --cron "0 4 * * 0" \
  --tz "Asia/Shanghai" \
  --agent editor \
  --session isolated \
  --message "执行每周伏笔审计：从 memory-keeper workspace 读取 memory/plot/foreshadowing.md 中的活跃伏笔表，标记超过20章未回收的伏笔为高风险，生成审计报告写入自己 workspace 的 memory/review/ 下以今天日期命名的审计报告文件。" \
  --announce

# 3. 每日进度汇总（晚上 10 点，coordinator 执行）
echo "[3/3] 注册每日进度汇总..."
openclaw cron add \
  --name "progress-summary" \
  --cron "0 22 * * *" \
  --tz "Asia/Shanghai" \
  --agent coordinator \
  --session isolated \
  --message "生成每日写作进度摘要：统计今日完成章节、总字数变化、待处理任务，分析最近章节的质量趋势（从审校报告中提取六维评分），更新 memory/plot/progress.md。" \
  --announce

echo ""
echo "=== 定时任务注册完成 ==="
echo ""
echo "查看已注册的任务: openclaw cron list"
echo "手动触发任务:     openclaw cron run <jobId>"
echo "查看运行历史:     openclaw cron runs --id <jobId>"
