---
name: portfolio-db-tools
description: 持仓数据库工具 — 通过 exec 调用 portfolio-db-mcp 管理投资者、自选股、模拟交易和收益排行
metadata: {"openclaw":{"requires":{"bins":["python"]}}}
---

# 持仓数据库工具

通过 `exec` 调用 `{baseDir}/../../mcp-servers/portfolio-db-mcp/server.py` 管理持仓数据。

## 调用格式

```bash
python {baseDir}/../../mcp-servers/portfolio-db-mcp/server.py call <tool_name> '<json_args>'
```

返回值为 JSON，直接解析使用。所有调用自动记录日志：
- `mcp-servers/logs/calls.log` — 摘要日志（单行，含时间、工具名、耗时、状态）
- `mcp-servers/logs/calls_detail.jsonl` — 详细日志（完整 JSON，不截断，含完整参数和返回结果）

## 投资者管理

### create_investor — 注册新投资者
参数: `{"feishu_user_id": "ou_xxx", "name": "昵称"}`
```bash
python {baseDir}/../../mcp-servers/portfolio-db-mcp/server.py call create_investor '{"feishu_user_id":"ou_abc123","name":"张三"}'
```
返回: `{"investor_id":"ou_abc123","name":"张三","initial_funds":1000000}`

### get_investor — 查询投资者信息
参数: `{"feishu_user_id": "ou_xxx"}`
```bash
python {baseDir}/../../mcp-servers/portfolio-db-mcp/server.py call get_investor '{"feishu_user_id":"ou_abc123"}'
```

### list_investors — 列出所有投资者
无参数:
```bash
python {baseDir}/../../mcp-servers/portfolio-db-mcp/server.py call list_investors '{}'
```

## 自选股管理

### add_watchlist — 添加自选股
参数: `{"investor_id": "ou_xxx", "ticker": "600519", "name": "贵州茅台"}`
```bash
python {baseDir}/../../mcp-servers/portfolio-db-mcp/server.py call add_watchlist '{"investor_id":"ou_abc123","ticker":"600519","name":"贵州茅台"}'
```

### remove_watchlist — 移除自选股
参数: `{"investor_id": "ou_xxx", "ticker": "600519"}`

### get_watchlist — 查询自选股列表
参数: `{"investor_id": "ou_xxx"}`
```bash
python {baseDir}/../../mcp-servers/portfolio-db-mcp/server.py call get_watchlist '{"investor_id":"ou_abc123"}'
```

## 模拟交易

### execute_trade — 执行模拟交易
参数: `{"investor_id":"ou_xxx","ticker":"600519","direction":"buy|sell","quantity":100,"price":1400.0}`
```bash
python {baseDir}/../../mcp-servers/portfolio-db-mcp/server.py call execute_trade '{"investor_id":"ou_abc123","ticker":"600519","direction":"buy","quantity":100,"price":1400.0}'
```
返回: `{"trade_id":1,"status":"executed","cost":140000.0,...}`

### get_available_funds — 查询可用资金
参数: `{"investor_id": "ou_xxx"}`

## 持仓查询

### get_positions — 查询个人持仓
参数: `{"investor_id": "ou_xxx"}`
```bash
python {baseDir}/../../mcp-servers/portfolio-db-mcp/server.py call get_positions '{"investor_id":"ou_abc123"}'
```
返回: `{"investor_id":"ou_abc123","positions":[{"ticker":"600519","quantity":100,"avg_cost":1400.0,...}]}`

### get_all_positions — 查询所有投资者持仓
无参数:
```bash
python {baseDir}/../../mcp-servers/portfolio-db-mcp/server.py call get_all_positions '{}'
```

### get_trades — 查询交易记录
参数: `{"investor_id": "ou_xxx", "days": 7}`

### get_all_today_trades — 查询今日全部交易
无参数

## 收益与排行

### save_daily_snapshot — 保存每日持仓快照
参数: `{"investor_id":"ou_xxx","total_value":1050000,"daily_pnl":5000,"daily_pnl_pct":0.5}`
```bash
python {baseDir}/../../mcp-servers/portfolio-db-mcp/server.py call save_daily_snapshot '{"investor_id":"ou_abc123","total_value":1050000,"daily_pnl":5000,"daily_pnl_pct":0.5}'
```

### get_pnl_ranking — 获取收益排行榜
参数: `{"ranking_date": "2026-03-12"}` (可选，默认今天)
```bash
python {baseDir}/../../mcp-servers/portfolio-db-mcp/server.py call get_pnl_ranking '{}'
```

## 注意事项
- 数据库文件位于 `mcp-servers/portfolio-db-mcp/portfolio.db`（SQLite）
- 每位投资者初始资金 100 万元
- 交易不允许超出可用资金或持仓数量
