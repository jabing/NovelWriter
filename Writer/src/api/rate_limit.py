"""Rate limiting middleware for API protection.

Provides IP-based request rate limiting to prevent abuse.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Callable

import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    block_duration_seconds: int = 60


@dataclass
class ClientState:
    """Tracks request state for a single client."""
    minute_requests: list[float] = field(default_factory=list)
    hour_requests: list[float] = field(default_factory=list)
    blocked_until: float = 0.0


class RateLimiter:
    """IP-based rate limiter with sliding window."""
    
    def __init__(self, config: RateLimitConfig | None = None) -> None:
        self.config = config or RateLimitConfig()
        self._clients: dict[str, ClientState] = defaultdict(ClientState)
        logger.info(
            f"RateLimiter initialized: {self.config.requests_per_minute}/min, "
            f"{self.config.requests_per_hour}/hour"
        )
    
    def _cleanup_old_requests(self, client: ClientState, now: float) -> None:
        """Remove requests older than the tracking window."""
        minute_ago = now - 60
        hour_ago = now - 3600
        
        client.minute_requests = [t for t in client.minute_requests if t > minute_ago]
        client.hour_requests = [t for t in client.hour_requests if t > hour_ago]
    
    def is_allowed(self, client_ip: str) -> tuple[bool, str]:
        """Check if client is allowed to make a request."""
        now = time.time()
        client = self._clients[client_ip]
        
        if client.blocked_until > now:
            remaining = int(client.blocked_until - now)
            return False, f"Rate limit exceeded. Try again in {remaining}s"
        
        self._cleanup_old_requests(client, now)
        
        if len(client.minute_requests) >= self.config.requests_per_minute:
            client.blocked_until = now + self.config.block_duration_seconds
            logger.warning(f"Rate limit exceeded for {client_ip}: minute limit")
            return False, "Minute rate limit exceeded"
        
        if len(client.hour_requests) >= self.config.requests_per_hour:
            client.blocked_until = now + self.config.block_duration_seconds
            logger.warning(f"Rate limit exceeded for {client_ip}: hour limit")
            return False, "Hourly rate limit exceeded"
        
        client.minute_requests.append(now)
        client.hour_requests.append(now)
        
        return True, ""
    
    def get_client_status(self, client_ip: str) -> dict:
        """Get rate limit status for a client."""
        now = time.time()
        client = self._clients[client_ip]
        self._cleanup_old_requests(client, now)
        
        return {
            "minute_requests": len(client.minute_requests),
            "minute_limit": self.config.requests_per_minute,
            "hour_requests": len(client.hour_requests),
            "hour_limit": self.config.requests_per_hour,
            "blocked": client.blocked_until > now,
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(
        self, 
        app, 
        limiter: RateLimiter | None = None,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.limiter = limiter or RateLimiter()
        self.exclude_paths = exclude_paths or {"/health", "/docs", "/openapi.json"}
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with rate limiting."""
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        allowed, reason = self.limiter.is_allowed(client_ip)
        
        if not allowed:
            logger.warning(f"Rate limit blocked: {client_ip} - {reason}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too Many Requests",
                    "reason": reason,
                    "retry_after": self.limiter.config.block_duration_seconds,
                },
                headers={"Retry-After": str(self.limiter.config.block_duration_seconds)},
            )
        
        response = await call_next(request)
        
        status = self.limiter.get_client_status(client_ip)
        response.headers["X-RateLimit-Limit-Minute"] = str(status["minute_limit"])
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            status["minute_limit"] - status["minute_requests"]
        )
        
        return response


rate_limiter = RateLimiter()
