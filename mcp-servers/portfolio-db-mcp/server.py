"""
portfolio-db-mcp: 持仓数据库 MCP Server
基于 SQLite 管理投资者、自选股、模拟持仓、交易记录和每日快照。
"""

from fastmcp import FastMCP
import sqlite3
import json
from datetime import datetime, date
from typing import Optional
from pathlib import Path

DB_PATH = Path(__file__).parent / "portfolio.db"

mcp = FastMCP(name="portfolio-db-mcp")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS investors (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            initial_funds REAL DEFAULT 1000000.00,
            available_funds REAL DEFAULT 1000000.00,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS watchlist (
            investor_id TEXT NOT NULL REFERENCES investors(id),
            ticker TEXT NOT NULL,
            name TEXT DEFAULT '',
            added_at TEXT DEFAULT (datetime('now', 'localtime')),
            PRIMARY KEY (investor_id, ticker)
        );

        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investor_id TEXT NOT NULL REFERENCES investors(id),
            ticker TEXT NOT NULL,
            name TEXT DEFAULT '',
            quantity INTEGER NOT NULL,
            avg_cost REAL NOT NULL,
            buy_date TEXT DEFAULT (date('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime')),
            UNIQUE(investor_id, ticker)
        );

        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investor_id TEXT NOT NULL REFERENCES investors(id),
            ticker TEXT NOT NULL,
            name TEXT DEFAULT '',
            action TEXT NOT NULL CHECK (action IN ('BUY', 'SELL')),
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            fee REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            reason TEXT DEFAULT '',
            traded_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS daily_snapshots (
            investor_id TEXT NOT NULL REFERENCES investors(id),
            date TEXT NOT NULL,
            total_value REAL,
            available_funds REAL,
            positions_value REAL,
            daily_pnl REAL,
            total_pnl REAL,
            total_pnl_pct REAL,
            positions_detail TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            PRIMARY KEY (investor_id, date)
        );
    """)
    conn.commit()
    conn.close()


init_db()


@mcp.tool
def create_investor(feishu_user_id: str, name: str) -> dict:
    """注册新投资者，初始资金100万。"""
    conn = get_conn()
    try:
        existing = conn.execute("SELECT id FROM investors WHERE id=?", (feishu_user_id,)).fetchone()
        if existing:
            return {"status": "exists", "investor_id": feishu_user_id, "message": f"投资者 {name} 已存在"}
        conn.execute(
            "INSERT INTO investors (id, name) VALUES (?, ?)",
            (feishu_user_id, name),
        )
        conn.commit()
        return {
            "status": "created",
            "investor_id": feishu_user_id,
            "name": name,
            "initial_funds": 1000000.00,
        }
    finally:
        conn.close()


@mcp.tool
def get_investor(feishu_user_id: str) -> dict:
    """查询投资者信息。"""
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM investors WHERE id=?", (feishu_user_id,)).fetchone()
        if not row:
            return {"error": f"投资者 {feishu_user_id} 不存在"}
        return dict(row)
    finally:
        conn.close()


@mcp.tool
def add_watchlist(investor_id: str, ticker: str, name: str = "") -> dict:
    """添加自选股。"""
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (investor_id, ticker, name) VALUES (?, ?, ?)",
            (investor_id, ticker, name),
        )
        conn.commit()
        return {"status": "ok", "investor_id": investor_id, "ticker": ticker, "action": "added"}
    finally:
        conn.close()


@mcp.tool
def remove_watchlist(investor_id: str, ticker: str) -> dict:
    """删除自选股。"""
    conn = get_conn()
    try:
        conn.execute(
            "DELETE FROM watchlist WHERE investor_id=? AND ticker=?",
            (investor_id, ticker),
        )
        conn.commit()
        return {"status": "ok", "investor_id": investor_id, "ticker": ticker, "action": "removed"}
    finally:
        conn.close()


@mcp.tool
def get_watchlist(investor_id: str) -> list[dict]:
    """获取投资者的自选股列表。"""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT ticker, name, added_at FROM watchlist WHERE investor_id=? ORDER BY added_at",
            (investor_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@mcp.tool
def execute_trade(
    investor_id: str,
    ticker: str,
    name: str,
    action: str,
    quantity: int,
    price: float,
    fee: float,
    reason: str = "",
) -> dict:
    """
    执行模拟交易。
    action: BUY 或 SELL
    fee: 手续费总额（由调用方计算好传入）
    """
    conn = get_conn()
    try:
        investor = conn.execute("SELECT * FROM investors WHERE id=?", (investor_id,)).fetchone()
        if not investor:
            return {"error": f"投资者 {investor_id} 不存在"}

        total_amount = price * quantity

        if action == "BUY":
            cost = total_amount + fee
            if investor["available_funds"] < cost:
                return {
                    "error": "资金不足",
                    "available": investor["available_funds"],
                    "required": cost,
                }
            conn.execute(
                "UPDATE investors SET available_funds = available_funds - ? WHERE id=?",
                (cost, investor_id),
            )
            existing = conn.execute(
                "SELECT * FROM positions WHERE investor_id=? AND ticker=?",
                (investor_id, ticker),
            ).fetchone()
            if existing:
                new_qty = existing["quantity"] + quantity
                new_cost = (existing["avg_cost"] * existing["quantity"] + total_amount + fee) / new_qty
                conn.execute(
                    "UPDATE positions SET quantity=?, avg_cost=?, updated_at=datetime('now','localtime') WHERE investor_id=? AND ticker=?",
                    (new_qty, round(new_cost, 4), investor_id, ticker),
                )
            else:
                avg_cost = (total_amount + fee) / quantity
                conn.execute(
                    "INSERT INTO positions (investor_id, ticker, name, quantity, avg_cost) VALUES (?, ?, ?, ?, ?)",
                    (investor_id, ticker, name, quantity, round(avg_cost, 4)),
                )

        elif action == "SELL":
            existing = conn.execute(
                "SELECT * FROM positions WHERE investor_id=? AND ticker=?",
                (investor_id, ticker),
            ).fetchone()
            if not existing:
                return {"error": f"未持有 {ticker}"}
            if existing["quantity"] < quantity:
                return {"error": f"持仓不足，当前持有 {existing['quantity']} 股"}

            proceeds = total_amount - fee
            conn.execute(
                "UPDATE investors SET available_funds = available_funds + ? WHERE id=?",
                (proceeds, investor_id),
            )

            new_qty = existing["quantity"] - quantity
            if new_qty == 0:
                conn.execute(
                    "DELETE FROM positions WHERE investor_id=? AND ticker=?",
                    (investor_id, ticker),
                )
            else:
                conn.execute(
                    "UPDATE positions SET quantity=?, updated_at=datetime('now','localtime') WHERE investor_id=? AND ticker=?",
                    (new_qty, investor_id, ticker),
                )

            pnl = (price - existing["avg_cost"]) * quantity - fee
        else:
            return {"error": f"无效的操作类型: {action}"}

        conn.execute(
            "INSERT INTO trades (investor_id, ticker, name, action, quantity, price, fee, total_amount, reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (investor_id, ticker, name, action, quantity, price, fee, total_amount, reason),
        )
        conn.commit()

        updated_investor = conn.execute("SELECT available_funds FROM investors WHERE id=?", (investor_id,)).fetchone()
        result = {
            "status": "ok",
            "action": action,
            "ticker": ticker,
            "name": name,
            "quantity": quantity,
            "price": price,
            "fee": round(fee, 2),
            "total_amount": round(total_amount, 2),
            "available_funds": round(updated_investor["available_funds"], 2),
        }
        if action == "SELL":
            result["pnl"] = round(pnl, 2)
            result["pnl_pct"] = round(pnl / (existing["avg_cost"] * quantity) * 100, 2)
        return result
    finally:
        conn.close()


@mcp.tool
def get_positions(investor_id: str) -> dict:
    """获取投资者的持仓明细。"""
    conn = get_conn()
    try:
        investor = conn.execute("SELECT * FROM investors WHERE id=?", (investor_id,)).fetchone()
        if not investor:
            return {"error": f"投资者 {investor_id} 不存在"}

        positions = conn.execute(
            "SELECT * FROM positions WHERE investor_id=? ORDER BY ticker",
            (investor_id,),
        ).fetchall()

        return {
            "investor_id": investor_id,
            "name": investor["name"],
            "available_funds": round(investor["available_funds"], 2),
            "initial_funds": investor["initial_funds"],
            "positions": [dict(p) for p in positions],
        }
    finally:
        conn.close()


@mcp.tool
def get_all_positions() -> dict:
    """获取所有投资者的持仓汇总（用于心跳监控）。"""
    conn = get_conn()
    try:
        investors = conn.execute("SELECT id, name FROM investors").fetchall()
        result = {"investors": [], "all_tickers": set()}
        for inv in investors:
            positions = conn.execute(
                "SELECT ticker FROM positions WHERE investor_id=?",
                (inv["id"],),
            ).fetchall()
            tickers = [p["ticker"] for p in positions]
            watchlist = conn.execute(
                "SELECT ticker FROM watchlist WHERE investor_id=?",
                (inv["id"],),
            ).fetchall()
            watch_tickers = [w["ticker"] for w in watchlist]

            all_tickers = list(set(tickers + watch_tickers))
            result["investors"].append({
                "investor_id": inv["id"],
                "name": inv["name"],
                "position_tickers": tickers,
                "watchlist_tickers": watch_tickers,
                "all_tickers": all_tickers,
            })
            result["all_tickers"].update(all_tickers)

        result["all_tickers"] = sorted(result["all_tickers"])
        return result
    finally:
        conn.close()


@mcp.tool
def get_trades(investor_id: str, days: int = 7) -> list[dict]:
    """获取投资者最近N天的交易记录。"""
    conn = get_conn()
    try:
        cutoff = (datetime.now() - __import__("datetime").timedelta(days=days)).strftime("%Y-%m-%d")
        rows = conn.execute(
            "SELECT * FROM trades WHERE investor_id=? AND date(traded_at) >= ? ORDER BY traded_at DESC",
            (investor_id, cutoff),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@mcp.tool
def get_all_today_trades() -> list[dict]:
    """获取所有投资者的今日交易记录。"""
    conn = get_conn()
    try:
        today = date.today().strftime("%Y-%m-%d")
        rows = conn.execute(
            """SELECT t.*, i.name as investor_name
               FROM trades t JOIN investors i ON t.investor_id = i.id
               WHERE date(t.traded_at) = ?
               ORDER BY t.traded_at DESC""",
            (today,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@mcp.tool
def save_daily_snapshot(
    investor_id: str,
    total_value: float,
    positions_value: float,
    daily_pnl: float,
    total_pnl: float,
    total_pnl_pct: float,
    positions_detail: str = "",
) -> dict:
    """保存投资者的每日持仓快照。"""
    conn = get_conn()
    try:
        today = date.today().strftime("%Y-%m-%d")
        investor = conn.execute("SELECT available_funds FROM investors WHERE id=?", (investor_id,)).fetchone()
        if not investor:
            return {"error": f"投资者 {investor_id} 不存在"}

        conn.execute(
            """INSERT OR REPLACE INTO daily_snapshots
               (investor_id, date, total_value, available_funds, positions_value, daily_pnl, total_pnl, total_pnl_pct, positions_detail)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (investor_id, today, total_value, investor["available_funds"], positions_value, daily_pnl, total_pnl, total_pnl_pct, positions_detail),
        )
        conn.commit()
        return {"status": "ok", "investor_id": investor_id, "date": today}
    finally:
        conn.close()


