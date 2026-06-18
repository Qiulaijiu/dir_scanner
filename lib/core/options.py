# -*- coding: utf-8 -*-
"""
选项解析与合并
"""

import os
import sys

from lib.core.settings import COMMON_EXTENSIONS, SCRIPT_PATH, SRC_WORDLISTS, DEFAULT_WORDLIST
from lib.parse.cmdline import parse_arguments
from lib.utils.file import FileUtils


def _parse_status_codes(str_):
    """
    解析状态码字符串，支持多种格式:
      - 单个: 200,403
      - 范围: 200-300,400-499
      - 分类: 2xx,3xx,4xx,5xx
      - 混合: 200,3xx,403,500-502
    """
    if not str_:
        return set()

    # 分类别名映射
    category_map = {
        "2xx": range(200, 300),
        "3xx": range(300, 400),
        "4xx": range(400, 500),
        "5xx": range(500, 600),
    }

    result = set()
    for part in str_.split(","):
        part = part.strip().lower()

        if not part:
            continue

        # 分类别名: 2xx, 3xx, 4xx, 5xx
        if part in category_map:
            result.update(category_map[part])
            continue

        # 范围格式: 200-300, 400-499
        if "-" in part:
            try:
                start, end = part.split("-")
                result.update(range(int(start.strip()), int(end.strip()) + 1))
            except ValueError:
                pass
            continue

        # 单个状态码
        try:
            result.add(int(part))
        except ValueError:
            pass

    return result


def parse_options():
    """解析并返回选项字典"""
    args = parse_arguments()
    options = {}

    # 目标URL
    options["urls"] = []
    if args.url:
        options["urls"].append(args.url)
    elif args.url_file:
        if not FileUtils.can_read(args.url_file):
            print(f"[!] Cannot read URL file: {args.url_file}")
            sys.exit(1)
        options["urls"] = FileUtils.get_lines(args.url_file)
    elif args.stdin:
        options["urls"] = [line.strip() for line in sys.stdin if line.strip()]

    # 字典模式设置
    wordlist_dir = os.path.join(SCRIPT_PATH, "wordlists")
    options["wordlist_dir"] = wordlist_dir

    # SRC模式判断
    if args.src:
        # SRC模式：使用全部SRC字典
        options["src_mode"] = True
        options["src_categories"] = None
        options["wordlists"] = None
        options["categories"] = None
    elif args.src_category:
        # SRC分类模式：使用指定的SRC类别
        options["src_mode"] = True
        options["src_categories"] = [c.strip() for c in args.src_category.split(",")]
        options["wordlists"] = None
        options["categories"] = None
    else:
        # 默认模式：使用通用字典
        options["src_mode"] = False
        options["src_categories"] = None
        options["wordlists"] = args.wordlists
        options["categories"] = [c.strip() for c in args.category.split(",")] if args.category else None

    # 扩展名设置
    options["extensions"] = tuple(args.extensions.split(","))
    options["force_extensions"] = args.force_extensions
    options["overwrite_extensions"] = args.overwrite_extensions
    options["exclude_extensions"] = tuple(args.exclude_extensions.split(",")) if args.exclude_extensions else ()
    options["prefixes"] = tuple(args.prefixes.split(",")) if args.prefixes else ()
    options["suffixes"] = tuple(args.suffixes.split(",")) if args.suffixes else ()
    options["lowercase"] = args.lowercase
    options["uppercase"] = args.uppercase
    options["capitalization"] = args.capital

    # 通用设置
    options["thread_count"] = args.threads
    options["recursive"] = args.recursive
    options["deep_recursive"] = args.deep_recursive
    options["force_recursive"] = args.force_recursive
    options["recursion_depth"] = args.recursion_depth
    options["recursion_status_codes"] = _parse_status_codes(args.recursion_status)
    options["subdirs"] = args.subdirs.split(",") if args.subdirs else ["/"]
    options["exclude_subdirs"] = args.exclude_subdirs.split(",") if args.exclude_subdirs else []
    options["include_status_codes"] = _parse_status_codes(args.include_status)
    options["exclude_status_codes"] = _parse_status_codes(args.exclude_status)

    # 默认只显示高价值状态码（用户未指定过滤条件时）
    # 排除403(WAF拦截噪声)和普通重定向，保留真正有价值的响应
    if not options["include_status_codes"] and not options["exclude_status_codes"]:
        options["include_status_codes"] = {200, 201, 204, 301, 302, 307, 308, 401, 403, 500}
    options["exclude_sizes"] = args.exclude_sizes.split(",") if args.exclude_sizes else []
    options["exclude_texts"] = args.exclude_text.split(",") if args.exclude_text else []
    options["exclude_regex"] = args.exclude_regex
    options["exclude_redirect"] = args.exclude_redirect
    options["exclude_response"] = args.exclude_response
    options["skip_on_status"] = _parse_status_codes(args.skip_on_status)
    options["minimum_response_size"] = args.min_response_size or 0
    options["maximum_response_size"] = args.max_response_size or 0
    options["max_time"] = args.max_time
    options["exit_on_error"] = args.exit_on_error

    # 请求设置
    options["http_method"] = args.http_method.upper()
    options["data"] = args.data
    options["headers"] = {}
    if args.header:
        for h in args.header:
            key, _, value = h.partition(":")
            options["headers"][key.strip()] = value.strip()
    options["follow_redirects"] = args.follow_redirects
    options["random_agents"] = args.random_agent
    options["user_agent"] = args.user_agent
    options["cookie"] = args.cookie
    options["auth"] = args.auth
    options["auth_type"] = args.auth_type

    # 连接设置
    options["timeout"] = args.timeout
    options["delay"] = args.delay
    options["proxies"] = []
    if args.proxy:
        options["proxies"].append(args.proxy)
    elif args.proxy_file:
        if FileUtils.can_read(args.proxy_file):
            options["proxies"] = FileUtils.get_lines(args.proxy_file)
    options["proxy_auth"] = args.proxy_auth
    options["max_rate"] = args.max_rate
    options["max_retries"] = args.retries

    # WAF绕过
    options["waf_bypass"] = args.waf_bypass
    options["bypass_403"] = args.bypass_403
    if args.random_user_agents:
        options["random_agents"] = True

    # 视图设置
    options["full_url"] = args.full_url
    options["color"] = not args.no_color
    options["show_filtered"] = args.show_filtered
    options["quiet"] = args.quiet

    # 输出设置
    options["output_file"] = args.output
    options["output_format"] = args.format
    options["log_file"] = args.log

    # 设置默认值
    options.setdefault("extensions", COMMON_EXTENSIONS)
    options.setdefault("prefixes", ())
    options.setdefault("suffixes", ())

    return options
