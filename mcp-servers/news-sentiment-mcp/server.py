"""
news-sentiment-mcp: A股舆情与新闻数据 MCP Server
基于 AKShare 和东方财富数据，提供个股新闻、政策新闻、市场情绪指标等。
"""

from fastmcp import FastMCP
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import time

mcp = FastMCP(name="news-sentiment-mcp")

_spot_cache = {"data": None, "ts": 0}
SPOT_CACHE_TTL = 30


def _get_spot_df() -> pd.DataFrame:
    now = time.time()
    if _spot_cache["data"] is not None and now - _spot_cache["ts"] < SPOT_CACHE_TTL:
        return _spot_cache["data"]
    df = ak.stock_zh_a_spot_em()
    _spot_cache["data"] = df
    _spot_cache["ts"] = now
    return df


def _safe_str(val) -> str:
    if pd.isna(val):
        return ""
    return str(val)


def _safe_float(val) -> Optional[float]:
    try:
        if pd.isna(val):
            return None
        return round(float(val), 4)
    except (ValueError, TypeError):
        return None


def _normalize_ticker(ticker: str) -> str:
    t = ticker.strip().upper()
    for suffix in (".SH", ".SZ", ".BJ"):
        t = t.replace(suffix, "")
    for prefix in ("SH", "SZ", "BJ"):
        if t.startswith(prefix) and len(t) == 8:
            t = t[2:]
    return t


