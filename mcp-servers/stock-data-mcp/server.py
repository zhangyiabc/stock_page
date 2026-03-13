"""
stock-data-mcp: A股行情数据 MCP Server
基于 AKShare 提供实时行情、K线、财报、板块资金流向、龙虎榜等数据。
"""

from fastmcp import FastMCP
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
import time
import json as _json
import urllib.request
import re

mcp = FastMCP(name="stock-data-mcp")

_LOCAL_CODES_CSV = Path(__file__).parent / "stock_codes.csv"
_local_codes_df: Optional[pd.DataFrame] = None


def _get_local_codes() -> pd.DataFrame:
    """加载本地股票代码表（5400+ A股），启动时读一次后常驻内存。"""
    global _local_codes_df
    if _local_codes_df is not None:
        return _local_codes_df
    if _LOCAL_CODES_CSV.exists():
        df = pd.read_csv(_LOCAL_CODES_CSV, dtype=str)
        df.columns = ["code", "name"]
        df["code"] = df["code"].str.strip()
        df["name"] = df["name"].str.replace(r"\s+", "", regex=True)
        _local_codes_df = df
        return df
    return pd.DataFrame(columns=["code", "name"])


_spot_cache = {"data": None, "ts": 0}
SPOT_CACHE_TTL = 30


def _retry(fn, max_retries=3, delay=2.0):
    """带重试的 AKShare 调用，应对东方财富限频。"""
    last_err = None
    for i in range(max_retries):
        try:
            return fn()
        except Exception as e:
            last_err = e
            if i < max_retries - 1:
                time.sleep(delay * (i + 1))
    raise last_err


def _get_spot_df() -> pd.DataFrame:
    """缓存实时行情数据，30秒内复用，减少东方财富限频。"""
    now = time.time()
    if _spot_cache["data"] is not None and now - _spot_cache["ts"] < SPOT_CACHE_TTL:
        return _spot_cache["data"]
    df = _retry(ak.stock_zh_a_spot_em)
    _spot_cache["data"] = df
    _spot_cache["ts"] = now
    return df


def _tencent_quote(code: str) -> Optional[dict]:
    """通过腾讯财经接口获取实时行情，作为东方财富接口的高可用备选。"""
    prefix = "sh" if code.startswith(("6", "9")) else "sz"
    if code.startswith(("8", "4", "92")):
        prefix = "bj"
    url = f"https://qt.gtimg.cn/q={prefix}{code}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read().decode("gbk", errors="ignore")
        m = re.search(r'"(.+)"', raw)
        if not m:
            return None
        parts = m.group(1).split("~")
        if len(parts) < 50:
            return None
        def fv(idx):
            try:
                return round(float(parts[idx]), 4) if parts[idx] else None
            except (ValueError, IndexError):
                return None
        return {
            "ticker": code + _market_suffix(code),
            "code": code,
            "name": parts[1],
            "price": fv(3),
            "prev_close": fv(4),
            "open": fv(5),
            "volume": int(float(parts[6]) * 100) if parts[6] else None,  # 手→股
            "change": fv(31),
            "change_pct": fv(32),
            "high": fv(33),
            "low": fv(34),
            "amount": fv(37),  # 万元
            "turnover_rate": fv(38),
            "pe_ttm": fv(39),
            "amplitude": fv(43),
            "circulating_market_cap": fv(44),  # 流通市值(亿)
            "total_market_cap": fv(45),  # 总市值(亿)
            "pb": fv(46),
            "source": "tencent",
        }
    except Exception:
        return None


def _tencent_batch_quote(codes: list[str]) -> dict[str, dict]:
    """批量查询腾讯行情，返回 {code: quote_dict}。"""
    if not codes:
        return {}
    symbols = []
    for c in codes:
        prefix = "sh" if c.startswith(("6", "9")) else "sz"
        if c.startswith(("8", "4", "92")):
            prefix = "bj"
        symbols.append(f"{prefix}{c}")
    url = f"https://qt.gtimg.cn/q={','.join(symbols)}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("gbk", errors="ignore")
        result = {}
        for m in re.finditer(r'v_(\w+)="(.+?)"', raw):
            parts = m.group(2).split("~")
            if len(parts) < 50:
                continue
            code = parts[2]
            def fv(idx, _parts=parts):
                try:
                    return round(float(_parts[idx]), 4) if _parts[idx] else None
                except (ValueError, IndexError):
                    return None
            result[code] = {
                "code": code,
                "name": parts[1],
                "price": fv(3),
                "change_pct": fv(32),
                "volume": int(float(parts[6]) * 100) if parts[6] else None,
                "amount": fv(37),
                "turnover_rate": fv(38),
            }
        return result
    except Exception:
        return {}


