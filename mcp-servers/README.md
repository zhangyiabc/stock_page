# MCP Servers - A股投资分析系统

3 个 MCP Server，为 OpenClaw Agent 提供 A 股数据、舆情分析和持仓管理能力。

## 架构

```
Agent (OpenClaw)
  │
  ├── stock-data-mcp      ← AKShare: 行情/K线/财报/资金流向
  ├── news-sentiment-mcp   ← AKShare: 新闻/舆情/市场情绪
  └── portfolio-db-mcp     ← SQLite: 投资者/自选/持仓/交易
```

## 快速开始

### 1. 安装依赖

```bash
pip install fastmcp akshare pandas
```

### 2. 启动服务

每个 MCP Server 独立运行，使用 stdio 或 HTTP 传输：

```bash
# stdio 模式（OpenClaw 默认）
python mcp-servers/stock-data-mcp/server.py
python mcp-servers/news-sentiment-mcp/server.py
python mcp-servers/portfolio-db-mcp/server.py

# HTTP 模式（调试用）
cd mcp-servers/stock-data-mcp && fastmcp run server.py:mcp --transport http --port 8001
cd mcp-servers/news-sentiment-mcp && fastmcp run server.py:mcp --transport http --port 8002
cd mcp-servers/portfolio-db-mcp && fastmcp run server.py:mcp --transport http --port 8003
```

### 3. 使用 MCP Inspector 调试

```bash
npx @modelcontextprotocol/inspector python mcp-servers/stock-data-mcp/server.py
```

## 各 Server 工具清单

### stock-data-mcp (10 个工具)

| 工具 | 参数 | 说明 |
|------|------|------|
| `search_stock` | keyword | 搜索股票（名称/代码） |
| `get_realtime_quote` | ticker | 实时行情（价格/涨跌/市值/PE/PB） |
| `get_kline` | ticker, period, count, adjust | K线数据（日/周/月，前复权） |
| `get_financial_report` | ticker | 核心财务指标（近4期） |
| `get_individual_info` | ticker | 个股基本信息（行业/上市日等） |
| `get_sector_flow` | — | 行业板块资金流向排名 |
| `get_top_list` | date | 龙虎榜数据 |
| `get_index_quote` | index_code | 大盘指数行情 |
| `get_stock_comments` | ticker | 千股千评（综合评分） |
| `get_north_flow` | — | 北向资金实时流向 |

### news-sentiment-mcp (6 个工具)

| 工具 | 参数 | 说明 |
|------|------|------|
| `get_stock_news` | ticker, count | 个股新闻资讯 |
| `get_policy_news` | category | 宏观政策新闻（央视新闻联播） |
| `get_market_sentiment` | — | 市场情绪指标（涨跌家数/涨停数/成交额） |
| `check_sentiment_change` | tickers, hours | 批量舆情变化检测 |
| `get_financial_news` | count | 最新财经要闻 |
| `get_stock_rank_hot` | count | 东方财富人气榜 |

### portfolio-db-mcp (12 个工具)

| 工具 | 参数 | 说明 |
|------|------|------|
| `create_investor` | feishu_user_id, name | 注册投资者 |
| `get_investor` | feishu_user_id | 查询投资者信息 |
| `add_watchlist` | investor_id, ticker, name | 添加自选 |
| `remove_watchlist` | investor_id, ticker | 删除自选 |
| `get_watchlist` | investor_id | 获取自选列表 |
| `execute_trade` | investor_id, ticker, name, action, quantity, price, fee, reason | 执行模拟交易 |
| `get_positions` | investor_id | 获取持仓明细 |
| `get_all_positions` | — | 全体投资者持仓汇总 |
| `get_trades` | investor_id, days | 交易记录查询 |
| `get_all_today_trades` | — | 所有今日交易 |
| `save_daily_snapshot` | investor_id, total_value, ... | 保存每日快照 |
| `get_pnl_ranking` | ranking_date | 收益排行榜 |
| `get_available_funds` | investor_id | 查询可用资金 |
| `list_investors` | — | 列出所有投资者 |

## 数据源

- **行情数据**: [AKShare](https://akshare.akfamily.xyz/) — 免费开源，覆盖 A 股全量数据
- **新闻数据**: 东方财富/央视新闻（通过 AKShare 封装）
- **持仓数据**: SQLite 本地数据库（`portfolio-db-mcp/portfolio.db`）
