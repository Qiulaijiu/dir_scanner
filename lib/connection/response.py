# -*- coding: utf-8 -*-
"""
HTTP响应封装
"""

import re

from lib.core.settings import DEFAULT_ENCODING, ITER_CHUNK_SIZE, MAX_RESPONSE_SIZE
from lib.core.structures import CaseInsensitiveDict
from lib.parse.url import clean_path, parse_path
from lib.utils.common import is_binary


class Response:
    """HTTP响应对象"""

    def __init__(self, response):
        self.url = response.url
        raw_path = parse_path(response.url)
        # 规范化路径，去除多余的斜杠
        self.full_path = re.sub(r"/+", "/", raw_path) if raw_path else raw_path
        self.path = clean_path(self.full_path)
        self.status = response.status_code
        self.headers = CaseInsensitiveDict(response.headers)
        self.redirect = self.headers.get("location", "")
        self.history = [res.url for res in response.history] if hasattr(response, 'history') else []
        self.content = ""
        self.body = b""
        self._title = None

        try:
            for chunk in response.iter_content(chunk_size=ITER_CHUNK_SIZE):
                self.body += chunk
                if len(self.body) >= MAX_RESPONSE_SIZE:
                    break
                if "content-length" in self.headers and is_binary(self.body):
                    break
        except Exception:
            pass

        if not is_binary(self.body):
            # 从Content-Type头检测编码
            content_type = self.headers.get("content-type", "")
            charset = None
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].split(";")[0].strip()

            # 尝试多种编码解码
            for encoding in [charset, response.encoding, "utf-8", "gbk", "gb2312", "latin-1"]:
                if not encoding:
                    continue
                try:
                    self.content = self.body.decode(encoding, errors="strict")
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            else:
                self.content = self.body.decode("utf-8", errors="replace")

    @property
    def title(self):
        """提取页面标题"""
        if self._title is None:
            self._title = ""
            if self.content:
                match = re.search(r"<title[^>]*>(.*?)</title>", self.content, re.IGNORECASE | re.DOTALL)
                if match:
                    title = match.group(1).strip()
                    title = re.sub(r"\s+", " ", title)
                    if len(title) > 60:
                        title = title[:57] + "..."
                    self._title = title
        return self._title

    @property
    def type(self):
        if "content-type" in self.headers:
            return self.headers.get("content-type").split(";")[0]
        return "unknown"

    @property
    def length(self):
        try:
            return int(self.headers.get("content-length"))
        except (TypeError, ValueError):
            return len(self.body)

    def __hash__(self):
        return hash(self.body)

    def __eq__(self, other):
        if not isinstance(other, Response):
            return False
        return (self.status, self.body, self.redirect) == (
            other.status,
            other.body,
            other.redirect,
        )
