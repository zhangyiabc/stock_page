# TOOLS.md - 朝闻 · 研究员

## MCP 工具

### stock-data-mcp（行情数据服务）
- `get_realtime_quote`：获取个股实时行情（价格、涨跌幅、成交量）
- `get_kline`：获取 K 线数据（日K/周K/月K）
- `get_financial_report`：获取上市公司财报数据
- `get_sector_flow`：获取板块资金流向
- `get_top_list`：获取龙虎榜数据
- `search_stock`：通过名称/代码搜索股票
- `get_index_quote`：获取大盘指数行情

### news-sentiment-mcp（舆情数据服务）
- `get_stock_news`：获取个股相关新闻
- `get_policy_news`：获取宏观政策新闻
- `get_market_sentiment`：获取市场情绪指标
- `check_sentiment_change`：检测股票列表的舆情变化

## 技术指标计算 Skill

位于 `skills/technical-indicators/`：
- 均线计算（MA）
- MACD 计算
- RSI 计算
- KDJ 计算
- 布林带计算

## 数据源说明

- 行情数据来源：AKShare（通过 stock-data-mcp 封装）
- 新闻数据来源：东方财富/新浪财经（通过 news-sentiment-mcp 封装）
- 数据更新频率：实时行情约 15 分钟延迟，新闻实时
