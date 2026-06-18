# -*- coding: utf-8 -*-
"""
CSV报告
"""

from lib.reports.base import FileBaseReport
from lib.utils.common import escape_csv


class CSVReport(FileBaseReport):
    """CSV格式报告"""

    def generate(self, entries):
        lines = ["URL,Status,Size,Content-Type,Redirect"]

        for entry in entries:
            url = escape_csv(entry.url)
            content_type = escape_csv(entry.type)
            redirect = escape_csv(entry.redirect) if entry.redirect else ""
            lines.append(f"{url},{entry.status},{entry.length},{content_type},{redirect}")

        return lines
