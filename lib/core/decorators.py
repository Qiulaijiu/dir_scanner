# -*- coding: utf-8 -*-
"""
装饰器
"""

import time
import threading

_lock = threading.Lock()


def locked(func):
    """线程锁装饰器"""
    def wrapper(*args, **kwargs):
        with _lock:
            return func(*args, **kwargs)
    return wrapper


def cached(timeout):
    """缓存装饰器（线程安全）"""
    def decorator(func):
        last_update = [0]
        cache = [None]
        cache_lock = threading.Lock()

        def wrapper(*args, **kwargs):
            now = time.time()
            if now - last_update[0] > timeout:
                with cache_lock:
                    if now - last_update[0] > timeout:
                        cache[0] = func(*args, **kwargs)
                        last_update[0] = now
            return cache[0]
        return wrapper
    return decorator
