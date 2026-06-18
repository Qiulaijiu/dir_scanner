# -*- coding: utf-8 -*-
"""
动态内容差异分析
"""

import difflib
import re


class DynamicContentParser:
    """动态内容解析器"""

    def __init__(self, content1, content2):
        self._static = content1 == content2
        self._content1 = content1
        self._content2 = content2
        self._patterns = None

        if not self._static:
            self._generate_patterns()

    def _generate_patterns(self):
        """从两个内容中提取稳定模式"""
        words1 = self._content1.split()
        words2 = self._content2.split()

        differ = difflib.Differ()
        diff = list(differ.compare(words1, words2))

        self._patterns = []
        for line in diff:
            if line.startswith("  "):  # 稳定部分
                self._patterns.append(re.escape(line[2:]))

    def compare_to(self, content):
        """比较内容是否与基准相同（是通配符）"""
        if self._static:
            return self._content1 == content

        if not self._patterns:
            return False

        # 使用SequenceMatcher计算相似度
        ratio = difflib.SequenceMatcher(
            None, self._content1, content
        ).ratio()

        return ratio > 0.98


def generate_matching_regex(string1, string2):
    """从两个字符串生成匹配正则表达式"""
    # 找共同前缀
    prefix = ""
    for c1, c2 in zip(string1, string2):
        if c1 == c2:
            prefix += c1
        else:
            break

    # 找共同后缀
    suffix = ""
    for c1, c2 in zip(reversed(string1[len(prefix):]), reversed(string2[len(prefix):])):
        if c1 == c2:
            suffix = c1 + suffix
        else:
            break

    # 生成正则
    pattern = "^" + re.escape(prefix) + "(.*)" + re.escape(suffix) + "$"
    return pattern
