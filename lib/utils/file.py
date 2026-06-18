# -*- coding: utf-8 -*-
"""
文件工具
"""

import os


class File:
    """文件对象"""

    def __init__(self, *path_components):
        self._path = os.path.join(*path_components)

    @property
    def path(self):
        return self._path

    def exists(self):
        return os.path.exists(self._path)

    def can_read(self):
        return os.access(self._path, os.R_OK)

    def can_write(self):
        return os.access(self._path, os.W_OK)

    def read(self):
        with open(self._path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def get_lines(self):
        with open(self._path, "r", encoding="utf-8", errors="ignore") as f:
            return [line.strip() for line in f if line.strip()]


class FileUtils:
    """文件工具类"""

    @staticmethod
    def build_path(*path_components):
        return os.path.join(*path_components)

    @staticmethod
    def get_abs_path(file_name):
        return os.path.abspath(file_name)

    @staticmethod
    def exists(file_name):
        return os.path.exists(file_name)

    @staticmethod
    def can_read(file_name):
        return os.path.isfile(file_name) and os.access(file_name, os.R_OK)

    @staticmethod
    def can_write(path):
        if os.path.isfile(path):
            return os.access(path, os.W_OK)
        directory = os.path.dirname(path) or "."
        return os.access(directory, os.W_OK)

    @staticmethod
    def read(file_name):
        with open(file_name, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    @staticmethod
    def get_lines(file_name):
        try:
            with open(file_name, "r", encoding="utf-8", errors="ignore") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception:
            return []

    @staticmethod
    def is_dir(path):
        return os.path.isdir(path)

    @staticmethod
    def is_file(path):
        return os.path.isfile(path)

    @staticmethod
    def parent(path, depth=1):
        for _ in range(depth):
            path = os.path.dirname(path)
        return path

    @staticmethod
    def create_dir(directory):
        os.makedirs(directory, exist_ok=True)

    @staticmethod
    def write_lines(file_name, lines, overwrite=False):
        mode = "w" if overwrite else "a"
        with open(file_name, mode, encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")