@mcp.tool
def get_stock_news(ticker: str, count: int = 20) -> list[dict]:
    """
    获取A股个股相关新闻资讯。
    ticker: 股票代码（如 600519 或 600519.SH）
    count: 返回新闻条数，默认20
    """
    code = _normalize_ticker(ticker)
    try:
        df = ak.stock_news_em(symbol=code)
        if df is None or df.empty:
            return [{"message": f"未找到 {ticker} 的新闻"}]
        results = []
        for _, row in df.head(count).iterrows():
            results.append({
                "title": _safe_str(row.get("新闻标题")),
                "content": _safe_str(row.get("新闻内容", ""))[:500],
                "source": _safe_str(row.get("文章来源")),
                "publish_time": _safe_str(row.get("发布时间")),
                "url": _safe_str(row.get("新闻链接")),
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool
def get_policy_news(category: str = "宏观经济") -> list[dict]:
    """
    获取财经政策新闻。
    category: 新闻分类，可选 宏观经济/产业政策/金融监管 等
    """
    try:
        df = ak.news_cctv(date=datetime.now().strftime("%Y%m%d"))
        if df is None or df.empty:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            df = ak.news_cctv(date=yesterday)

        if df is None or df.empty:
            return [{"message": "暂无政策新闻"}]

        results = []
        for _, row in df.head(15).iterrows():
            results.append({
                "title": _safe_str(row.get("title")),
                "content": _safe_str(row.get("content", ""))[:500],
                "date": _safe_str(row.get("date")),
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool
def get_market_sentiment() -> dict:
    """
    获取A股市场整体情绪指标：涨跌家数、涨停跌停、成交额等。
    """
    try:
        try:
            df = _get_spot_df()
            total = len(df)
            up_count = len(df[df["涨跌幅"] > 0])
            down_count = len(df[df["涨跌幅"] < 0])
            flat_count = total - up_count - down_count
            limit_up = len(df[df["涨跌幅"] >= 9.9])
            limit_down = len(df[df["涨跌幅"] <= -9.9])
            total_amount = df["成交额"].sum() if "成交额" in df.columns else 0

            avg_change = _safe_float(df["涨跌幅"].mean())
            median_change = _safe_float(df["涨跌幅"].median())

            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_stocks": total,
                "up_count": up_count,
                "down_count": down_count,
                "flat_count": flat_count,
                "limit_up_count": limit_up,
                "limit_down_count": limit_down,
                "total_amount_billion": round(float(total_amount) / 1e8, 2) if total_amount else 0,
                "avg_change_pct": avg_change,
                "median_change_pct": median_change,
                "market_temp": (
                    "极热" if limit_up > 80 else
                    "偏热" if limit_up > 40 else
                    "正常" if limit_up > 10 else
                    "偏冷" if limit_down < 20 else
                    "极冷"
                ),
                "up_down_ratio": round(up_count / max(down_count, 1), 2),
            }
        except Exception:
            pass

        df = ak.stock_board_industry_summary_ths()
        total_up = int(df["上涨家数"].sum())
        total_down = int(df["下跌家数"].sum())
        total_stocks = total_up + total_down
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "source": "同花顺行业板块汇总",
            "total_sectors": len(df),
            "up_count": total_up,
            "down_count": total_down,
            "up_down_ratio": round(total_up / max(total_down, 1), 2),
            "top_sectors": [
                {"name": _safe_str(r.get("板块")), "change_pct": _safe_float(r.get("涨跌幅"))}
                for _, r in df.head(5).iterrows()
            ],
            "bottom_sectors": [
                {"name": _safe_str(r.get("板块")), "change_pct": _safe_float(r.get("涨跌幅"))}
                for _, r in df.tail(5).iterrows()
            ],
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def check_sentiment_change(tickers: str, hours: int = 4) -> dict:
    """
    检测股票列表的舆情变化（新闻异动检测）。
    tickers: 逗号分隔的股票代码列表，如 "600519,002594,000858"
    hours: 检查最近N小时的新闻
    """
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
    cutoff = datetime.now() - timedelta(hours=hours)
    changes = []
    no_change = []

    for ticker in ticker_list:
        code = _normalize_ticker(ticker)
        try:
            df = ak.stock_news_em(symbol=code)
            if df is None or df.empty:
                no_change.append(code)
                continue

            recent_news = []
            for _, row in df.iterrows():
                pub_time_str = _safe_str(row.get("发布时间"))
                if not pub_time_str:
                    continue
                try:
                    pub_time = pd.to_datetime(pub_time_str)
                    if pub_time >= cutoff:
                        recent_news.append({
                            "title": _safe_str(row.get("新闻标题")),
                            "source": _safe_str(row.get("文章来源")),
                            "time": pub_time_str,
                        })
                except (ValueError, TypeError):
                    continue

            if recent_news:
                change_type = _classify_news([n["title"] for n in recent_news])
                changes.append({
                    "ticker": code,
                    "change_type": change_type,
                    "news_count": len(recent_news),
                    "latest_news": recent_news[:3],
                    "impact": _assess_impact(change_type),
                })
            else:
                no_change.append(code)
        except Exception:
            no_change.append(code)

    return {
        "checked_at": datetime.now().isoformat(),
        "hours_window": hours,
        "changes": changes,
        "no_change": no_change,
    }


def _classify_news(titles: list[str]) -> str:
    """简单的新闻分类。"""
    text = " ".join(titles)
    keywords = {
        "财报发布": ["财报", "年报", "季报", "半年报", "业绩", "营收", "净利润", "预告", "快报"],
        "重大合同": ["中标", "合同", "订单", "签约"],
        "高管变动": ["辞职", "任命", "高管", "董事", "总经理", "董事长"],
        "监管处罚": ["处罚", "立案", "调查", "违规", "罚款", "警示"],
        "减持增持": ["减持", "增持", "回购", "质押"],
        "并购重组": ["并购", "重组", "收购", "资产注入", "借壳"],
        "政策相关": ["政策", "补贴", "规划", "集采", "反垄断"],
        "评级变化": ["评级", "研报", "目标价", "上调", "下调"],
    }
    for category, words in keywords.items():
        if any(w in text for w in words):
            return category
    return "一般新闻"


def _assess_impact(change_type: str) -> str:
    """评估新闻变化的影响方向。"""
    positive = {"重大合同", "评级变化"}
    negative = {"监管处罚"}
    mixed = {"财报发布", "高管变动", "减持增持", "并购重组", "政策相关"}
    if change_type in positive:
        return "偏正面"
    elif change_type in negative:
        return "偏负面"
    elif change_type in mixed:
        return "需进一步分析"
    return "中性"


@mcp.tool
def get_financial_news(count: int = 20) -> list[dict]:
    """获取最新财经要闻（来源：财新网）。"""
    try:
        df = ak.stock_news_main_cx()
        if df is None or df.empty:
            return [{"message": "暂无财经要闻"}]
        results = []
        for _, row in df.head(count).iterrows():
            results.append({
                "tag": _safe_str(row.get("tag")),
                "title": _safe_str(row.get("summary")),
                "url": _safe_str(row.get("url")),
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool
def get_stock_rank_hot(count: int = 20) -> list[dict]:
    """获取东方财富人气榜（股票热度排名）。"""
    try:
        df = ak.stock_hot_rank_em()
        if df is None or df.empty:
            return [{"message": "暂无人气榜数据"}]
        return [
            {
                "rank": int(i + 1),
                "code": _safe_str(row.get("代码")),
                "name": _safe_str(row.get("股票名称")),
                "price": _safe_float(row.get("最新价")),
                "change_pct": _safe_float(row.get("涨跌幅")),
                "rank_change": _safe_str(row.get("排名变化")),
            }
            for i, (_, row) in enumerate(df.head(count).iterrows())
        ]
    except Exception as e:
        return [{"error": str(e)}]


_TOOLS = {
    "get_stock_news": get_stock_news,
    "get_policy_news": get_policy_news,
    "get_market_sentiment": get_market_sentiment,
    "check_sentiment_change": check_sentiment_change,
    "get_financial_news": get_financial_news,
    "get_stock_rank_hot": get_stock_rank_hot,
}

if __name__ == "__main__":
    import sys, json as _json
    if len(sys.argv) >= 3 and sys.argv[1] == "call":
        tool_name = sys.argv[2]
        args = _json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        if tool_name == "list":
            print(_json.dumps(list(_TOOLS.keys()), ensure_ascii=False))
        elif tool_name in _TOOLS:
            result = _TOOLS[tool_name](**args)
            print(_json.dumps(result, ensure_ascii=False, default=str))
        else:
            print(_json.dumps({"error": f"Unknown tool: {tool_name}"}))
    else:
        mcp.run()
