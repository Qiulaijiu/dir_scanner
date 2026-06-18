# -*- coding: utf-8 -*-
"""
JSON报告
"""

import json
import time

from lib.reports.base import FileBaseReport


class JSONReport(FileBaseReport):
    """JSON格式报告"""

    def generate(self, entries):
        result = {
            "tool": "dir_scanner",
            "version": "1.0.0",
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": []
        }

        for entry in entries:
            item = {
                "url": entry.url,
                "path": "/" + entry.full_path,
                "status": entry.status,
                "length": entry.length,
                "content_type": entry.type,
            }
            if entry.redirect:
                item["redirect"] = entry.redirect
            if entry.history:
                item["history"] = entry.history

            result["results"].append(item)

        return json.dumps(result, indent=2, ensure_ascii=False)