@mcp.tool
def get_pnl_ranking(ranking_date: str = "") -> list[dict]:
    """
    获取指定日期的收益排行榜。
    ranking_date: YYYY-MM-DD格式，默认今天。
    """
    conn = get_conn()
    try:
        if not ranking_date:
            ranking_date = date.today().strftime("%Y-%m-%d")
        rows = conn.execute(
            """SELECT s.*, i.name as investor_name
               FROM daily_snapshots s JOIN investors i ON s.investor_id = i.id
               WHERE s.date = ?
               ORDER BY s.daily_pnl DESC""",
            (ranking_date,),
        ).fetchall()
        if not rows:
            return [{"message": f"{ranking_date} 暂无快照数据"}]
        return [dict(r) for r in rows]
    finally:
        conn.close()


@mcp.tool
def get_available_funds(investor_id: str) -> dict:
    """查询投资者可用资金。"""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT available_funds, initial_funds FROM investors WHERE id=?",
            (investor_id,),
        ).fetchone()
        if not row:
            return {"error": f"投资者 {investor_id} 不存在"}
        return {
            "investor_id": investor_id,
            "available_funds": round(row["available_funds"], 2),
            "initial_funds": row["initial_funds"],
        }
    finally:
        conn.close()


@mcp.tool
def list_investors() -> list[dict]:
    """列出所有已注册的投资者。"""
    conn = get_conn()
    try:
        rows = conn.execute("SELECT id, name, available_funds, initial_funds, created_at FROM investors ORDER BY created_at").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


if __name__ == "__main__":
    mcp.run()
