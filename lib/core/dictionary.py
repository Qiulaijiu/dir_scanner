# -*- coding: utf-8 -*-
"""
字典加载和处理模块
支持加载SRC字典目录下的所有txt文件
支持SRC模式和通用模式切换
"""

import os
import re
from pathlib import Path

from lib.core.data import options
from lib.core.decorators import locked
from lib.core.settings import (
    EXTENSION_TAG,
    EXTENSION_RECOGNITION_REGEX,
    SCRIPT_PATH,
    SRC_WORDLISTS,
    DEFAULT_WORDLIST,
)
from lib.core.structures import OrderedSet
from lib.utils.file import FileUtils


def get_blacklists():
    """获取黑名单状态码配置"""
    blacklists = {}
    for status in [400, 403, 500]:
        blacklist_file = FileUtils.build_path(SCRIPT_PATH, "db", f"{status}_blacklist.txt")
        if FileUtils.can_read(blacklist_file):
            blacklists[status] = Dictionary(files=[blacklist_file], is_blacklist=True)
    return blacklists


def get_wordlist_files(wordlist_dir, mode="default", categories=None):
    """
    获取字典文件列表

    Args:
        wordlist_dir: 字典目录
        mode: 模式选择
            - "default": 默认使用通用字典(dicc.txt)
            - "src": SRC模式，使用全部SRC字典
            - "src-select": SRC选择模式，使用指定的SRC类别
        categories: SRC类别列表（仅src-select模式使用）

    Returns:
        字典文件路径列表
    """
    wordlist_path = Path(wordlist_dir)
    files = []

    if not wordlist_path.exists():
        return files

    if mode == "src":
        # SRC模式：加载所有SRC字典
        for filename in SRC_WORDLISTS:
            filepath = wordlist_path / filename
            if filepath.exists():
                files.append(str(filepath))

    elif mode == "src-select":
        # SRC选择模式：加载指定的SRC类别
        for filename in SRC_WORDLISTS:
            category = filename.replace(".txt", "")
            if categories and category in categories:
                filepath = wordlist_path / filename
                if filepath.exists():
                    files.append(str(filepath))

    else:
        # 默认模式：使用通用字典
        default_file = wordlist_path / DEFAULT_WORDLIST
        if default_file.exists():
            files.append(str(default_file))

    return files


def list_all_categories(wordlist_dir):
    """列出所有可用类别（区分SRC和通用）"""
    wordlist_path = Path(wordlist_dir)
    categories = {
        "src": [],
        "default": [],
    }

    if not wordlist_path.exists():
        return categories

    for txt_file in sorted(wordlist_path.glob("*.txt")):
        count = sum(1 for _ in open(txt_file, encoding="utf-8", errors="ignore"))
        name = txt_file.stem

        if name in [w.replace(".txt", "") for w in SRC_WORDLISTS]:
            categories["src"].append((name, count))
        elif name == DEFAULT_WORDLIST.replace(".txt", ""):
            categories["default"].append((name, count))
        else:
            categories["default"].append((name, count))

    return categories


class Dictionary:
    """字典类"""

    def __init__(self, **kwargs):
        self._index = 0
        self._items = self.generate(**kwargs)

    @property
    def index(self):
        return self._index

    @locked
    def __next__(self):
        try:
            path = self._items[self._index]
        except IndexError:
            raise StopIteration
        self._index += 1
        return path

    def __contains__(self, item):
        return item in self._items

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def generate(self, files=[], is_blacklist=False, categories=None, wordlist_dir=None, mode="default"):
        """生成字典列表"""
        wordlist = OrderedSet()
        re_ext_tag = re.compile(EXTENSION_TAG, re.IGNORECASE)

        # 如果指定了字典目录，根据模式加载文件
        if wordlist_dir:
            if mode in ("src", "src-select"):
                files = get_wordlist_files(wordlist_dir, mode=mode, categories=categories)
            elif not files:
                files = get_wordlist_files(wordlist_dir, mode="default")

        for dict_file in files:
            for line in FileUtils.get_lines(dict_file):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # 去掉开头的/
                if line.startswith("/"):
                    line = line[1:]

                if not self.is_valid(line):
                    continue

                # 处理%EXT%标签
                if EXTENSION_TAG in line.lower():
                    for extension in options.get("extensions", []):
                        newline = re_ext_tag.sub(extension, line)
                        wordlist.add(newline)
                else:
                    wordlist.add(line)

                    if is_blacklist:
                        continue

                    # 强制扩展名
                    if (options.get("force_extensions", False)
                            and "." not in line
                            and not line.endswith("/")):
                        wordlist.add(line + "/")
                        for extension in options.get("extensions", []):
                            wordlist.add(f"{line}.{extension}")

        # 应用前缀和后缀
        if not is_blacklist:
            altered_wordlist = OrderedSet()
            prefixes = options.get("prefixes", [])
            suffixes = options.get("suffixes", [])

            for path in wordlist:
                for pref in prefixes:
                    if not path.startswith(("/", pref)):
                        altered_wordlist.add(pref + path)
                for suff in suffixes:
                    if not path.endswith(("/", suff)) and "?" not in path and "#" not in path:
                        altered_wordlist.add(path + suff)

            if altered_wordlist:
                wordlist = altered_wordlist

        # 大小写转换
        if options.get("lowercase", False):
            return list(map(str.lower, wordlist))
        elif options.get("uppercase", False):
            return list(map(str.upper, wordlist))
        elif options.get("capitalization", False):
            return list(map(str.capitalize, wordlist))
        else:
            return list(wordlist)

    def _load_from_directory(self, wordlist_dir, categories=None):
        """从目录加载字典文件"""
        files = []
        wordlist_path = Path(wordlist_dir)

        if not wordlist_path.exists():
            return files

        for txt_file in sorted(wordlist_path.glob("*.txt")):
            category = txt_file.stem
            if categories and category not in categories:
                continue
            files.append(str(txt_file))

        return files

    def is_valid(self, path):
        """检查路径是否有效"""
        if not path or path.startswith("#"):
            return False

        # 检查排除的扩展名
        exclude_extensions = options.get("exclude_extensions", [])
        if exclude_extensions:
            for ext in exclude_extensions:
                if path.endswith(f".{ext}"):
                    return False

        return True

    def reset(self):
        """重置索引"""
        self._index = 0


def load_wordlists_from_directory(wordlist_dir, categories=None):
    """从目录加载字典文件，返回 {类别: [路径列表]}"""
    result = {}
    wordlist_path = Path(wordlist_dir)

    if not wordlist_path.exists():
        return result

    for txt_file in sorted(wordlist_path.glob("*.txt")):
        category = txt_file.stem
        if categories and category not in categories:
            continue

        lines = []
        with open(txt_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    lines.append(line)

        if lines:
            result[category] = lines

    return result


def list_categories(wordlist_dir):
    """列出所有可用类别（保持向后兼容）"""
    wordlist_path = Path(wordlist_dir)
    categories = []

    if not wordlist_path.exists():
        return categories

    for txt_file in sorted(wordlist_path.glob("*.txt")):
        count = sum(1 for _ in open(txt_file, encoding="utf-8", errors="ignore"))
        categories.append((txt_file.stem, count))

    return categories
