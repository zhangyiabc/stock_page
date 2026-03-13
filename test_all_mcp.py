"""
批量测试所有 MCP 工具。
运行方式: python -u test_all_mcp.py
"""

import subprocess
import json
import time
import sys
import os
from pathlib import Path

os.environ["PYTHONUNBUFFERED"] = "1"

BASE = Path(__file__).parent / "mcp-servers"
PYTHON = sys.executable

TESTS = [
    # ── stock-data-mcp (10 tools) ──
    ("stock-data-mcp", "search_stock", {"keyword": "茅台"}),
    ("stock-data-mcp", "get_realtime_quote", {"ticker": "600519"}),
    ("stock-data-mcp", "get_kline", {"ticker": "600519", "period": "daily", "count": 3}),
    ("stock-data-mcp", "get_financial_report", {"ticker": "600519"}),
    ("stock-data-mcp", "get_individual_info", {"ticker": "600519"}),
    ("stock-data-mcp", "get_sector_flow", {}),
    ("stock-data-mcp", "get_top_list", {}),
    ("stock-data-mcp", "get_index_quote", {}),
    ("stock-data-mcp", "get_stock_comments", {"ticker": "600519"}),
    ("stock-data-mcp", "get_north_flow", {}),

    # ── news-sentiment-mcp (6 tools) ──
    ("news-sentiment-mcp", "get_stock_news", {"ticker": "600519", "count": 3}),
    ("news-sentiment-mcp", "get_policy_news", {}),
    ("news-sentiment-mcp", "get_market_sentiment", {}),
    ("news-sentiment-mcp", "check_sentiment_change", {"tickers": "600519,000858"}),
    ("news-sentiment-mcp", "get_financial_news", {"count": 3}),
    ("news-sentiment-mcp", "get_stock_rank_hot", {}),

    # ── portfolio-db-mcp (14 tools) ──
    ("portfolio-db-mcp", "create_investor", {"feishu_user_id": "ou_test_run_001", "name": "全量测试用户"}),
    ("portfolio-db-mcp", "get_investor", {"feishu_user_id": "ou_test_run_001"}),
    ("portfolio-db-mcp", "list_investors", {}),
    ("portfolio-db-mcp", "get_available_funds", {"investor_id": "ou_test_run_001"}),
    ("portfolio-db-mcp", "add_watchlist", {"investor_id": "ou_test_run_001", "ticker": "600519", "name": "贵州茅台"}),
    ("portfolio-db-mcp", "get_watchlist", {"investor_id": "ou_test_run_001"}),
    ("portfolio-db-mcp", "execute_trade", {"investor_id": "ou_test_run_001", "ticker": "600519", "name": "贵州茅台", "action": "BUY", "price": 1413.0, "quantity": 100, "fee": 4.24}),
    ("portfolio-db-mcp", "get_positions", {"investor_id": "ou_test_run_001"}),
    ("portfolio-db-mcp", "get_all_positions", {}),
    ("portfolio-db-mcp", "get_trades", {"investor_id": "ou_test_run_001"}),
    ("portfolio-db-mcp", "get_all_today_trades", {}),
    ("portfolio-db-mcp", "save_daily_snapshot", {"investor_id": "ou_test_run_001", "total_value": 500000, "positions_value": 141300, "daily_pnl": 0, "total_pnl": 0, "total_pnl_pct": 0}),
    ("portfolio-db-mcp", "get_pnl_ranking", {}),
    ("portfolio-db-mcp", "remove_watchlist", {"investor_id": "ou_test_run_001", "ticker": "600519"}),
]

WIDTH_SVC = 22
WIDTH_TOOL = 26

def run_test(svc, tool, args):
    server_py = str(BASE / svc / "server.py")
    cmd = [PYTHON, server_py, "call", tool]
    if args:
        cmd.append(json.dumps(args, ensure_ascii=False))
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        elapsed = (time.time() - t0) * 1000
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        if proc.returncode != 0:
            return "FAIL", elapsed, f"exit={proc.returncode} stderr={stderr[:200]}"
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return "FAIL", elapsed, f"invalid JSON: {stdout[:200]}"
        if isinstance(data, dict) and "error" in data:
            return "FAIL", elapsed, data["error"][:200]
        preview = json.dumps(data, ensure_ascii=False)
        if len(preview) > 120:
            preview = preview[:120] + "..."
        return "OK", elapsed, preview
    except subprocess.TimeoutExpired:
        return "TIMEOUT", 90000, "超过 90 秒"
    except Exception as e:
        return "ERROR", 0, str(e)[:200]

if __name__ == "__main__":
    header = f"{'服务':<{WIDTH_SVC}} {'工具':<{WIDTH_TOOL}} {'状态':>6}  {'耗时':>10}  结果预览"
    print(header, flush=True)
    print("─" * 130, flush=True)
    ok_count = 0
    fail_count = 0
    for svc, tool, args in TESTS:
        status, ms, preview = run_test(svc, tool, args)
        tag = "✓" if status == "OK" else "✗"
        if status == "OK":
            ok_count += 1
        else:
            fail_count += 1
        print(f"{svc:<{WIDTH_SVC}} {tool:<{WIDTH_TOOL}} {tag} {status:>5}  {ms:>8.0f}ms  {preview}", flush=True)
    print("─" * 130, flush=True)
    print(f"总计: {ok_count + fail_count} 个工具 | ✓ {ok_count} 通过 | ✗ {fail_count} 失败", flush=True)
