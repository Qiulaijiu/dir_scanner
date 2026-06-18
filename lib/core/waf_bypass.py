# -*- coding: utf-8 -*-
"""
WAF绕过模块
提供多种绕过技术：随机UA、IP伪造、路径混淆、垃圾参数等
"""

import random
from lib.core.settings import WAF_BYPASS_HEADERS, USER_AGENT_POOL


class WAFBypass:
    """WAF绕过技术集合"""

    @staticmethod
    def get_random_ua() -> str:
        """获取随机User-Agent"""
        return random.choice(USER_AGENT_POOL)

    @staticmethod
    def random_ip_headers() -> dict:
        """随机伪造IP来源头"""
        ip = f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        headers = {}
        count = random.randint(1, 4)
        chosen = random.sample(WAF_BYPASS_HEADERS, min(count, len(WAF_BYPASS_HEADERS)))
        for h in chosen:
            headers[h] = ip
        return headers

    @staticmethod
    def case_mix_path(path: str) -> str:
        """路径大小写混淆"""
        result = []
        for ch in path:
            if ch.isalpha():
                result.append(ch.upper() if random.random() > 0.5 else ch.lower())
            else:
                result.append(ch)
        return "".join(result)

    @staticmethod
    def add_junk_params(url: str) -> str:
        """添加垃圾参数消耗WAF算力"""
        junk_keys = ["_", "t", "ts", "time", "r", "rand", "v", "ver", "cb"]
        junk_params = []
        count = random.randint(1, 3)
        for _ in range(count):
            k = random.choice(junk_keys)
            v = random.randint(100000, 9999999)
            junk_params.append(f"{k}={v}")
        sep = "&" if "?" in url else "?"
        return url + sep + "&".join(junk_params)

    @staticmethod
    def add_decoy_headers() -> dict:
        """添加迷惑性请求头"""
        headers = {}
        decoys = [
            ("Accept-Language", random.choice([
                "zh-CN,zh;q=0.9,en;q=0.8",
                "en-US,en;q=0.9,zh-CN;q=0.8",
                "zh-TW,zh;q=0.9,en-US;q=0.8",
                "ja,en-US;q=0.9,en;q=0.8",
            ])),
            ("Accept-Encoding", "gzip, deflate, br"),
            ("Cache-Control", random.choice(["no-cache", "max-age=0", "no-store"])),
            ("Pragma", "no-cache"),
            ("Sec-Fetch-Dest", "document"),
            ("Sec-Fetch-Mode", "navigate"),
            ("Sec-Fetch-Site", "none"),
            ("Sec-Fetch-User", "?1"),
            ("Upgrade-Insecure-Requests", "1"),
        ]
        for k, v in decoys:
            if random.random() > 0.4:
                headers[k] = v
        return headers

    @staticmethod
    def path_with_fragments(path: str) -> str:
        """路径片段混淆: 添加分号、%09、%20等"""
        techniques = [
            lambda p: p + ";" + random.choice(["", "a", ".js"]),
            lambda p: p + "%09",
            lambda p: p + "%20",
            lambda p: p + "%00",
            lambda p: p + "?#" + str(random.randint(1, 99)),
            lambda p: p + "/.",
            lambda p: p + "..;/",
        ]
        if random.random() > 0.5:
            return random.choice(techniques)(path)
        return path

    @staticmethod
    def http_method_override(method: str) -> dict:
        """HTTP方法覆盖头"""
        headers = {}
        if random.random() > 0.5:
            headers["X-HTTP-Method-Override"] = method
        if random.random() > 0.7:
            headers["X-HTTP-Method"] = method
        return headers

    @staticmethod
    def get_waf_bypass_headers(method: str = "GET") -> dict:
        """获取所有WAF绕过头"""
        headers = {}
        headers["User-Agent"] = WAFBypass.get_random_ua()
        headers.update(WAFBypass.random_ip_headers())
        headers.update(WAFBypass.add_decoy_headers())
        if method == "GET" and random.random() > 0.7:
            headers.update(WAFBypass.http_method_override(method))
        return headers

    @staticmethod
    def apply_path_bypass(path: str) -> str:
        """应用路径绕过技术"""
        path = WAFBypass.path_with_fragments(path)
        path = WAFBypass.case_mix_path(path)
        return path
