# -*- coding: utf-8 -*-
"""
URL解析
"""

from urllib.parse import urlparse


def clean_path(path):
    """清理路径，去除查询字符串和DOM"""
    if "?" in path:
        path = path.split("?")[0]
    if "#" in path:
        path = path.split("#")[0]
    return path


def parse_path(url):
    """从URL中提取路径"""
    parsed = urlparse(url)
    return parsed.path
