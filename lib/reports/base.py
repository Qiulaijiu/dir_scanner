# -*- coding: utf-8 -*-
"""
报告基类
"""

import os
from lib.core.decorators import locked
from lib.utils.file import FileUtils


class FileBaseReport:
    """报告基类"""

    def __init__(self, output_file):
        self.output_file = output_file
        self._is_first = True

        # 创建报告目录
        directory = os.path.dirname(output_file)
        if directory:
            FileUtils.create_dir(directory)

    @locked
    def save(self, entries):
        """保存报告"""
        with open(self.output_file, "w", encoding="utf-8") as f:
            content = self.generate(entries)
            if isinstance(content, list):
                f.write("\n".join(content))
            else:
                f.write(content)

    def generate(self, entries):
        """生成报告内容（子类实现）"""
        raise NotImplementedError
