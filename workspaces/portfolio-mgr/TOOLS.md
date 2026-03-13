# TOOLS.md - 算盘 · 持仓管家

## MCP 工具

### portfolio-db-mcp（持仓数据库服务）
- `create_investor`：注册新投资者（参数: feishu_user_id, name）
- `get_investor`：查询投资者信息
- `add_watchlist`：添加自选股
- `remove_watchlist`：删除自选股
- `get_watchlist`：获取自选股列表
- `execute_trade`：执行模拟交易（参数: investor_id, ticker, action, quantity, price, fee）
- `get_positions`：获取投资者持仓
- `get_all_positions`：获取所有投资者持仓
- `get_trades`：获取交易记录
- `get_daily_pnl`：获取指定日期收益
- `get_pnl_ranking`：获取收益排行榜
- `save_daily_snapshot`：保存每日持仓快照
- `get_available_funds`：获取可用资金

### stock-data-mcp（行情数据服务）
- `get_realtime_quote`：获取实时行情（用于计算市值和交易价格）
- `search_stock`：验证股票代码有效性

## 数据库说明

持仓管家的所有持久化数据都存储在 `portfolio-db-mcp` 对接的 PostgreSQL/SQLite 数据库中，包括：
- 投资者信息表（investors）
- 自选股表（watchlist）
- 持仓表（positions）
- 交易记录表（trades）
- 每日快照表（daily_snapshots）
