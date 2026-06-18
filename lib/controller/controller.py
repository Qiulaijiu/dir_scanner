# -*- coding: utf-8 -*-
"""
主控制器
"""

import gc
import os
import time

from urllib.parse import urlparse

from lib.connection.requester import Requester
from lib.core.data import blacklists, options
from lib.core.decorators import locked
from lib.core.dictionary import Dictionary, get_blacklists, load_wordlists_from_directory, list_categories
from lib.core.exceptions import (
    InvalidURLException,
    RequestException,
    SkipTargetInterrupt,
    QuitInterrupt,
)
from lib.core.fuzzer import Fuzzer
from lib.core.logger import logger
from lib.core.settings import (
    BANNER,
    DEFAULT_HEADERS,
    MAX_CONSECUTIVE_REQUEST_ERRORS,
    NEW_LINE,
    SCRIPT_PATH,
    STANDARD_PORTS,
    PAUSING_WAIT_TIMEOUT,
)
from lib.parse.url import clean_path, parse_path
from lib.reports.csv_report import CSVReport
from lib.reports.html_report import HTMLReport
from lib.reports.json_report import JSONReport
from lib.reports.markdown_report import MarkdownReport
from lib.reports.plain_text_report import PlainTextReport
from lib.reports.simple_report import SimpleReport
from lib.reports.xml_report import XMLReport
from lib.utils.common import get_valid_filename
from lib.utils.file import FileUtils
from lib.view.terminal import output


