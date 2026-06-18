# -*- coding: utf-8 -*-
"""
日志模块
"""

import logging
import sys

logger = logging.getLogger("dir_scanner")
logger.setLevel(logging.DEBUG)
logger.propagate = False

# 默认不输出到控制台，只在启用日志时输出
_null_handler = logging.NullHandler()
logger.addHandler(_null_handler)

_enabled = False


def enable_logging(log_file=None):
    global _enabled
    _enabled = True

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s"))
        logger.addHandler(file_handler)


def is_enabled():
    return _enabled
