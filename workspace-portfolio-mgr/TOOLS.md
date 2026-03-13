# TOOLS.md - 算盘 · 持仓管家

## 数据工具（通过 exec 调用）

所有数据工具通过 `exec` 命令调用 Python 脚本。调用格式：
```bash
python <script_path> call <tool_name> '<json_args>'
```

### portfolio-db-mcp（持仓数据库）
脚本路径：`mcp-servers/portfolio-db-mcp/server.py`

**投资者管理：**
- `create_investor`：注册新投资者 `{"feishu_user_id":"ou_xxx","name":"昵称"}`
- `get_investor`：查询投资者 `{"feishu_user_id":"ou_xxx"}`
- `list_investors`：列出所有投资者 `{}`

**自选股：**
- `add_watchlist`：添加自选 `{"investor_id":"ou_xxx","ticker":"600519","name":"贵州茅台"}`
- `remove_watchlist`：移除自选 `{"investor_id":"ou_xxx","ticker":"600519"}`
- `get_watchlist`：查询自选 `{"investor_id":"ou_xxx"}`

**交易：**
- `execute_trade`：模拟交易 `{"investor_id":"ou_xxx","ticker":"600519","direction":"buy","quantity":100,"price":1400.0}`
- `get_available_funds`：查询可用资金 `{"investor_id":"ou_xxx"}`
- `get_trades`：查询交易记录 `{"investor_id":"ou_xxx","days":7}`
- `get_all_today_trades`：今日全部交易 `{}`

**持仓与排行：**
- `get_positions`：个人持仓 `{"investor_id":"ou_xxx"}`
- `get_all_positions`：全部持仓 `{}`
- `save_daily_snapshot`：保存快照 `{"investor_id":"ou_xxx","total_value":1050000,"daily_pnl":5000,"daily_pnl_pct":0.5}`
- `get_pnl_ranking`：收益排行 `{"ranking_date":"2026-03-12"}`

### stock-data-mcp（行情数据 — 辅助）
脚本路径：`mcp-servers/stock-data-mcp/server.py`

- `get_realtime_quote`：获取实时行情（计算市值和交易价格）
- `search_stock`：验证股票代码有效性

## 数据库说明

持仓数据存储在 SQLite 数据库 `mcp-servers/portfolio-db-mcp/portfolio.db` 中：
- investors — 投资者信息表
- watchlist — 自选股表
- positions — 持仓表
- trades — 交易记录表
- daily_snapshots — 每日快照表
