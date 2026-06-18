# -*- coding: utf-8 -*-
"""


异常类定义
"""


class DirsearchBaseException(Exception):
    """基础异常"""
    pass


class RequestException(DirsearchBaseException):
    """请求异常"""
    pass


class InvalidURLException(DirsearchBaseException):
    """无效URL异常"""
    pass


class SkipTargetInterrupt(DirsearchBaseException):
    """跳过目标中断"""
    pass


class QuitInterrupt(DirsearchBaseException):
    """退出中断"""
    pass


class FailedDependenciesInstallation(DirsearchBaseException):
    """依赖安装失败"""
    pass
