# -*- coding: utf-8 -*-
"""
爬虫模块 - 从响应中提取路径
支持: HTML标签、JS文件、robots.txt、sitemap.xml、HTML注释
"""

import re
from urllib.parse import urljoin, urlparse, urlunparse

from lib.core.logger import logger
from lib.core.settings import (
    COMMENT_PATH_REGEX,
    HTML_LINK_ATTRS,
    HTML_LINK_TAGS,
    JS_PATH_REGEXES,
    ROBOTS_DIRECTIVE_REGEX,
    SITEMAP_LOC_REGEX,
)

# 预编译正则
_re_html_tag = re.compile(
    r"<\s*(?:" + "|".join(HTML_LINK_TAGS) + r")\b[^>]*?>",
    re.IGNORECASE | re.DOTALL,
)
_re_attr = re.compile(
    r"""(?<![:\w])""" + r"""(?:""" + "|".join(HTML_LINK_ATTRS) + r""")\s*=\s*(?:"([^"]*)"|'([^']*)')""",
    re.IGNORECASE,
)
_re_comment = re.compile(COMMENT_PATH_REGEX, re.DOTALL)
_re_js_paths = [re.compile(p) for p in JS_PATH_REGEXES]
_re_robots_directive = re.compile(ROBOTS_DIRECTIVE_REGEX, re.IGNORECASE)
_re_sitemap_loc = re.compile(SITEMAP_LOC_REGEX, re.IGNORECASE)

# 排除的文件扩展名
_EXCLUDE_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "svg", "ico", "webp", "bmp", "tiff",
    "css", "map", "woff", "woff2", "ttf", "eot", "otf",
    "mp3", "mp4", "avi", "mov", "wmv", "flv", "webm",
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "zip", "rar", "tar", "gz", "7z", "bz2",
}


