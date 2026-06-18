# -*- coding: utf-8 -*-
"""
HTTP请求器
"""

import random
import re
import requests
import threading
import time
import urllib3

from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from urllib.parse import urlparse

from lib.core.data import options
from lib.core.decorators import cached
from lib.core.exceptions import RequestException
from lib.core.logger import logger
from lib.core.rate_limiter import SyncRateLimiter
from lib.core.settings import PROXY_SCHEMES, RATE_UPDATE_DELAY
from lib.core.structures import CaseInsensitiveDict
from lib.core.waf_bypass import WAFBypass
from lib.connection.response import Response
from lib.utils.common import safequote

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Requester:
    """HTTP请求器"""

    def __init__(self):
        self._url = None
        self._proxy_cred = None
        self._rate = 0
        self.headers = CaseInsensitiveDict(options.get("headers", {}))
        self.agents = []
        self.session = requests.Session()
        self.session.verify = False
        self.session.trust_env = False  # 不使用系统代理

        # 认证设置
        if options.get("auth"):
            self.set_auth(options.get("auth_type", "basic"), options["auth"])

        # 随机UA池
        if options.get("random_agents", False):
            from lib.core.settings import USER_AGENT_POOL
            self.agents = USER_AGENT_POOL

        # WAF绕过
        self.waf_bypass = options.get("waf_bypass", False)

        # 限速器
        self.rate_limiter = None
        if options.get("max_rate", 0) > 0:
            self.rate_limiter = SyncRateLimiter(options["max_rate"])

        # 连接池设置
        thread_count = options.get("thread_count", 30)
        for scheme in ("http://", "https://"):
            self.session.mount(
                scheme, HTTPAdapter(max_retries=0, pool_maxsize=thread_count)
            )

    def set_url(self, url):
        self._url = url

    def set_header(self, key, value):
        self.headers[key] = value.lstrip()

    def set_auth(self, auth_type, credential):
        if auth_type in ("bearer", "jwt", "oauth2"):
            self.headers["Authorization"] = f"Bearer {credential}"
        else:
            try:
                user, password = credential.split(":", 1)
            except ValueError:
                user = credential
                password = ""

            if auth_type == "basic":
                self.session.auth = HTTPBasicAuth(user, password)
            elif auth_type == "digest":
                self.session.auth = HTTPDigestAuth(user, password)

    def set_proxy(self, proxy):
        if not proxy:
            return

        if not proxy.startswith(PROXY_SCHEMES):
            proxy = f"http://{proxy}"

        if self._proxy_cred and "@" not in proxy:
            proxy = proxy.replace("://", f"://{self._proxy_cred}@", 1)

        self.session.proxies = {"https": proxy}
        if not proxy.startswith("https://"):
            self.session.proxies["http"] = proxy

    def set_proxy_auth(self, credential):
        self._proxy_cred = credential

    def request(self, path, proxy=None):
        """发送HTTP请求"""
        # 限速（令牌桶算法）
        if self.rate_limiter:
            self.rate_limiter.acquire()

        self.increase_rate()

        err_msg = None
        # 规范化URL，避免双斜杠
        base = self._url.rstrip("/") if self._url else ""
        url = safequote(base + "/" + path.lstrip("/") if self._url else path)
        original_path = path

        max_retries = options.get("max_retries", 1)

        for _ in range(max_retries + 1):
            try:
                # 设置代理
                try:
                    proxy = proxy or random.choice(options.get("proxies", []))
                    self.set_proxy(proxy)
                except (IndexError, KeyError):
                    pass

                # 构建请求头
                headers = dict(self.headers)

                # 随机UA
                if self.agents:
                    headers["User-Agent"] = random.choice(self.agents)

                # WAF绕过头
                if self.waf_bypass:
                    method = options.get("http_method", "GET")
                    headers.update(WAFBypass.get_waf_bypass_headers(method))

                # WAF路径绕过（使用原始path，确保重试时一致）
                request_path = original_path
                if self.waf_bypass:
                    request_path = WAFBypass.apply_path_bypass(request_path)
                    url = safequote(self._url + request_path if self._url else request_path)
                else:
                    url = safequote(self._url + original_path if self._url else original_path)

                # WAF垃圾参数
                if self.waf_bypass and random.random() > 0.6:
                    url = WAFBypass.add_junk_params(url)

                # 发送请求
                method = options.get("http_method", "GET").upper()
                response = self.session.request(
                    method,
                    url,
                    headers=headers,
                    data=options.get("data"),
                    allow_redirects=options.get("follow_redirects", False),
                    timeout=options.get("timeout", 10),
                    stream=True,
                )

                response = Response(response)

                log_msg = f'"{method} {response.url}" {response.status} - {response.length}B'
                if response.redirect:
                    log_msg += f" - LOCATION: {response.redirect}"
                logger.info(log_msg)

                return response

            except Exception as e:
                logger.debug(str(e))

                if "ProxyError" in str(e):
                    err_msg = f"Error with the proxy: {proxy}"
                    proxies = options.get("proxies", [])
                    if proxy in proxies and len(proxies) > 1:
                        proxies.remove(proxy)
                elif "ConnectionError" in str(e):
                    err_msg = f"Cannot connect to: {urlparse(url).netloc}"
                elif "Timeout" in str(e):
                    err_msg = f"Request timeout: {url}"
                else:
                    err_msg = f"Request error: {url}"

        raise RequestException(err_msg)

    def is_rate_exceeded(self):
        max_rate = options.get("max_rate", 0)
        return self._rate >= max_rate > 0

    def decrease_rate(self):
        self._rate -= 1

    def increase_rate(self):
        self._rate += 1
        timer = threading.Timer(1, self.decrease_rate)
        timer.daemon = True
        timer.start()

    @property
    @cached(RATE_UPDATE_DELAY)
    def rate(self):
        return self._rate
