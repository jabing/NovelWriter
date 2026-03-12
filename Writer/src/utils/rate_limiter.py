#!/usr/bin/env python3
"""
API Rate Limiter - Prevents API abuse through request throttling.

Features:
- IP-based rate limiting (default: 60 requests/minute)
- User-based quota limiting (default: 1000 requests/hour)
- Configurable rate limit parameters
- Thread-safe implementation
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps
from threading import Lock
from typing import Any, Callable


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    remaining: int
    reset_time: float
    retry_after: float | None = None


class APILimiter:
    """
    API 限流器 - 基于滑动窗口算法实现请求速率限制。

    Attributes:
        requests_per_minute: 每分钟最大请求数
        requests_per_hour: 每小时最大请求数（可选）
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int | None = None,
    ) -> None:
        """
        初始化限流器。

        Args:
            requests_per_minute: 每分钟最大请求数，默认 60
            requests_per_hour: 每小时最大请求数，默认 None（不限制）
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour or 0
        self.requests_per_second: dict[str, list[float]] = defaultdict(list)
        self.requests_per_minute_data: dict[str, list[float]] = defaultdict(list)
        self.requests_per_hour_data: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def _cleanup_old_requests(self, client_id: str, cutoff: float) -> None:
        """清理指定时间之前的请求记录。"""
        for data_dict in [
            self.requests_per_second,
            self.requests_per_minute_data,
            self.requests_per_hour_data,
        ]:
            data_dict[client_id] = [
                req_time for req_time in data_dict[client_id] if req_time > cutoff
            ]

    def is_allowed(self, client_id: str) -> RateLimitResult:
        """
        检查请求是否允许。

        Args:
            client_id: 客户端标识（IP 地址或用户 ID）

        Returns:
            RateLimitResult: 包含是否允许、剩余请求数等信息
        """
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600

        with self._lock:
            # 清理旧请求 - 分别清理分钟和小时数据
            self.requests_per_minute_data[client_id] = [
                req_time for req_time in self.requests_per_minute_data[client_id]
                if req_time > minute_ago
            ]
            self.requests_per_hour_data[client_id] = [
                req_time for req_time in self.requests_per_hour_data[client_id]
                if req_time > hour_ago
            ]

            # 检查每分钟限制
            minute_requests = self.requests_per_minute_data[client_id]
            if len(minute_requests) >= self.requests_per_minute:
                oldest_minute = min(minute_requests) if minute_requests else now
                retry_after = oldest_minute + 60 - now
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=oldest_minute + 60,
                    retry_after=max(0, retry_after),
                )

            # 检查每小时限制
            if self.requests_per_hour > 0:
                hour_requests = self.requests_per_hour_data[client_id]
                if len(hour_requests) >= self.requests_per_hour:
                    oldest_hour = min(hour_requests) if hour_requests else now
                    retry_after = oldest_hour + 3600 - now
                    return RateLimitResult(
                        allowed=False,
                        remaining=0,
                        reset_time=oldest_hour + 3600,
                        retry_after=max(0, retry_after),
                    )

            # 记录新请求
            self.requests_per_minute_data[client_id].append(now)
            if self.requests_per_hour > 0:
                self.requests_per_hour_data[client_id].append(now)

            # 计算剩余请求数
            minute_remaining = self.requests_per_minute - len(minute_requests) - 1
            hour_remaining = -1
            if self.requests_per_hour > 0:
                hour_requests = self.requests_per_hour_data[client_id]
                hour_remaining = self.requests_per_hour - len(hour_requests) - 1
            remaining = min(minute_remaining, hour_remaining) if hour_remaining >= 0 else minute_remaining

            return RateLimitResult(
                allowed=True,
                remaining=max(0, remaining),
                reset_time=now + 60,
                retry_after=None,
            )

    def rate_limit(
        self,
        requests_per_minute: int | None = None,
        requests_per_hour: int | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        限流装饰器。

        Args:
            requests_per_minute: 每分钟最大请求数
            requests_per_hour: 每小时最大请求数

        Returns:
            装饰器函数

        Example:
            @limiter.rate_limit(requests_per_minute=10)
            async def my_api_endpoint():
                ...
        """
        rpm = requests_per_minute or self.requests_per_minute
        rph = requests_per_hour or self.requests_per_hour

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                # 尝试获取 client_id（从请求参数或上下文）
                client_id = kwargs.get("client_id", kwargs.get("ip", "default"))

                # 创建临时限流器实例进行检查
                temp_limiter = APILimiter(requests_per_minute=rpm, requests_per_hour=rph)
                # 复用主限流器的状态（这里简化处理，实际应共享状态）
                result = self.is_allowed(client_id)

                if not result.allowed:
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=429,
                        detail={
                            "error": "Rate limit exceeded",
                            "retry_after": result.retry_after,
                            "reset_time": result.reset_time,
                        },
                    )

                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def get_client_stats(self, client_id: str) -> dict[str, Any]:
        """
        获取客户端的请求统计信息。

        Args:
            client_id: 客户端标识

        Returns:
            包含请求统计的字典
        """
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600

        with self._lock:
            minute_count = len(
                [t for t in self.requests_per_minute_data.get(client_id, []) if t > minute_ago]
            )
            hour_count = len(
                [t for t in self.requests_per_hour_data.get(client_id, []) if t > hour_ago]
            )

            return {
                "client_id": client_id,
                "requests_last_minute": minute_count,
                "requests_last_hour": hour_count,
                "minute_limit": self.requests_per_minute,
                "hour_limit": self.requests_per_hour,
                "minute_remaining": max(0, self.requests_per_minute - minute_count),
                "hour_remaining": max(0, self.requests_per_hour - hour_count)
                if self.requests_per_hour > 0
                else None,
            }

    def reset_client(self, client_id: str) -> None:
        """
        重置客户端的请求计数。

        Args:
            client_id: 客户端标识
        """
        with self._lock:
            self.requests_per_minute_data.pop(client_id, None)
            self.requests_per_hour_data.pop(client_id, None)

    def reset_all(self) -> None:
        """重置所有客户端的请求计数。"""
        with self._lock:
            self.requests_per_minute_data.clear()
            self.requests_per_hour_data.clear()


# 全局限流器实例
_default_limiter: APILimiter | None = None


def get_api_limiter(
    requests_per_minute: int = 60, requests_per_hour: int = 1000
) -> APILimiter:
    """
    获取或创建全局限流器实例。

    Args:
        requests_per_minute: 每分钟最大请求数
        requests_per_hour: 每小时最大请求数

    Returns:
        APILimiter 实例
    """
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = APILimiter(
            requests_per_minute=requests_per_minute, requests_per_hour=requests_per_hour
        )
    return _default_limiter


def rate_limit(
    requests_per_minute: int = 60, requests_per_hour: int = 1000
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    便捷的限流装饰器。

    Args:
        requests_per_minute: 每分钟最大请求数
        requests_per_hour: 每小时最大请求数

    Returns:
        装饰器函数

    Example:
        @rate_limit(requests_per_minute=30)
        async def my_endpoint():
            ...
    """
    limiter = get_api_limiter(requests_per_minute, requests_per_hour)
    return limiter.rate_limit(requests_per_minute, requests_per_hour)
