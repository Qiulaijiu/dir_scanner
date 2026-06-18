# -*- coding: utf-8 -*-
"""
简单报告
"""

from lib.reports.base import FileBaseReport


class SimpleReport(FileBaseReport):
    """简单URL列表报告"""

    def generate(self, entries):
        return [f"/{entry.full_path}" for entry in entries]
