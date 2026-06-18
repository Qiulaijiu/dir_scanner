# -*- coding: utf-8 -*-
"""
核心扫描引擎
"""

import re
import threading
import time

from lib.core.data import options
from lib.core.exceptions import RequestException
from lib.core.logger import logger
from lib.core.scanner import Scanner
from lib.core.settings import (
    DEFAULT_TEST_PREFIXES,
    DEFAULT_TEST_SUFFIXES,
    WILDCARD_TEST_POINT_MARKER,
)
from lib.parse.url import clean_path
from lib.utils.common import human_size, lstrip_once


class Fuzzer:
    """核心扫描引擎"""

    def __init__(self, requester, dictionary, **kwargs):
        self._threads = []
        self._scanned = set()
        self._requester = requester
        self._dictionary = dictionary
        self._is_running = False
        self._play_event = threading.Event()
        self._paused_semaphore = threading.Semaphore(0)
        self._base_path = None
        self.exc = None
        self.match_callbacks = kwargs.get("match_callbacks", [])
        self.not_found_callbacks = kwargs.get("not_found_callbacks", [])
        self.error_callbacks = kwargs.get("error_callbacks", [])

    def wait(self, timeout=None):
        if self.exc:
            raise self.exc

        for thread in self._threads:
            thread.join(timeout)
            if thread.is_alive():
                return False
        return True

    def setup_scanners(self):
        """设置wildcard检测器"""
        self.scanners = {
            "default": {},
            "prefixes": {},
            "suffixes": {},
        }

        self.scanners["default"].update({
            "index": Scanner(self._requester, path=self._base_path),
            "random": Scanner(self._requester, path=self._base_path + WILDCARD_TEST_POINT_MARKER),
        })

        if options.get("exclude_response"):
            self.scanners["default"]["custom"] = Scanner(
                self._requester, tested=self.scanners, path=options["exclude_response"]
            )

        for prefix in list(options.get("prefixes", [])) + list(DEFAULT_TEST_PREFIXES):
            self.scanners["prefixes"][prefix] = Scanner(
                self._requester, tested=self.scanners,
                path=f"{self._base_path}{prefix}{WILDCARD_TEST_POINT_MARKER}",
                context=f"/{self._base_path}{prefix}***",
            )

        for suffix in list(options.get("suffixes", [])) + list(DEFAULT_TEST_SUFFIXES):
            self.scanners["suffixes"][suffix] = Scanner(
                self._requester, tested=self.scanners,
                path=f"{self._base_path}{WILDCARD_TEST_POINT_MARKER}{suffix}",
                context=f"/{self._base_path}***{suffix}",
            )

        for extension in options.get("extensions", []):
            if "." + extension not in self.scanners["suffixes"]:
                self.scanners["suffixes"]["." + extension] = Scanner(
                    self._requester, tested=self.scanners,
                    path=f"{self._base_path}{WILDCARD_TEST_POINT_MARKER}.{extension}",
                    context=f"/{self._base_path}***.{extension}",
                )

    def setup_threads(self):
        if self._threads:
            self._threads = []

        thread_count = options.get("thread_count", 30)
        for _ in range(thread_count):
            new_thread = threading.Thread(target=self.thread_proc)
            new_thread.daemon = True
            self._threads.append(new_thread)

    def get_scanners_for(self, path):
        """获取适用于路径的检测器"""
        path = clean_path(path)

        for prefix in self.scanners["prefixes"]:
            if path.startswith(prefix):
                yield self.scanners["prefixes"][prefix]

        for suffix in self.scanners["suffixes"]:
            if path.endswith(suffix):
                yield self.scanners["suffixes"][suffix]

        for scanner in self.scanners["default"].values():
            yield scanner

    def start(self):
        """启动扫描"""
        self.setup_scanners()
        self.setup_threads()

        self._running_threads_count = len(self._threads)
        self._is_running = True
        self._play_event.clear()

        for thread in self._threads:
            thread.start()

        self.play()

    def play(self):
        self._play_event.set()

    def pause(self):
        self._play_event.clear()
        for thread in self._threads:
            if thread.is_alive():
                self._paused_semaphore.acquire()
        self._is_running = False

    def resume(self):
        self._is_running = True
        self._paused_semaphore.release()
        self.play()

    def stop(self):
        self._is_running = False
        self.play()

    def scan(self, path, scanners):
        """扫描单个路径"""
        if path in self._scanned:
            return
        else:
            self._scanned.add(path)

        response = self._requester.request(path)

        if self.is_excluded(response):
            for callback in self.not_found_callbacks:
                callback(response)
            return

        for tester in scanners:
            if not tester.check(path, response):
                for callback in self.not_found_callbacks:
                    callback(response)
                return

        for callback in self.match_callbacks:
            callback(response)

    def is_excluded(self, resp):
        """验证响应是否应被排除"""
        if resp.status in options.get("exclude_status_codes", []):
            return True

        include_status = options.get("include_status_codes", [])
        if include_status and resp.status not in include_status:
            return True

        if resp.status in self._blacklists:
            for suffix in self._blacklists.get(resp.status, []):
                if resp.path.endswith(lstrip_once(suffix, "/")):
                    return True

        exclude_sizes = options.get("exclude_sizes", [])
        if human_size(resp.length).rstrip() in exclude_sizes:
            return True

        min_size = options.get("minimum_response_size", 0)
        if min_size and resp.length < min_size:
            return True

        max_size = options.get("maximum_response_size", 0)
        if max_size and resp.length > max_size:
            return True

        exclude_texts = options.get("exclude_texts", [])
        if any(text in resp.content for text in exclude_texts):
            return True

        exclude_regex = options.get("exclude_regex")
        if exclude_regex and re.search(exclude_regex, resp.content):
            return True

        exclude_redirect = options.get("exclude_redirect")
        if exclude_redirect:
            if exclude_redirect in resp.redirect or re.search(exclude_redirect, resp.redirect):
                return True

        return False

    def is_stopped(self):
        return self._running_threads_count == 0

    def decrease_threads(self):
        self._running_threads_count -= 1

    def increase_threads(self):
        self._running_threads_count += 1

    def set_base_path(self, path):
        self._base_path = path
        self._blacklists = {}

    def thread_proc(self):
        """线程处理函数"""
        self._play_event.wait()

        while self._is_running:
            try:
                path = next(self._dictionary)
                scanners = self.get_scanners_for(path)
                self.scan(self._base_path + path, scanners)
            except StopIteration:
                break
            except RequestException as e:
                for callback in self.error_callbacks:
                    callback(e)
                continue
            except Exception:
                self._is_running = False
                break

            if not self._play_event.is_set():
                self.decrease_threads()
                self._paused_semaphore.release()
                self._play_event.wait()
                self.increase_threads()

            delay = options.get("delay", 0)
            if delay:
                time.sleep(delay)
