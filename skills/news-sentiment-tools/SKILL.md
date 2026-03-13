---
name: news-sentiment-tools
description: A股舆情与新闻工具 — 通过 exec 调用 news-sentiment-mcp 获取个股新闻、政策新闻、市场情绪等数据
metadata: {"openclaw":{"requires":{"bins":["python"]}}}
---

# A 股舆情与新闻工具

通过 `exec` 调用 `{baseDir}/../../mcp-servers/news-sentiment-mcp/server.py` 获取舆情数据。

## 调用格式

```bash
python {baseDir}/../../mcp-servers/news-sentiment-mcp/server.py call <tool_name> '<json_args>'
```

## 可用工具

### get_stock_news — 获取个股新闻
参数: `{"ticker": "代码", "count": 20}`
```bash
python {baseDir}/../../mcp-servers/news-sentiment-mcp/server.py call get_stock_news '{"ticker":"600519","count":10}'
```
返回: `[{"title":"...","content":"...","datetime":"...","source":"..."}]`

### get_policy_news — 获取宏观政策新闻
参数: `{"category": "宏观经济"}` (可选)
```bash
python {baseDir}/../../mcp-servers/news-sentiment-mcp/server.py call get_policy_news '{"category":"宏观经济"}'
```

### get_market_sentiment — 获取市场整体情绪指标
无参数:
```bash
python {baseDir}/../../mcp-servers/news-sentiment-mcp/server.py call get_market_sentiment '{}'
```
返回: 涨跌家数、涨停跌停数、平均涨跌幅、成交量等

### check_sentiment_change — 检测舆情变化
参数: `{"tickers": "600519,002594", "hours": 4}`
多只股票用逗号分隔。
```bash
python {baseDir}/../../mcp-servers/news-sentiment-mcp/server.py call check_sentiment_change '{"tickers":"600519,002594","hours":4}'
```
返回每只股票的舆情变化情况（正面/负面/中性比例变化）

### get_financial_news — 获取财经要闻
参数: `{"count": 20}` (可选)
```bash
python {baseDir}/../../mcp-servers/news-sentiment-mcp/server.py call get_financial_news '{"count":15}'
```

### get_stock_rank_hot — 获取热门股票排行
参数: `{"count": 20}` (可选)
```bash
python {baseDir}/../../mcp-servers/news-sentiment-mcp/server.py call get_stock_rank_hot '{"count":20}'
```

## 注意事项
- 舆情检查用于心跳监控流程，对比历史基线识别异常
- 返回 JSON 中若有 `error` 字段表示调用失败
