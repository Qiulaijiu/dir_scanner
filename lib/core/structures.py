# -*- coding: utf-8 -*-
"""
数据结构
"""

from collections import OrderedDict


class OrderedSet:
    """有序集合"""

    def __init__(self):
        self._dict = OrderedDict()

    def add(self, item):
        self._dict[item] = None

    def discard(self, item):
        self._dict.pop(item, None)

    def __contains__(self, item):
        return item in self._dict

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def __getitem__(self, index):
        return list(self._dict.keys())[index]


class CaseInsensitiveDict(dict):
    """大小写不敏感的字典"""

    def __init__(self, *args, **kwargs):
        super().__init__()
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    def __setitem__(self, key, value):
        super().__setitem__(key.lower() if isinstance(key, str) else key, value)

    def __getitem__(self, key):
        return super().__getitem__(key.lower() if isinstance(key, str) else key)

    def get(self, key, default=None):
        return super().get(key.lower() if isinstance(key, str) else key, default)

    def __contains__(self, key):
        return super().__contains__(key.lower() if isinstance(key, str) else key)