def _em_secid(code: str) -> str:
    """将纯数字股票代码转为东方财富 push2 的 secid 格式（market.code）。"""
    if code.startswith("6") or code.startswith("9"):
        return f"1.{code}"
    elif code.startswith("4") or code.startswith("8"):
        return f"0.{code}"
    return f"0.{code}"


_EM_PUSH_FIELDS = "f12,f13,f14,f2,f4,f18,f3,f5,f6,f8,f7,f10,f9,f100,f22,f30,f31,f32"


def _em_push_quote(codes: list[str]) -> dict[str, dict]:
    """通过东方财富 push2 接口批量获取实时行情，毫秒级响应。返回 {code: quote_dict}。"""
    if not codes:
        return {}
    secids = ",".join(_em_secid(c) for c in codes)
    url = f"https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&fields={_EM_PUSH_FIELDS}&secids={secids}"
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        if data.get("rc") != 0 or not data.get("data"):
            return {}
        result = {}
        for item in data["data"].get("diff", []):
            code = str(item.get("f12", ""))
            if not code:
                continue
            def fv(val):
                try:
                    if val == "-" or val is None:
                        return None
                    return round(float(val), 4)
                except (ValueError, TypeError):
                    return None
            market = item.get("f13", 0)
            result[code] = {
                "ticker": code + (".SH" if market == 1 else ".SZ"),
                "code": code,
                "name": str(item.get("f14", "")).replace(" ", ""),
                "price": fv(item.get("f2")),
                "prev_close": fv(item.get("f18")),
                "change": fv(item.get("f4")),
                "change_pct": fv(item.get("f3")),
                "volume": int(item["f5"]) * 100 if item.get("f5") and item["f5"] != "-" else None,
                "amount": fv(item.get("f6")),
                "amplitude": fv(item.get("f7")),
                "turnover_rate": fv(item.get("f8")),
                "pe_ttm": fv(item.get("f9")),
                "volume_ratio": fv(item.get("f10")),
                "industry": str(item.get("f100", "")),
                "source": "eastmoney_push",
            }
        return result
    except Exception:
        return {}


_EM_SEARCH_TOKEN = "D43BF722C8E33BDC906FB84D85E326E8"


def _em_search(keyword: str, count: int = 10) -> list[dict]:
    """通过东方财富搜索接口按关键词搜索 A 股。"""
    url = (
        f"https://searchapi.eastmoney.com/api/suggest/get"
        f"?input={urllib.request.quote(keyword)}&type=14"
        f"&token={_EM_SEARCH_TOKEN}&count={count}"
    )
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        items = data.get("QuotationCodeTable", {}).get("Data") or []
        results = []
        for it in items:
            sec_type = it.get("SecurityTypeName", "")
            if "A" not in sec_type and "科创" not in sec_type and "创业" not in sec_type:
                continue
            results.append({
                "code": it["Code"],
                "name": it["Name"],
                "secid": it.get("QuoteID", ""),
                "market": it.get("MktNum", ""),
            })
        return results
    except Exception:
        return []


def _safe_float(val) -> Optional[float]:
    try:
        if pd.isna(val):
            return None
        return round(float(val), 4)
    except (ValueError, TypeError):
        return None


def _safe_str(val) -> str:
    if pd.isna(val):
        return ""
    return str(val)


def _local_name(code: str) -> str:
    """从本地代码表查股票名称。"""
    df = _get_local_codes()
    if df.empty:
        return ""
    row = df[df["code"] == code]
    return row.iloc[0]["name"] if not row.empty else ""


