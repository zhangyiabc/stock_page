# TOOLS.md - 朝闻 · 研究员

## 数据工具（通过 exec 调用）

所有数据工具通过 `exec` 命令调用 Python 脚本。调用格式：
```bash
python <script_path> call <tool_name> '<json_args>'
```

### stock-data-mcp（行情数据）
脚本路径：`mcp-servers/stock-data-mcp/server.py`

- `search_stock`：通过名称/代码搜索股票 `{"keyword":"茅台"}`
- `get_realtime_quote`：获取个股实时行情 `{"ticker":"600519"}`
- `get_kline`：获取 K 线数据 `{"ticker":"600519","period":"daily","count":120}`
- `get_financial_report`：获取财报数据 `{"ticker":"600519","report_type":"利润表"}`
- `get_individual_info`：获取个股基本信息 `{"ticker":"600519"}`
- `get_sector_flow`：获取板块资金流向 `{"count":10}`
- `get_top_list`：获取龙虎榜 `{"days":5}`
- `get_index_quote`：获取大盘指数 `{"index_code":"000001"}`
- `get_stock_comments`：获取千股千评 `{"ticker":"600519"}`
- `get_north_flow`：获取北向资金 `{}`

### news-sentiment-mcp（舆情数据）
脚本路径：`mcp-servers/news-sentiment-mcp/server.py`

- `get_stock_news`：获取个股新闻 `{"ticker":"600519","count":20}`
- `get_policy_news`：获取宏观政策新闻 `{"category":"宏观经济"}`
- `get_market_sentiment`：获取市场情绪指标 `{}`
- `check_sentiment_change`：检测舆情变化 `{"tickers":"600519,002594","hours":4}`
- `get_financial_news`：获取财经要闻 `{"count":15}`
- `get_stock_rank_hot`：获取热门股排行 `{"count":20}`

## 技术指标计算

基于 K 线数据在分析过程中计算：
- 均线系统（MA5/10/20/60/120/250）
- MACD、RSI、KDJ、布林带

## 数据源说明

- 行情数据：AKShare/东方财富 → 腾讯财经 → 本地 CSV（三级降级）
- 新闻数据：东方财富/财新网
- 数据更新频率：实时行情约 15 分钟延迟，新闻实时
