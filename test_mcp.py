"""
MCP Server 端到端测试脚本
逐个测试 3 个 MCP Server 的所有工具
"""
import asyncio
import json
import sys
import traceback
from fastmcp import Client

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
SKIP = "\033[93m○\033[0m"


async def call(client, tool_name, args=None):
    result = await client.call_tool(tool_name, args or {})
    if isinstance(result, list) and len(result) > 0:
        content = result[0]
        if hasattr(content, "text"):
            text = content.text
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return text
    if hasattr(result, "content") and result.content:
        content = result.content[0]
        if hasattr(content, "text"):
            try:
                return json.loads(content.text)
            except (json.JSONDecodeError, TypeError):
                return content.text
    return result


def preview(data, max_len=200):
    s = json.dumps(data, ensure_ascii=False, default=str)
    return s[:max_len] + "..." if len(s) > max_len else s


async def test_stock_data_mcp():
    print("\n" + "=" * 60)
    print("  Testing stock-data-mcp")
    print("=" * 60)

    client = Client("mcp-servers/stock-data-mcp/server.py")
    async with client:
        tools = await client.list_tools()
        print(f"  Loaded {len(tools)} tools: {[t.name for t in tools]}\n")

        tests = [
            ("search_stock", {"keyword": "贵州茅台"}),
            ("get_realtime_quote", {"ticker": "600519"}),
            ("get_kline", {"ticker": "600519", "period": "daily", "count": 5}),
            ("get_individual_info", {"ticker": "600519"}),
            ("get_index_quote", {"index_code": "000001"}),
            ("get_stock_comments", {"ticker": "600519"}),
            ("get_sector_flow", {}),
            ("get_north_flow", {}),
            ("get_financial_report", {"ticker": "600519"}),
            ("get_top_list", {}),
        ]

        results = {}
        for name, args in tests:
            try:
                r = await call(client, name, args)
                has_error = False
                if isinstance(r, dict) and "error" in r:
                    has_error = True
                elif isinstance(r, list) and r and isinstance(r[0], dict) and "error" in r[0]:
                    has_error = True

                if has_error:
                    print(f"  {FAIL} {name}: ERROR - {preview(r)}")
                    results[name] = "FAIL"
                else:
                    print(f"  {PASS} {name}: {preview(r)}")
                    results[name] = "PASS"
            except Exception as e:
                print(f"  {FAIL} {name}: EXCEPTION - {e}")
                traceback.print_exc()
                results[name] = "FAIL"

    return results


async def test_news_sentiment_mcp():
    print("\n" + "=" * 60)
    print("  Testing news-sentiment-mcp")
    print("=" * 60)

    client = Client("mcp-servers/news-sentiment-mcp/server.py")
    async with client:
        tools = await client.list_tools()
        print(f"  Loaded {len(tools)} tools: {[t.name for t in tools]}\n")

        tests = [
            ("get_stock_news", {"ticker": "600519", "count": 3}),
            ("get_policy_news", {}),
            ("get_market_sentiment", {}),
            ("check_sentiment_change", {"tickers": "600519,000858", "hours": 24}),
            ("get_financial_news", {"count": 3}),
            ("get_stock_rank_hot", {"count": 5}),
        ]

        results = {}
        for name, args in tests:
            try:
                r = await call(client, name, args)
                has_error = False
                if isinstance(r, dict) and "error" in r:
                    has_error = True
                elif isinstance(r, list) and r and isinstance(r[0], dict) and "error" in r[0]:
                    has_error = True

                if has_error:
                    print(f"  {FAIL} {name}: ERROR - {preview(r)}")
                    results[name] = "FAIL"
                else:
                    print(f"  {PASS} {name}: {preview(r)}")
                    results[name] = "PASS"
            except Exception as e:
                print(f"  {FAIL} {name}: EXCEPTION - {e}")
                traceback.print_exc()
                results[name] = "FAIL"

    return results