def _normalize_ticker(ticker: str) -> str:
    """将 600519.SH / SH600519 / 600519 统一为纯数字代码。"""
    t = ticker.strip().upper()
    for suffix in (".SH", ".SZ", ".BJ"):
        t = t.replace(suffix, "")
    for prefix in ("SH", "SZ", "BJ"):
        if t.startswith(prefix) and len(t) == 8:
            t = t[2:]
    return t


def _market_suffix(code: str) -> str:
    if code.startswith("6"):
        return ".SH"
    elif code.startswith("0") or code.startswith("3"):
        return ".SZ"
    elif code.startswith("4") or code.startswith("8"):
        return ".BJ"
    return ".SZ"


@mcp.tool
def search_stock(keyword: str) -> list[dict]:
    """通过名称或代码关键词搜索A股股票，返回匹配的股票列表。
    数据源优先级：东方财富搜索+push2 → 本地代码表+push2 → 本地代码表+腾讯行情"""
    try:
        # 优先级1: 东方财富搜索接口 + push2 行情（毫秒级）
        em_results = _em_search(keyword)
        if em_results:
            codes = [r["code"] for r in em_results]
            quotes = _em_push_quote(codes)
            out = []
            for r in em_results:
                code = r["code"]
                q = quotes.get(code, {})
                out.append({
                    "ticker": code + _market_suffix(code),
                    "code": code,
                    "name": q.get("name") or r["name"],
                    "price": q.get("price"),
                    "change_pct": q.get("change_pct"),
                })
            return out

        # 优先级2: 本地代码表 + push2 行情
        df = _get_local_codes()
        if df.empty:
            return [{"error": "本地股票代码表为空，且在线接口不可用"}]
        mask = df["name"].str.contains(keyword, na=False) | df["code"].str.contains(keyword, na=False)
        results = df[mask].head(10)
        codes = [row["code"] for _, row in results.iterrows()]
        quotes = _em_push_quote(codes) if codes else {}
        if not quotes:
            quotes = _tencent_batch_quote(codes) if codes else {}
        out = []
        for _, row in results.iterrows():
            q = quotes.get(row["code"], {})
            out.append({
                "ticker": row["code"] + _market_suffix(row["code"]),
                "code": row["code"],
                "name": q.get("name") or row["name"],
                "price": q.get("price"),
                "change_pct": q.get("change_pct"),
            })
        return out
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool
def get_realtime_quote(ticker: str) -> dict:
    """获取A股个股实时行情，包括价格、涨跌幅、成交量、资金流向等。
    数据源优先级：东方财富push2 → 腾讯财经 → AKShare全量行情表。"""
    code = _normalize_ticker(ticker)
    ts = datetime.now().isoformat()
    try:
        # 优先级1: 东方财富 push2 接口（毫秒级，单股精准查询）
        quotes = _em_push_quote([code])
        if code in quotes:
            q = quotes[code]
            q["timestamp"] = ts
            return q

        # 优先级2: 腾讯财经接口
        tq = _tencent_quote(code)
        if tq and tq.get("price"):
            tq["timestamp"] = ts
            return tq

        # 优先级3: AKShare 全量行情表（较慢，兜底）
        df = _get_spot_df()
        row = df[df["代码"] == code]
        if not row.empty:
            r = row.iloc[0]
            return {
                "ticker": code + _market_suffix(code),
                "code": code,
                "name": _safe_str(r.get("名称")),
                "price": _safe_float(r.get("最新价")),
                "change": _safe_float(r.get("涨跌额")),
                "change_pct": _safe_float(r.get("涨跌幅")),
                "open": _safe_float(r.get("今开")),
                "high": _safe_float(r.get("最高")),
                "low": _safe_float(r.get("最低")),
                "prev_close": _safe_float(r.get("昨收")),
                "volume": _safe_float(r.get("成交量")),
                "amount": _safe_float(r.get("成交额")),
                "turnover_rate": _safe_float(r.get("换手率")),
                "pe_ttm": _safe_float(r.get("市盈率-动态")),
                "pb": _safe_float(r.get("市净率")),
                "total_market_cap": _safe_float(r.get("总市值")),
                "circulating_market_cap": _safe_float(r.get("流通市值")),
                "amplitude": _safe_float(r.get("振幅")),
                "volume_ratio": _safe_float(r.get("量比")),
                "source": "eastmoney_spot",
                "timestamp": ts,
            }

        return {"error": f"未找到股票 {code}", "code": code}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_kline(
    ticker: str,
    period: str = "daily",
    count: int = 120,
    adjust: str = "qfq",
) -> list[dict]:
    """
    获取A股K线数据。
    period: daily/weekly/monthly
    count: 返回的K线条数
    adjust: qfq(前复权)/hfq(后复权)/空字符串(不复权)
    """
    code = _normalize_ticker(ticker)
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=count * 2)).strftime("%Y%m%d")
    try:
        df = ak.stock_zh_a_hist(
            symbol=code,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )
        df = df.tail(count)
        return [
            {
                "date": _safe_str(row.get("日期")),
                "open": _safe_float(row.get("开盘")),
                "close": _safe_float(row.get("收盘")),
                "high": _safe_float(row.get("最高")),
                "low": _safe_float(row.get("最低")),
                "volume": _safe_float(row.get("成交量")),
                "amount": _safe_float(row.get("成交额")),
                "amplitude": _safe_float(row.get("振幅")),
                "change_pct": _safe_float(row.get("涨跌幅")),
                "change": _safe_float(row.get("涨跌额")),
                "turnover_rate": _safe_float(row.get("换手率")),
            }
            for _, row in df.iterrows()
        ]
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool
def get_financial_report(ticker: str) -> dict:
    """获取A股上市公司核心财务指标（近4期）。"""
    code = _normalize_ticker(ticker)
    try:
        df = _retry(lambda: ak.stock_financial_abstract_ths(symbol=code, indicator="按年度"))
        if df is None or df.empty:
            df = _retry(lambda: ak.stock_financial_analysis_indicator(symbol=code))

        if df is None or df.empty:
            return {"error": f"未找到 {ticker} 的财务数据"}

        records = []
        for _, row in df.head(4).iterrows():
            record = {}
            for col in df.columns:
                val = row[col]
                if isinstance(val, (int, float)):
                    record[col] = _safe_float(val)
                else:
                    record[col] = _safe_str(val)
            records.append(record)
        return {"ticker": code + _market_suffix(code), "periods": records}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_individual_info(ticker: str) -> dict:
    """获取A股个股的基本信息（行业、上市日期、总股本等）。"""
    code = _normalize_ticker(ticker)
    try:
        df = ak.stock_individual_info_em(symbol=code)
        info = {}
        for _, row in df.iterrows():
            info[_safe_str(row.iloc[0])] = _safe_str(row.iloc[1])
        return {"ticker": code + _market_suffix(code), "info": info}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_sector_flow() -> list[dict]:
    """获取A股行业板块涨跌幅排名（当日），含资金净流入和领涨股。"""
    try:
        try:
            df = _retry(lambda: ak.stock_sector_fund_flow_rank(indicator="今日"))
            return [
                {
                    "sector": _safe_str(row.get("名称")),
                    "change_pct": _safe_float(row.get("今日涨跌幅")),
                    "main_net_inflow": _safe_float(row.get("主力净流入-净额")),
                    "main_net_inflow_pct": _safe_float(row.get("主力净流入-净占比")),
                }
                for _, row in df.head(20).iterrows()
            ]
        except Exception:
            pass

        df = _retry(ak.stock_board_industry_summary_ths)
        return [
            {
                "sector": _safe_str(row.get("板块")),
                "change_pct": _safe_float(row.get("涨跌幅")),
                "net_inflow": _safe_float(row.get("净流入")),
                "total_volume": _safe_float(row.get("总成交量")),
                "total_amount": _safe_float(row.get("总成交额")),
                "up_count": _safe_float(row.get("上涨家数")),
                "down_count": _safe_float(row.get("下跌家数")),
                "leading_stock": _safe_str(row.get("领涨股")),
                "leading_stock_change": _safe_float(row.get("领涨股-涨跌幅")),
            }
            for _, row in df.head(20).iterrows()
        ]
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool
def get_top_list(date: str = "") -> list[dict]:
    """
    获取龙虎榜数据。
    date: YYYYMMDD格式，默认最近5个交易日。
    """
    try:
        if not date:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")
        else:
            start_date = date
            end_date = date

        df = _retry(lambda: ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date))
        if df is None or df.empty:
            return [{"message": f"{start_date}~{end_date} 无龙虎榜数据"}]
        return [
            {
                "code": _safe_str(row.get("代码")),
                "name": _safe_str(row.get("名称")),
                "date": _safe_str(row.get("上榜日")),
                "close": _safe_float(row.get("收盘价")),
                "change_pct": _safe_float(row.get("涨跌幅")),
                "reason": _safe_str(row.get("上榜原因")),
                "net_buy_amount": _safe_float(row.get("龙虎榜净买额")),
                "buy_amount": _safe_float(row.get("龙虎榜买入额")),
                "sell_amount": _safe_float(row.get("龙虎榜卖出额")),
                "turnover_rate": _safe_float(row.get("换手率")),
            }
            for _, row in df.head(30).iterrows()
        ]
    except Exception as e:
        return [{"error": str(e)}]


