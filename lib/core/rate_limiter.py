# -*- coding: utf-8 -*-
"""
令牌桶限速器
"""

import asyncio
import threading
import time


class RateLimiter:
    """令牌桶算法限速器，限制每秒请求数"""

    def __init__(self, rate: float):
        """
        rate: 每秒允许的最大请求数
        """
        self.rate = rate
        self.tokens = rate
        self.last_time = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """获取一个令牌"""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_time
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_time = now

            if self.tokens < 1:
                wait = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1

    def reset(self):
        """重置限速器"""
        self.tokens = self.rate
        self.last_time = time.monotonic()


class SyncRateLimiter:
    """同步令牌桶限速器"""

    def __init__(self, rate: float):
        self.rate = rate
        self.tokens = rate
        self.last_time = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self):
        """获取一个令牌"""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_time
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_time = now

            if self.tokens < 1:
                wait = (1 - self.tokens) / self.rate
                time.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1

    def reset(self):
        """重置限速器"""
        self.tokens = self.rate
        self.last_time = time.monotonic()
