#!/bin/bash
# ═══════════════════════════════════════════════════
# A 股投资分析系统 - Cron 定时任务配置
# ═══════════════════════════════════════════════════

# 每日早报 - 周一至周五 8:30 (Asia/Shanghai)
openclaw cron add \
  --name "每日早报" \
  --cron "30 8 * * 1-5" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --agent coordinator \
  --message "[CRON:MORNING_BRIEF] 执行每日早报流程：1) 调用研究员进行选股扫描 2) 调用策略师评估推荐个股 3) 组装早报消息发送到飞书群" \
  --model "kimi-k2.5" \
  --announce \
  --channel feishu \
  --to "oc_XXXXXXXX"

# 每日晚报 - 周一至周五 15:30 (收盘后)
openclaw cron add \
  --name "每日晚报" \
  --cron "30 15 * * 1-5" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --agent coordinator \
  --message "[CRON:EVENING_REPORT] 执行每日晚报流程：1) 调用持仓管家生成全体投资者收益排行 2) 获取今日大盘数据 3) 组装晚报消息发送到飞书群" \
  --model "kimi-k2.5" \
  --announce \
  --channel feishu \
  --to "oc_XXXXXXXX"

echo "✅ Cron 定时任务配置完成"
echo ""
echo "查看已配置的任务："
openclaw cron list