INDEX_SYMBOL_MAP = {
    "000001": "sh000001",
    "399001": "sz399001",
    "399006": "sz399006",
    "000300": "sh000300",
    "000016": "sh000016",
    "000905": "sh000905",
    "399005": "sz399005",
}
INDEX_NAME_MAP = {
    "000001": "上证指数",
    "399001": "深证成指",
    "399006": "创业板指",
    "000300": "沪深300",
    "000016": "上证50",
    "000905": "中证500",
    "399005": "中小100",
}


def _em_index_secid(index_code: str) -> str:
    """指数的 secid：上证系 1.xxx，深证系 0.xxx。"""
    if index_code.startswith("0"):
        return f"1.{index_code}"
    return f"0.{index_code}"


def _em_push_index_quote(index_code: str) -> Optional[dict]:
    """通过 push2 接口获取指数行情。"""
    secid = _em_index_secid(index_code)
    url = f"https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&fields=f12,f13,f14,f2,f4,f18,f3,f5,f6,f7,f8,f10&secids={secid}"
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        items = data.get("data", {}).get("diff", [])
        if not items:
            return None
        it = items[0]
        def fv(val):
            try:
                if val == "-" or val is None:
                    return None
                return round(float(val), 4)
            except (ValueError, TypeError):
                return None
        return {
            "code": str(it.get("f12", "")),
            "name": str(it.get("f14", "")).replace(" ", ""),
            "price": fv(it.get("f2")),
            "prev_close": fv(it.get("f18")),
            "change": fv(it.get("f4")),
            "change_pct": fv(it.get("f3")),
            "volume": int(it["f5"]) * 100 if it.get("f5") and it["f5"] != "-" else None,
            "amount": fv(it.get("f6")),
            "amplitude": fv(it.get("f7")),
            "source": "eastmoney_push",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception:
        return None


@mcp.tool
def get_index_quote(index_code: str = "000001") -> dict:
    """
    获取大盘指数实时行情。
    常用指数代码: 000001(上证指数) 399001(深证成指) 399006(创业板指) 000300(沪深300)
    数据源优先级：东方财富push2 → AKShare指数行情 → AKShare历史日线。
    """
    try:
        # 优先级1: push2 接口（毫秒级）
        result = _em_push_index_quote(index_code)
        if result and result.get("price"):
            return result

        # 优先级2: AKShare 指数行情表
        try:
            df = _retry(ak.stock_zh_index_spot_em)
            row = df[df["代码"] == index_code]
            if not row.empty:
                r = row.iloc[0]
                return {
                    "code": _safe_str(r.get("代码")),
                    "name": _safe_str(r.get("名称")),
                    "price": _safe_float(r.get("最新价")),
                    "change": _safe_float(r.get("涨跌额")),
                    "change_pct": _safe_float(r.get("涨跌幅")),
                    "open": _safe_float(r.get("今开")),
                    "high": _safe_float(r.get("最高")),
                    "low": _safe_float(r.get("最低")),
                    "prev_close": _safe_float(r.get("昨收")),
                    "volume": _safe_float(r.get("成交量")),
                    "amount": _safe_float(r.get("成交额")),
                    "source": "akshare",
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception:
            pass

        # 优先级3: AKShare 历史日线
        symbol = INDEX_SYMBOL_MAP.get(index_code)
        if not symbol:
            prefix = "sh" if index_code.startswith("0") else "sz"
            symbol = prefix + index_code
        df = _retry(lambda: ak.stock_zh_index_daily_em(symbol=symbol))
        if df is None or df.empty:
            return {"error": f"未找到指数 {index_code}"}
        r = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else None
        close = float(r["close"])
        prev_close = float(prev["close"]) if prev is not None else None
        return {
            "code": index_code,
            "name": INDEX_NAME_MAP.get(index_code, index_code),
            "price": round(close, 2),
            "open": _safe_float(r.get("open")),
            "high": _safe_float(r.get("high")),
            "low": _safe_float(r.get("low")),
            "prev_close": round(prev_close, 2) if prev_close else None,
            "change": round(close - prev_close, 2) if prev_close else None,
            "change_pct": round((close - prev_close) / prev_close * 100, 2) if prev_close else None,
            "volume": _safe_float(r.get("volume")),
            "amount": _safe_float(r.get("amount")),
            "date": _safe_str(r.get("date")),
            "source": "akshare_hist",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_stock_comments(ticker: str) -> dict:
    """获取个股的千股千评数据（综合评分、资金流向评级等）。"""
    code = _normalize_ticker(ticker)
    try:
        df = _retry(ak.stock_comment_em)
        row = df[df["代码"] == code]
        if row.empty:
            return {"error": f"未找到 {ticker} 的千股千评数据"}
        r = row.iloc[0]
        return {
            "ticker": code + _market_suffix(code),
            "name": _safe_str(r.get("名称")),
            "score": _safe_float(r.get("综合得分")),
            "rank_change": _safe_str(r.get("综合排名变化")),
            "attention_index": _safe_float(r.get("关注指数")),
            "technical_side": _safe_str(r.get("技术面")),
            "capital_side": _safe_str(r.get("资金面")),
            "message_side": _safe_str(r.get("消息面")),
            "fundamental_side": _safe_str(r.get("基本面")),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_north_flow() -> dict:
    """获取北向资金（沪股通+深股通）当日实时流向数据。"""
    try:
        df = _retry(ak.stock_hsgt_fund_flow_summary_em)
        north_rows = df[df["资金方向"] == "北向"]
        if north_rows.empty:
            return {"error": "未获取到北向资金数据"}

        sh_row = north_rows[north_rows["板块"] == "沪股通"]
        sz_row = north_rows[north_rows["板块"] == "深股通"]
        sh_val = _safe_float(sh_row.iloc[0].get("成交净买额")) if not sh_row.empty else 0
        sz_val = _safe_float(sz_row.iloc[0].get("成交净买额")) if not sz_row.empty else 0
        sh_val = sh_val or 0
        sz_val = sz_val or 0
        trade_date = _safe_str(north_rows.iloc[0].get("交易日", ""))
        return {
            "date": trade_date,
            "shanghai_connect_net_buy": sh_val,
            "shenzhen_connect_net_buy": sz_val,
            "total_net_buy": round(sh_val + sz_val, 4),
            "unit": "亿元",
        }
    except Exception as e:
        return {"error": str(e)}


_TOOLS = {
    "search_stock": search_stock,
    "get_realtime_quote": get_realtime_quote,
    "get_kline": get_kline,
    "get_financial_report": get_financial_report,
    "get_individual_info": get_individual_info,
    "get_sector_flow": get_sector_flow,
    "get_top_list": get_top_list,
    "get_index_quote": get_index_quote,
    "get_stock_comments": get_stock_comments,
    "get_north_flow": get_north_flow,
}

if __name__ == "__main__":
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from call_logger import cli_main
    if not cli_main("stock-data-mcp", _TOOLS):
        mcp.run()
