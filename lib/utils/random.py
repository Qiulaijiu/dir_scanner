# -*- coding: utf-8 -*-
"""
随机字符串生成
"""

import random
import string


def rand_string(length=6, omit=None):
    """生成随机字符串"""
    chars = string.ascii_lowercase + string.digits

    while True:
        result = "".join(random.choices(chars, k=length))
        if result != omit:
            return result
