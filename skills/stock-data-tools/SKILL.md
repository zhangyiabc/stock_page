---
name: stock-data-tools
description: A股行情数据工具 — 通过 exec 调用 stock-data-mcp 获取实时行情、K线、财报、板块资金流向等数据
metadata: {"openclaw":{"requires":{"bins":["python"]}}}
---

# A 股行情数据工具

通过 `exec` 调用 `{baseDir}/../../mcp-servers/stock-data-mcp/server.py` 获取 A 股数据。

## 调用格式

```bash
python {baseDir}/../../mcp-servers/stock-data-mcp/server.py call <tool_name> '<json_args>'
```

返回值为 JSON，直接解析使用。所有调用自动记录日志：
- `mcp-servers/logs/calls.log` — 摘要日志（单行，含时间、工具名、耗时、状态）
- `mcp-servers/logs/calls_detail.jsonl` — 详细日志（完整 JSON，不截断，含完整参数和返回结果）

## 可用工具

### search_stock — 搜索股票
参数: `{"keyword": "关键词"}`
```bash
python {baseDir}/../../mcp-servers/stock-data-mcp/server.py call search_stock '{"keyword":"贵州茅台"}'
```
返回: `[{"ticker":"600519.SH","code":"600519","name":"贵州茅台","price":1400.0,"change_pct":0.5}]`

### get_realtime_quote — 获取实时行情
参数: `{"ticker": "股票代码"}`
```bash
python {baseDir}/../../mcp-servers/stock-data-mcp/server.py call get_realtime_quote '{"ticker":"600519"}'
```
返回包含: price, change, change_pct, open, high, low, volume, amount, turnover_rate, pe_ttm, pb, total_market_cap 等

### get_kline — 获取K线数据
参数: `{"ticker": "代码", "period": "daily|weekly|monthly", "count": 120, "adjust": "qfq|hfq|"}`
```bash
python {baseDir}/../../mcp-servers/stock-data-mcp/server.py call get_kline '{"ticker":"600519","period":"daily","count":60}'
```
返回 OHLCV 列表，用于技术面分析

### get_financial_report — 获取财务数据
参数: `{"ticker": "代码", "report_type": "利润表|资产负债表|现金流量表"}`
```bash
python {baseDir}/../../mcp-servers/stock-data-mcp/server.py call get_financial_report '{"ticker":"600519","report_type":"利润表"}'
```

### get_individual_info — 获取个股基本信息
参数: `{"ticker": "代码"}`
```bash
python {baseDir}/../../mcp-servers/stock-data-mcp/server.py call get_individual_info '{"ticker":"600519"}'
```
返回: 股票简称、总市值、流通市值、行业、上市日期等

### get_sector_flow — 获取板块资金流向
参数: `{"count": 10}` (可选)
```bash
python {baseDir}/../../mcp-servers/stock-data-mcp/server.py call get_sector_flow '{"count":10}'
```

### get_top_list — 获取龙虎榜数据
参数: `{"days": 5}` (可选)
```bash
python {baseDir}/../../mcp-servers/stock-data-mcp/server.py call get_top_list '{"days":5}'
```

### get_index_quote — 获取大盘指数
参数: `{"index_code": "000001|399001|399006"}` (上证/深证/创业板)
```bash
python {baseDir}/../../mcp-servers/stock-data-mcp/server.py call get_index_quote '{"index_code":"000001"}'
```

### get_stock_comments — 获取千股千评
参数: `{"ticker": "代码"}`
```bash
python {baseDir}/../../mcp-servers/stock-data-mcp/server.py call get_stock_comments '{"ticker":"600519"}'
```

### get_north_flow — 获取北向资金流向
无参数:
```bash
python {baseDir}/../../mcp-servers/stock-data-mcp/server.py call get_north_flow '{}'
```

## 注意事项
- 所有股票代码支持纯数字（600519）或带后缀（600519.SH）格式
- 数据源有三级降级：东方财富 → 腾讯财经 → 本地CSV，可用性有保障
- 返回 JSON 中若有 `error` 字段表示调用失败
