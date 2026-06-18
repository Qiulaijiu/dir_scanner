# -*- coding: utf-8 -*-
"""
XML报告
"""

import time
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

from lib.reports.base import FileBaseReport


class XMLReport(FileBaseReport):
    """XML格式报告"""

    def generate(self, entries):
        root = Element("dir_scanner_report")

        # 元信息
        meta = SubElement(root, "meta")
        SubElement(meta, "tool").text = "dir_scanner"
        SubElement(meta, "version").text = "1.0.0"
        SubElement(meta, "date").text = time.strftime("%Y-%m-%d %H:%M:%S")
        SubElement(meta, "total_results").text = str(len(entries))

        # 结果
        results = SubElement(root, "results")
        for entry in entries:
            item = SubElement(results, "result")
            SubElement(item, "url").text = entry.url
            SubElement(item, "path").text = "/" + entry.full_path
            SubElement(item, "status").text = str(entry.status)
            SubElement(item, "length").text = str(entry.length)
            SubElement(item, "content_type").text = entry.type
            if entry.redirect:
                SubElement(item, "redirect").text = entry.redirect

        xml_str = tostring(root, encoding="unicode")
        return parseString(xml_str).toprettyxml(indent="  ")
