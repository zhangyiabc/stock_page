"""
统一的 CLI 调用日志模块。

日志文件：
  - mcp-servers/logs/calls.log      — 摘要日志（单行格式，便于 tail -f 监控）
  - mcp-servers/logs/calls_detail.jsonl — 详细日志（完整 JSON，不截断，便于排查）

每次工具调用同时写入两份日志。
"""

import json
import time
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_FILE = LOG_DIR / "calls.log"
DETAIL_FILE = LOG_DIR / "calls_detail.jsonl"
SUMMARY_PREVIEW = 300


def _truncate(text: str, limit: int = SUMMARY_PREVIEW) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _is_error(result) -> bool:
    if isinstance(result, dict) and "error" in result:
        return True
    if isinstance(result, list) and result and isinstance(result[0], dict) and "error" in result[0]:
        return True
    return False


def log_call(server_name: str, tool_name: str, args: dict, result, elapsed_ms: float):
    LOG_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    status = "FAIL" if _is_error(result) else "OK"

    result_s = json.dumps(result, ensure_ascii=False, default=str) if result is not None else ""
    args_s = json.dumps(args, ensure_ascii=False)

    # 摘要日志
    summary_line = (
        f"{ts} | {server_name:20s} | {tool_name:25s} | "
        f"{elapsed_ms:8.0f}ms | {status:4s} | "
        f"{_truncate(args_s)} | {_truncate(result_s)}\n"
    )
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(summary_line)

    # 详细日志（完整 JSON，不截断）
    detail = {
        "ts": ts,
        "server": server_name,
        "tool": tool_name,
        "elapsed_ms": round(elapsed_ms, 1),
        "status": status,
        "args": args,
        "result": result,
    }
    with open(DETAIL_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(detail, ensure_ascii=False, default=str) + "\n")


def cli_main(server_name: str, tools: dict) -> bool:
    """统一的 CLI 入口，带日志记录。返回 True 表示已处理 CLI 调用，False 表示应走 MCP 模式。"""
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "call":
        tool_name = sys.argv[2]
        args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        if tool_name == "list":
            print(json.dumps(list(tools.keys()), ensure_ascii=False))
            return True
        if tool_name == "breaker_status":
            try:
                from circuit_breaker import breaker
                print(json.dumps(breaker.get_all_status(), ensure_ascii=False))
            except ImportError:
                print(json.dumps({"error": "circuit_breaker module not available"}))
            return True

        if tool_name not in tools:
            err = {"error": f"Unknown tool: {tool_name}"}
            log_call(server_name, tool_name, args, err, 0)
            print(json.dumps(err))
            return True

        t0 = time.time()
        try:
            result = tools[tool_name](**args)
        except Exception as e:
            result = {"error": str(e)}
        elapsed = (time.time() - t0) * 1000
        log_call(server_name, tool_name, args, result, elapsed)
        print(json.dumps(result, ensure_ascii=False, default=str))
        return True
    return False
