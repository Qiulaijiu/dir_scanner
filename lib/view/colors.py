# -*- coding: utf-8 -*-
"""
颜色处理 - dir_scanner专用配色方案
与dirsearch区分：使用更鲜艳的颜色和不同的配色逻辑
"""

import sys
import re

# ANSI颜色代码 - 扩展颜色
COLORS = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
    "bright_white": "\033[97m",
    "reset": "\033[0m",
}

STYLES = {
    "normal": "\033[0m",
    "bright": "\033[1m",
    "dim": "\033[2m",
    "italic": "\033[3m",
    "underline": "\033[4m",
    "reset": "\033[0m",
}

_enabled = True


def set_color(msg, fore="none", back="none", style="normal"):
    """设置文字颜色"""
    if not _enabled:
        return msg

    result = ""
    if fore in COLORS:
        result += COLORS[fore]
    if back in COLORS:
        result += COLORS[back].replace("[3", "[4").replace("[9", "[10")
    if style in STYLES:
        result += STYLES[style]

    result += msg
    result += COLORS["reset"]
    return result


def clean_color(msg):
    """去除ANSI颜色代码"""
    return re.sub(r"\033\[[0-9;]*m", "", msg)


def disable_color():
    """禁用颜色"""
    global _enabled
    _enabled = False
