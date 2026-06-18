# -*- coding: utf-8 -*-
"""
HTML报告
"""

import time

from lib.reports.base import FileBaseReport
from lib.utils.common import human_size


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>dir_scanner Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #eee; }}
        h1 {{ color: #00bcd4; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ padding: 8px 12px; text-align: left; border: 1px solid #333; }}
        th {{ background: #333; color: #00bcd4; }}
        tr:nth-child(even) {{ background: #222; }}
        tr:hover {{ background: #2a2a2a; }}
        .status-2xx {{ color: #4caf50; }}
        .status-3xx {{ color: #00bcd4; }}
        .status-4xx {{ color: #ff9800; }}
        .status-5xx {{ color: #f44336; }}
        .info {{ margin: 20px 0; color: #888; }}
        a {{ color: #00bcd4; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>dir_scanner Scan Report</h1>
    <div class="info">
        <p>Generated: {date}</p>
        <p>Total Results: {count}</p>
    </div>
    <table>
        <tr>
            <th>#</th>
            <th>Status</th>
            <th>Size</th>
            <th>URL</th>
            <th>Content-Type</th>
            <th>Redirect</th>
        </tr>
        {rows}
    </table>
</body>
</html>"""

ROW_TEMPLATE = """        <tr>
            <td>{index}</td>
            <td class="{status_class}">{status}</td>
            <td>{size}</td>
            <td><a href="{url}" target="_blank">{path}</a></td>
            <td>{content_type}</td>
            <td>{redirect}</td>
        </tr>"""


class HTMLReport(FileBaseReport):
    """HTML格式报告"""

    def generate(self, entries):
        rows = []
        for i, entry in enumerate(entries, 1):
            status_class = f"status-{str(entry.status)[0]}xx"
            size = human_size(entry.length)
            redirect = entry.redirect or ""

            rows.append(ROW_TEMPLATE.format(
                index=i,
                status_class=status_class,
                status=entry.status,
                size=size,
                url=entry.url,
                path="/" + entry.full_path,
                content_type=entry.type,
                redirect=redirect,
            ))

        return HTML_TEMPLATE.format(
            date=time.strftime("%Y-%m-%d %H:%M:%S"),
            count=len(entries),
            rows="\n".join(rows),
        )
