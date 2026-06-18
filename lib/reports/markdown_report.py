# -*- coding: utf-8 -*-
"""
Markdown报告
"""

import time

from lib.reports.base import FileBaseReport
from lib.utils.common import human_size


class MarkdownReport(FileBaseReport):
    """Markdown格式报告"""

    def generate(self, entries):
        lines = [
            "# dir_scanner Scan Report",
            "",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Results: {len(entries)}",
            "",
            "| # | Status | Size | URL | Content-Type | Redirect |",
            "|---|--------|------|-----|--------------|----------|",
        ]

        for i, entry in enumerate(entries, 1):
            size = human_size(entry.length)
            redirect = entry.redirect or ""
            lines.append(
                f"| {i} | {entry.status} | {size} | /{entry.full_path} | {entry.type} | {redirect} |"
            )

        return "\n".join(lines)