async def test_portfolio_db_mcp():
    print("\n" + "=" * 60)
    print("  Testing portfolio-db-mcp")
    print("=" * 60)

    client = Client("mcp-servers/portfolio-db-mcp/server.py")
    async with client:
        tools = await client.list_tools()
        print(f"  Loaded {len(tools)} tools: {[t.name for t in tools]}\n")

        results = {}

        async def run(name, args=None):
            try:
                r = await call(client, name, args or {})
                has_error = isinstance(r, dict) and "error" in r
                if has_error:
                    print(f"  {FAIL} {name}: ERROR - {preview(r)}")
                    results[name] = "FAIL"
                else:
                    print(f"  {PASS} {name}: {preview(r)}")
                    results[name] = "PASS"
                return r
            except Exception as e:
                print(f"  {FAIL} {name}: EXCEPTION - {e}")
                traceback.print_exc()
                results[name] = "FAIL"
                return None

        await run("create_investor", {"feishu_user_id": "test_user_001", "name": "测试张三"})
        await run("create_investor", {"feishu_user_id": "test_user_002", "name": "测试李四"})

        await run("get_investor", {"feishu_user_id": "test_user_001"})
        await run("list_investors")

        await run("add_watchlist", {"investor_id": "test_user_001", "ticker": "600519.SH", "name": "贵州茅台"})
        await run("add_watchlist", {"investor_id": "test_user_001", "ticker": "000858.SZ", "name": "五粮液"})
        await run("get_watchlist", {"investor_id": "test_user_001"})

        await run("execute_trade", {
            "investor_id": "test_user_001",
            "ticker": "600519.SH",
            "name": "贵州茅台",
            "action": "BUY",
            "quantity": 100,
            "price": 1800.0,
            "fee": 54.0,
            "reason": "测试买入",
        })

        await run("get_positions", {"investor_id": "test_user_001"})
        await run("get_available_funds", {"investor_id": "test_user_001"})
        await run("get_trades", {"investor_id": "test_user_001", "days": 7})

        await run("execute_trade", {
            "investor_id": "test_user_001",
            "ticker": "600519.SH",
            "name": "贵州茅台",
            "action": "SELL",
            "quantity": 50,
            "price": 1850.0,
            "fee": 27.75,
            "reason": "测试卖出",
        })

        await run("get_positions", {"investor_id": "test_user_001"})
        await run("get_all_positions")
        await run("get_all_today_trades")

        await run("save_daily_snapshot", {
            "investor_id": "test_user_001",
            "total_value": 1002000.0,
            "positions_value": 92000.0,
            "daily_pnl": 2000.0,
            "total_pnl": 2000.0,
            "total_pnl_pct": 0.2,
            "positions_detail": "600519:50股",
        })
        await run("get_pnl_ranking")

        await run("remove_watchlist", {"investor_id": "test_user_001", "ticker": "000858.SZ"})
        await run("get_watchlist", {"investor_id": "test_user_001"})

    return results


async def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    all_results = {}

    if target in ("all", "stock"):
        all_results["stock-data-mcp"] = await test_stock_data_mcp()

    if target in ("all", "news"):
        all_results["news-sentiment-mcp"] = await test_news_sentiment_mcp()

    if target in ("all", "portfolio"):
        all_results["portfolio-db-mcp"] = await test_portfolio_db_mcp()

    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    total_pass = 0
    total_fail = 0
    for server, results in all_results.items():
        p = sum(1 for v in results.values() if v == "PASS")
        f = sum(1 for v in results.values() if v == "FAIL")
        total_pass += p
        total_fail += f
        status = PASS if f == 0 else FAIL
        print(f"  {status} {server}: {p}/{p + f} passed")
        if f > 0:
            for name, v in results.items():
                if v == "FAIL":
                    print(f"      {FAIL} {name}")

    print(f"\n  Total: {total_pass}/{total_pass + total_fail} passed")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
