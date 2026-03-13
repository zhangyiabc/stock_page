# Yahoo Finance CLI（雅虎财经数据工具）

> 整合自 [gracefullight/stock-checker@yahoo-finance](https://skills.sh/gracefullight/stock-checker/yahoo-finance)。用于补充获取海外市场数据和全球宏观指标。

基于 Python + yfinance 的命令行工具，用于获取全面的股票数据。

## 前置依赖

- uv（Python 包管理器）
- Python 3.11+

## 安装 uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 可用命令

| 命令 | 用途 | 示例 |
|------|------|------|
| `yf price {symbol}` | 快速价格查询 | `yf price AAPL` |
| `yf quote {symbol}` | 详细报价 | `yf quote MSFT` |
| `yf fundamentals {symbol}` | 基本面数据 | `yf fundamentals NVDA` |
| `yf earnings {symbol}` | 财报日期和历史 | `yf earnings TSLA` |
| `yf profile {symbol}` | 公司概况 | `yf profile GOOGL` |
| `yf dividends {symbol}` | 分红信息 | `yf dividends KO` |
| `yf ratings {symbol}` | 分析师评级 | `yf ratings AAPL` |
| `yf history {symbol} {period}` | 历史行情 | `yf history GOOGL 1y` |
| `yf compare {symbols}` | 多股对比 | `yf compare AAPL,MSFT` |
| `yf search {keyword}` | 搜索股票 | `yf search "reliance"` |

## A 股使用说明

A 股数据主要通过 `stock-data-mcp`（基于 AKShare）获取。Yahoo Finance 作为补充数据源：

- **全球指数对比**：`yf price ^GSPC`（标普500）、`yf price ^HSI`（恒生指数）
- **港股数据**：`yf price 0700.HK`（腾讯控股）
- **汇率查询**：`yf price USDCNY=X`（美元兑人民币）
- **大宗商品**：`yf price GC=F`（黄金）、`yf price CL=F`（原油）
- **全球 ETF**：`yf compare SPY,QQQ,EWJ`

## 使用场景

1. **地缘政治分析**中获取全球市场联动数据
2. **宏观分析**中查询汇率和大宗商品价格
3. **行业对比**中参考海外同行估值