class Crawler:
    """从HTTP响应中提取路径的爬虫"""

    def __init__(self, base_url, requester):
        self.base_url = base_url
        self.requester = requester
        parsed = urlparse(base_url)
        self.base_host = parsed.netloc.lower()
        self.base_scheme = parsed.scheme

    def crawl_response(self, response):
        """
        从响应中提取路径
        返回: list[str] 规范化后的路径列表
        """
        paths = set()

        content_type = response.type or ""
        content = response.content

        if not content:
            return []

        if "javascript" in content_type or response.path.endswith(".js"):
            paths.update(self.crawl_js(content))
        elif "html" in content_type or "text" in content_type:
            paths.update(self._extract_from_html(content))
            paths.update(self._extract_from_comments(content))
            # 从内联JS中提取路径（Vue/React等SPA框架）
            paths.update(self._extract_from_inline_js(content))

        # 过滤和规范化
        result = []
        for path in paths:
            normalized = self._normalize_path(path, response.url)
            if normalized:
                result.append(normalized)

        return result

    def crawl_js(self, content):
        """从JavaScript内容中提取路径"""
        paths = set()
        for regex in _re_js_paths:
            for match in regex.finditer(content):
                url = match.group(1) if match.lastindex else match.group(0)
                if url and len(url) > 1:
                    paths.add(url)
        return paths

    def crawl_robots(self):
        """
        请求并解析 robots.txt
        返回: list[str] 路径列表
        """
        paths = []
        try:
            robots_url = self.base_url.rstrip("/") + "/robots.txt"
            response = self.requester.request("robots.txt")
            if response.status == 200 and response.content:
                for line in response.content.splitlines():
                    line = line.strip()
                    match = _re_robots_directive.match(line)
                    if match:
                        path = match.group(1).strip()
                        if path and path != "/" and "*" not in path:
                            if path.startswith("/"):
                                paths.append(path)
                            else:
                                paths.append("/" + path)
                logger.info(f"robots.txt: found {len(paths)} paths")
        except Exception as e:
            logger.debug(f"robots.txt error: {e}")
        return paths

    def crawl_sitemap(self):
        """
        请求并解析 sitemap.xml
        返回: list[str] 路径列表
        """
        paths = []
        try:
            response = self.requester.request("sitemap.xml")
            if response.status == 200 and response.content:
                for match in _re_sitemap_loc.finditer(response.content):
                    url = match.group(1).strip()
                    normalized = self._normalize_path(url, self.base_url)
                    if normalized:
                        paths.append(normalized)
                logger.info(f"sitemap.xml: found {len(paths)} paths")
        except Exception as e:
            logger.debug(f"sitemap.xml error: {e}")
        return paths

    def _extract_from_html(self, content):
        """从HTML中提取所有链接属性值"""
        paths = set()
        for tag_match in _re_html_tag.finditer(content):
            tag = tag_match.group(0)
            for attr_match in _re_attr.finditer(tag):
                url = attr_match.group(1) or attr_match.group(2)
                if url and not url.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
                    paths.add(url)
        return paths

    def _extract_from_comments(self, content):
        """从HTML注释中提取路径"""
        paths = set()
        for match in _re_comment.finditer(content):
            comment = match.group(0)
            # 提取注释中看起来像路径的内容
            for path_match in re.finditer(r"""(/[\w\-./]+\w)""", comment):
                path = path_match.group(1)
                if len(path) > 2 and "." not in path.split("/")[-1]:
                    paths.add(path)
        return paths

    def _extract_from_inline_js(self, content):
        """从HTML内联JS和JS调用中提取路径（支持Vue/React等SPA框架）"""
        paths = set()
        # 从 <script> 标签中提取
        for script_match in re.finditer(r"<script[^>]*>(.*?)</script>", content, re.DOTALL | re.IGNORECASE):
            script = script_match.group(1)
            self._extract_js_paths(script, paths)

        # 从HTML属性中的JS调用提取（如 href="javascript:navPage('./path')"）
        self._extract_js_paths(content, paths)
        return paths

    def _extract_js_paths(self, text, paths):
        """从JS代码中提取路径"""
        for pattern in [
            r"""navPage\(\s*['"](\./[^'"]+)['"]\s*\)""",
            r"""window\.location\s*[=.]\s*['"]([^'"]+)['"]\s*""",
            r"""router\.push\(\s*['"]([^'"]+)['"]\s*\)""",
            r"""location\.href\s*=\s*['"]([^'"]+)['"]\s*""",
            r"""['"](\./[^'"]+\.html)['"]\s*""",
            r"""['"](\./pages/[^'"]+)['"]\s*""",
        ]:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                url = m.group(1)
                if url and not url.startswith(("#", "mailto:", "tel:", "data:")):
                    # 排除包含JS模板语法的路径
                    if "'" not in url and '"' not in url and "+" not in url:
                        paths.add(url)

    def _normalize_path(self, url, context_url=None):
        """
        规范化URL为路径
        返回: str 路径 或 None（排除）
        """
        if not url:
            return None

        url = url.strip()

        # 处理相对URL
        if not url.startswith(("http://", "https://", "/")):
            base = context_url or self.base_url
            url = urljoin(base, url)

        parsed = urlparse(url)

        # 同源校验（绝对URL）
        if parsed.scheme and parsed.netloc:
            host = parsed.netloc.lower()
            if host != self.base_host:
                return None

        # 提取路径
        path = parsed.path
        if not path:
            return None

        # 确保以 / 开头
        if not path.startswith("/"):
            path = "/" + path

        # 排除JS模板残留和无效路径
        if any(ch in path for ch in ("'", '"', "+", ":", "{", "}", "$", "<", ">")):
            return None

        # 排除过短路径（<4字符，如 /div, /a）
        if len(path) < 4:
            return None

        # 排除纯变量名（无斜杠、无点号）
        if "/" not in path[1:] and "." not in path:
            return None

        # 排除静态资源
        ext = path.rsplit(".", 1)[-1].lower() if "." in path.split("/")[-1] else ""
        if ext in _EXCLUDE_EXTENSIONS:
            return None

        # 排除过长路径
        if len(path) > 200:
            return None

        return path
