# -*- coding: utf-8 -*-
"""
通用工具函数
"""

import re
import string


def safequote(string_):
    """URL编码，保留标点字符"""
    from urllib.parse import quote
    return quote(string_, safe=string.punctuation)


def lstrip_once(string, pattern):
    """只去除一次前缀"""
    if string.startswith(pattern):
        return string[len(pattern):]
    return string


def rstrip_once(string, pattern):
    """只去除一次后缀"""
    if string.endswith(pattern):
        return string[:-len(pattern)]
    return string


def get_valid_filename(string):
    """替换Windows非法文件名字符"""
    invalid_chars = ('"', "*", "<", ">", "?", "\\", "|", "/", ":")
    for ch in invalid_chars:
        string = string.replace(ch, "_")
    return string


def human_size(num):
    """将字节数转换为人类可读格式"""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num) < 1024.0:
            return f"{num:.1f}{unit}"
        num /= 1024.0
    return f"{num:.1f}PB"


def is_binary(bytes_):
    """判断内容是否为二进制"""
    text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7F})
    return bool(bytes_.translate(None, text_chars))


def escape_csv(text):
    """CSV注入防护"""
    if text and text[0] in ("+", "-", "=", "@"):
        return "'" + text
    return text
