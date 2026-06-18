# -*- coding: utf-8 -*-
"""
纯文本报告
"""

from lib.reports.base import FileBaseReport
from lib.utils.common import human_size


class PlainTextReport(FileBaseReport):
    """纯文本格式报告"""

    def generate(self, entries):
        lines = []
        for entry in entries:
            length = human_size(entry.length).rjust(6)
            line = f"{entry.status}  {length}  /{entry.full_path}"
            if entry.redirect:
                line += f"  ->  {entry.redirect}"
            lines.append(line)
        return lines
