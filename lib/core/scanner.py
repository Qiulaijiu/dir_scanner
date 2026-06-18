# -*- coding: utf-8 -*-
"""
响应分析器 - Wildcard检测
"""

import re
from urllib.parse import unquote

from lib.core.logger import logger
from lib.core.settings import (
    REFLECTED_PATH_MARKER,
    TEST_PATH_LENGTH,
    WILDCARD_TEST_POINT_MARKER,
)
from lib.parse.url import clean_path
from lib.utils.diff import generate_matching_regex, DynamicContentParser
from lib.utils.random import rand_string


class Scanner:
    """Wildcard检测器"""

    def __init__(self, requester, **kwargs):
        self.path = kwargs.get("path", "")
        self.tested = kwargs.get("tested", [])
        self.context = kwargs.get("context", "all cases")
        self.requester = requester
        self.response = None
        self.wildcard_redirect_regex = None
        self.setup()

    def setup(self):
        """生成wildcard响应信息"""
        first_path = self.path.replace(
            WILDCARD_TEST_POINT_MARKER,
            rand_string(TEST_PATH_LENGTH),
        )
        first_response = self.requester.request(first_path)
        self.response = first_response

        duplicate = self.get_duplicate(first_response)
        if duplicate:
            self.content_parser = duplicate.content_parser
            self.wildcard_redirect_regex = duplicate.wildcard_redirect_regex
            logger.debug(f'Skipped the second test for "{self.context}"')
            return

        second_path = self.path.replace(
            WILDCARD_TEST_POINT_MARKER,
            rand_string(TEST_PATH_LENGTH, omit=first_path),
        )
        second_response = self.requester.request(second_path)

        if first_response.redirect and second_response.redirect:
            self.wildcard_redirect_regex = self.generate_redirect_regex(
                clean_path(first_response.redirect),
                first_path,
                clean_path(second_response.redirect),
                second_path,
            )

        self.content_parser = DynamicContentParser(
            first_response.content, second_response.content
        )

    def get_duplicate(self, response):
        for category in self.tested:
            for tester in self.tested[category].values():
                if response == tester.response:
                    return tester
        return None

    def is_wildcard(self, response):
        """检查响应是否为wildcard"""
        if not self.response.content and not response.content:
            return self.response.body == response.body
        return self.content_parser.compare_to(response.content)

    def check(self, path, response):
        """执行分析，检查响应是否为wildcard"""
        if self.response.status != response.status:
            return True

        if self.wildcard_redirect_regex and response.redirect:
            path = unquote(clean_path(path))
            redirect = unquote(clean_path(response.redirect))
            regex_to_compare = self.wildcard_redirect_regex.replace(
                REFLECTED_PATH_MARKER, re.escape(path)
            )
            is_wildcard_redirect = re.match(regex_to_compare, redirect, re.IGNORECASE)
            if not is_wildcard_redirect:
                return True

        if self.is_wildcard(response):
            return False

        return True

    @staticmethod
    def generate_redirect_regex(first_loc, first_path, second_loc, second_path):
        """从2个wildcard重定向生成正则表达式"""
        if first_path:
            first_loc = unquote(first_loc).replace(first_path, REFLECTED_PATH_MARKER)
        if second_path:
            second_loc = unquote(second_loc).replace(second_path, REFLECTED_PATH_MARKER)
        return generate_matching_regex(first_loc, second_loc)
