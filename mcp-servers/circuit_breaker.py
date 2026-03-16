"""
通用熔断器 (Circuit Breaker) 模块。

三态模型：
  CLOSED  (正常)  → 连续失败 N 次 → OPEN  (熔断)
  OPEN    (熔断)  → 冷却时间到   → HALF_OPEN (探测)
  HALF_OPEN (探测) → 成功 → CLOSED / 失败 → OPEN

用法：
  from circuit_breaker import breaker

  if not breaker.is_available("akshare_spot"):
      ... 跳过此数据源 ...

  try:
      result = fetch_data()
      breaker.record_success("akshare_spot")
  except Exception as e:
      breaker.record_failure("akshare_spot", str(e))
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class _Entry:
    state: State = State.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0
    last_error: str = ""
    success_count: int = 0
    total_calls: int = 0
    total_failures: int = 0


class CircuitBreaker:
    """进程内熔断器，按 source_key 独立管理。"""

    def __init__(
        self,
        failure_threshold: int = 3,
        cooldown_seconds: float = 300,
        half_open_max_calls: int = 1,
    ):
        self._threshold = failure_threshold
        self._cooldown = cooldown_seconds
        self._half_open_max = half_open_max_calls
        self._entries: dict[str, _Entry] = {}

    def _get(self, key: str) -> _Entry:
        if key not in self._entries:
            self._entries[key] = _Entry()
        return self._entries[key]

    def is_available(self, key: str) -> bool:
        e = self._get(key)
        if e.state == State.CLOSED:
            return True
        if e.state == State.OPEN:
            if time.time() - e.last_failure_time >= self._cooldown:
                e.state = State.HALF_OPEN
                e.success_count = 0
                return True
            return False
        # HALF_OPEN: 允许有限探测
        return e.success_count < self._half_open_max

    def record_success(self, key: str) -> None:
        e = self._get(key)
        e.total_calls += 1
        if e.state == State.HALF_OPEN:
            e.success_count += 1
            if e.success_count >= self._half_open_max:
                e.state = State.CLOSED
                e.failure_count = 0
        else:
            e.failure_count = 0
            e.state = State.CLOSED

    def record_failure(self, key: str, error: str = "") -> None:
        e = self._get(key)
        e.total_calls += 1
        e.total_failures += 1
        e.failure_count += 1
        e.last_failure_time = time.time()
        e.last_error = error
        if e.state == State.HALF_OPEN:
            e.state = State.OPEN
        elif e.failure_count >= self._threshold:
            e.state = State.OPEN

    def get_status(self, key: str) -> dict:
        e = self._get(key)
        return {
            "key": key,
            "state": e.state.value,
            "failure_count": e.failure_count,
            "total_calls": e.total_calls,
            "total_failures": e.total_failures,
            "last_error": e.last_error[:200] if e.last_error else "",
            "cooldown_remaining": max(
                0, self._cooldown - (time.time() - e.last_failure_time)
            )
            if e.state == State.OPEN
            else 0,
        }

    def get_all_status(self) -> list[dict]:
        return [self.get_status(k) for k in sorted(self._entries)]

    def reset(self, key: Optional[str] = None) -> None:
        if key:
            if key in self._entries:
                del self._entries[key]
        else:
            self._entries.clear()


# 全局单例，各 MCP server 按需 import
breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=300)
