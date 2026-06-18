# -*- coding: utf-8 -*-
"""
全局设置和常量
"""

import os
import sys

VERSION = "1.0.0"

BANNER = r"""
  ____  _      _
 |  _ \(_) ___| | __
 | | | | |/ __| |/ /
 | |_| | | (__|   <
 |____/|_|\___|_|\_\  v{}
    SRC Directory Scanner
""".format(VERSION)

SCRIPT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

IS_WINDOWS = sys.platform in ("win32", "msys")

DEFAULT_ENCODING = "utf-8"

NEW_LINE = os.linesep

OUTPUT_FORMATS = ("plain", "json", "csv", "html", "xml")

COMMON_EXTENSIONS = ("php", "jsp", "asp", "aspx", "do", "action", "cgi", "html", "htm", "js")

DEFAULT_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
}

DEFAULT_TEST_PREFIXES = (".",)
DEFAULT_TEST_SUFFIXES = ("/",)

PROXY_SCHEMES = ("http://", "https://", "socks5://", "socks5h://", "socks4://", "socks4a://")

STANDARD_PORTS = {"http": 80, "https": 443}

MAX_CONSECUTIVE_REQUEST_ERRORS = 75

PAUSING_WAIT_TIMEOUT = 7

RATE_UPDATE_DELAY = 0.15

ITER_CHUNK_SIZE = 1024 * 1024

MAX_RESPONSE_SIZE = 80 * 1024 * 1024

TEST_PATH_LENGTH = 6

WILDCARD_TEST_POINT_MARKER = "__WILDCARD_POINT__"

REFLECTED_PATH_MARKER = "__REFLECTED_PATH__"

EXTENSION_TAG = "%ext%"

EXTENSION_RECOGNITION_REGEX = r"\w+([.][a-zA-Z0-9]{2,5}){1,3}~?$"

# WAF绕过相关
WAF_BYPASS_HEADERS = [
    "X-Forwarded-For",
    "X-Real-IP",
    "X-Originating-IP",
    "X-Remote-IP",
    "X-Client-IP",
    "X-Forwarded-Host",
    "True-Client-IP",
    "CF-Connecting-IP",
    "X-Forwarded-Server",
    "X-Host",
]

# SRC字典列表（不含通用字典dicc.txt）
SRC_WORDLISTS = [
    "API接口路径.txt",
    "Spring监控端点.txt",
    "Web文件.txt",
    "上传下载功能.txt",
    "其他路径.txt",
    "开发测试路径.txt",
    "敏感文件配置.txt",
    "数据库相关.txt",
    "模板变量路径.txt",
    "版本控制相关.txt",
    "目录遍历绕过.txt",
    "管理后台路径.txt",
    "编辑器路径.txt",
    "认证相关路径.txt",
    "配置系统路径.txt",
]

# 通用字典文件名
DEFAULT_WORDLIST = "dicc.txt"

# 爬虫相关常量
CRAWL_TAG = "[CRAWL]"

# HTML标签中可能包含路径的属性
HTML_LINK_ATTRS = (
    "href", "src", "action", "data-src", "data-href", "data-url",
    "content", "url", "poster", "background", "formaction",
)

# HTML标签名
HTML_LINK_TAGS = (
    "a", "form", "script", "link", "img", "iframe", "frame",
    "embed", "object", "source", "video", "audio", "track",
    "area", "base", "input", "button",
)

# JS中路径提取正则
JS_PATH_REGEXES = (
    r"""(?:"|')(/(?:[a-zA-Z0-9_\-./]+)?)\??[^"']*(?:"|')""",
    r"""(?:"|')(https?://[^"']+)(?:"|')""",
    r"""(?:path|url|href|src|action|endpoint|api)\s*[:=]\s*(?:"|')(/[^"']+)(?:"|')""",
    r"""(?:fetch|axios|ajax|get|post|put|delete)\s*\(\s*(?:"|')(/[^"']+)(?:"|')""",
)

# HTML注释中的路径提取正则
COMMENT_PATH_REGEX = r"""<!--[\s\S]*?-->"""

# robots.txt User-Agent 段落匹配
ROBOTS_USERAGENT_REGEX = r"(?i)^User-agent:\s*\*"

# robots.txt Disallow/Allow 匹配
ROBOTS_DIRECTIVE_REGEX = r"(?i)^(?:Disallow|Allow):\s*(.+)"

# sitemap.xml loc 匹配
SITEMAP_LOC_REGEX = r"<loc>\s*(.*?)\s*</loc>"

# 随机UA池
USER_AGENT_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]