class Controller:
    """主控制器"""

    def __init__(self):
        self.setup()
        self.run()

    def setup(self):
        """初始化所有组件"""
        blacklists.update(get_blacklists())

        # 设置请求头
        options["headers"] = {**DEFAULT_HEADERS, **options.get("headers", {})}

        if options.get("user_agent"):
            options["headers"]["User-Agent"] = options["user_agent"]

        if options.get("cookie"):
            options["headers"]["Cookie"] = options["cookie"]

        # 创建请求器
        self.requester = Requester()

        # 创建字典 - 根据模式选择
        wordlist_dir = options.get("wordlist_dir", os.path.join(SCRIPT_PATH, "wordlists"))
        src_mode = options.get("src_mode", False)
        src_categories = options.get("src_categories")
        categories = options.get("categories")
        wordlists = options.get("wordlists")

        if wordlists:
            # 自定义字典文件
            self.dictionary = Dictionary(files=wordlists)
        elif src_mode:
            # SRC模式
            if src_categories:
                # SRC分类模式
                self.dictionary = Dictionary(
                    wordlist_dir=wordlist_dir,
                    mode="src-select",
                    categories=src_categories
                )
            else:
                # SRC全量模式
                self.dictionary = Dictionary(wordlist_dir=wordlist_dir, mode="src")
        else:
            # 默认模式（使用dirsearch通用字典）
            self.dictionary = Dictionary(wordlist_dir=wordlist_dir, mode="default")

        self.results = []
        self.targets = options.get("urls", [])
        self.start_time = time.time()
        self.passed_urls = set()
        self.directories = []
        self.report = None
        self.batch = False
        self.jobs_processed = 0
        self.errors = 0
        self.consecutive_errors = 0
        self.seen_responses = {}  # 去重: (status, body_hash) -> count
        self.filtered_responses = []  # 被过滤的响应
        self.paths_403 = []  # 收集403路径用于bypass

        # 设置报告
        self.setup_reports()

        # 输出Banner和配置
        output.header(BANNER)
        output.config(len(self.dictionary))

    def run(self):
        """主循环"""
        match_callbacks = (self.match_callback, self.reset_consecutive_errors)
        not_found_callbacks = (self.update_progress_bar, self.reset_consecutive_errors)
        error_callbacks = (self.raise_error, self.append_error_log)

        while self.targets:
            url = self.targets[0]
            self.fuzzer = Fuzzer(
                self.requester,
                self.dictionary,
                match_callbacks=match_callbacks,
                not_found_callbacks=not_found_callbacks,
                error_callbacks=error_callbacks,
            )

            try:
                self.set_target(url)

                if not self.directories:
                    for subdir in options.get("subdirs", ["/"]):
                        self.add_directory(self.base_path + subdir)

                output.target(self.url)
                self.start()

            except (
                InvalidURLException,
                RequestException,
                SkipTargetInterrupt,
                KeyboardInterrupt,
            ) as e:
                self.directories.clear()
                self.dictionary.reset()
                # 只在非SkipTargetInterrupt时显示错误
                if not isinstance(e, SkipTargetInterrupt) and e.args:
                    output.error(str(e))

            except QuitInterrupt as e:
                output.error(e.args[0])
                exit(0)

            finally:
                self.targets.pop(0)

        elapsed_time = time.time() - self.start_time
        filtered_count = sum(c - 1 for c in self.seen_responses.values() if c > 1)
        output.scan_summary(self.results, elapsed_time, filtered_count, self.filtered_responses)

        # 403 Bypass模式
        if options.get("bypass_403", False) and self.paths_403:
            self.run_bypass403()

    def start(self):
        """处理单个目标的目录队列"""
        while self.directories:
            try:
                gc.collect()
                current_directory = self.directories[0]

                self.fuzzer.set_base_path(current_directory)
                self.fuzzer.start()
                self.process()

            except KeyboardInterrupt:
                pass

            finally:
                self.update_progress_bar()
                self.dictionary.reset()
                self.directories.pop(0)
                self.jobs_processed += 1

    def set_target(self, url):
        """设置目标URL"""
        if "://" not in url:
            url = f"http://{url}"
        if not url.endswith("/"):
            url += "/"

        parsed = urlparse(url)
        self.base_path = clean_path(parsed.path)
        # 规范化路径，避免双斜杠
        self.base_path = "/" + self.base_path.strip("/") + "/" if self.base_path.strip("/") else "/"

        host = parsed.netloc.split(":")[0]

        try:
            port = int(parsed.netloc.split(":")[1])
        except (IndexError, ValueError):
            port = STANDARD_PORTS.get(parsed.scheme, 80)

        self.url = f"{parsed.scheme}://{host}"
        if port != STANDARD_PORTS.get(parsed.scheme, 80):
            self.url += f":{port}"
        self.url += "/"

        self.requester.set_url(self.url)

    def setup_reports(self):
        """设置报告"""
        output_file = options.get("output_file")
        if not output_file:
            return

        output_format = options.get("output_format", "plain")

        if output_format == "plain":
            self.report = PlainTextReport(output_file)
        elif output_format == "json":
            self.report = JSONReport(output_file)
        elif output_format == "xml":
            self.report = XMLReport(output_file)
        elif output_format == "md":
            self.report = MarkdownReport(output_file)
        elif output_format == "csv":
            self.report = CSVReport(output_file)
        elif output_format == "html":
            self.report = HTMLReport(output_file)
        else:
            self.report = SimpleReport(output_file)

        output.output_file(output_file)

    def reset_consecutive_errors(self, response):
        """重置连续错误计数"""
        self.consecutive_errors = 0

    def match_callback(self, response):
        """发现路径的回调"""
        if response.status in options.get("skip_on_status", []):
            raise SkipTargetInterrupt(
                f"Skipped the target due to {response.status} status code"
            )

        # 去重: 相同状态码+响应体的只显示第一条（过滤WAF拦截等重复响应）
        resp_hash = hash((response.status, response.body[:512]))
        if resp_hash in self.seen_responses:
            self.seen_responses[resp_hash] += 1
            # 记录被过滤的响应
            self.filtered_responses.append(response)
            # 403路径仍然收集用于bypass
            if response.status == 403:
                self.paths_403.append(response.full_path)
            return
        self.seen_responses[resp_hash] = 1

        # 收集403路径
        if response.status == 403:
            self.paths_403.append(response.full_path)

        output.status_report(response, options.get("full_url", False))

        # 递归处理
        if response.status in options.get("recursion_status_codes", []):
            if response.redirect:
                new_path = clean_path(parse_path(response.redirect))
                added_to_queue = self.recur_for_redirect(response.path, new_path)
            elif response.history:
                old_path = clean_path(parse_path(response.history[0]))
                added_to_queue = self.recur_for_redirect(old_path, response.path)
            else:
                added_to_queue = self.recur(response.path)

            if added_to_queue:
                output.new_directories(added_to_queue)

        # 保存报告
        if self.report:
            self.results.append(response)
            self.report.save(self.results)

    def update_progress_bar(self, response=None):
        """更新进度条"""
        jobs_count = (
            len(options.get("subdirs", ["/"])) * (len(self.targets) - 1)
            + len(self.directories)
            + self.jobs_processed
        )

        output.last_path(
            self.dictionary.index,
            len(self.dictionary),
            self.jobs_processed + 1,
            jobs_count,
            self.requester.rate,
            self.errors,
        )

    def raise_error(self, exception):
        """错误处理"""
        if options.get("exit_on_error", False):
            raise QuitInterrupt("Canceled due to an error")

        self.errors += 1
        self.consecutive_errors += 1

        if self.consecutive_errors > MAX_CONSECUTIVE_REQUEST_ERRORS:
            raise SkipTargetInterrupt("Too many request errors")

    def append_error_log(self, exception):
        """记录错误日志"""
        logger.warning(str(exception))

    def run_bypass403(self):
        """运行403绕过"""
        from lib.core.pass403 import Pass403Threaded

        # 去重403路径
        unique_paths = list(set(self.paths_403))
        if not unique_paths:
            return

        output.warning(f"\n[*] 403 Bypass: {len(unique_paths)} 个路径待绕过")
        output.warning("[*] 使用路径变形 + HTTP方法 + IP头伪造 + URL重写头")

        threads = min(len(unique_paths) * 4, 40)
        bypass = Pass403Threaded(
            self.url,
            timeout=options.get("timeout", 10),
            threads=threads,
        )

        bypass_results = bypass.run(unique_paths)

        # 去重结果
        seen = set()
        unique_results = []
        for r in bypass_results:
            key = (r.status, r.length)
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        if unique_results:
            output.warning(f"[+] Bypass成功: {len(unique_results)} 条")
            for r in unique_results:
                # 构造模拟response对象用于status_report
                class BypassResponse:
                    pass
                resp = BypassResponse()
                resp.status = r.status
                resp.length = r.length
                resp.url = r.url
                resp.full_path = r.url.replace(self.url, "").lstrip("/")
                resp.redirect = ""
                resp.title = r.title
                resp.body = b""
                output.status_report(resp, full_url=True)
        else:
            output.warning("[-] 403 Bypass未发现绕过路径")

    def handle_pause(self):
        """暂停处理"""
        output.warning("CTRL+C detected: Pausing threads, please wait...", do_save=False)
        self.fuzzer.pause()

        start_time = time.time()
        while True:
            is_timed_out = time.time() - start_time > PAUSING_WAIT_TIMEOUT
            if self.fuzzer.is_stopped() or is_timed_out:
                break
            time.sleep(0.2)

        while True:
            msg = "[q]uit / [c]ontinue"
            if len(self.directories) > 1:
                msg += " / [n]ext"
            if len(self.targets) > 1:
                msg += " / [s]kip target"

            output.in_line(msg + ": ")
            option = input()

            if option.lower() == "q":
                raise QuitInterrupt("Canceled by the user")
            elif option.lower() == "c":
                self.fuzzer.resume()
                return
            elif option.lower() == "n" and len(self.directories) > 1:
                self.fuzzer.stop()
                return
            elif option.lower() == "s" and len(self.targets) > 1:
                raise SkipTargetInterrupt("Target skipped by the user")

    def is_timed_out(self):
        """检查是否超时"""
        max_time = options.get("max_time", 0)
        return time.time() - self.start_time > max_time > 0

    def process(self):
        """等待fuzzer完成"""
        while True:
            try:
                while not self.fuzzer.wait(0.25):
                    if self.is_timed_out():
                        raise SkipTargetInterrupt("Runtime exceeded the maximum set by the user")
                break
            except KeyboardInterrupt:
                self.handle_pause()

    def add_directory(self, path):
        """添加目录到递归队列"""
        exclude_subdirs = options.get("exclude_subdirs", [])
        if any("/" + dir in path for dir in exclude_subdirs):
            return

        url = self.url + path
        max_depth = options.get("recursion_depth", 0)

        if max_depth > 0 and path.count("/") - self.base_path.count("/") > max_depth:
            return

        if url in self.passed_urls:
            return

        self.directories.append(path)
        self.passed_urls.add(url)

    @locked
    def recur(self, path):
        """递归目录管理"""
        dirs_count = len(self.directories)
        path = clean_path(path)

        if options.get("force_recursive", False) and not path.endswith("/"):
            path += "/"

        if options.get("deep_recursive", False):
            i = 0
            for _ in range(path.count("/")):
                i = path.index("/", i) + 1
                self.add_directory(path[:i])
        elif options.get("recursive", False) and path.endswith("/"):
            self.add_directory(path)

        return self.directories[dirs_count:]

    def recur_for_redirect(self, path, redirect_path):
        """处理重定向递归"""
        if redirect_path == path + "/":
            return self.recur(redirect_path)
        return []
