# -*- coding: utf-8 -*-
"""
终端输出 - dir_scanner专用
使用与dirsearch不同的配色方案和显示风格
"""

import sys
import time

from lib.core.data import options
from lib.core.decorators import locked
from lib.utils.common import human_size
from lib.view.colors import set_color, clean_color


class Output:
    """终端输出类"""

    def __init__(self):
        self.last_in_line = False
        self.buffer = ""

    @staticmethod
    def erase():
        """清除当前行"""
        sys.stdout.write("\033[1K")
        sys.stdout.write("\033[0G")
        sys.stdout.flush()

    @locked
    def in_line(self, string):
        """覆盖式输出"""
        self.erase()
        try:
            sys.stdout.write(string)
        except UnicodeEncodeError:
            sys.stdout.write(string.encode("utf-8", errors="replace").decode("utf-8"))
        sys.stdout.flush()
        self.last_in_line = True

    @locked
    def new_line(self, string="", do_save=True):
        """换行输出"""
        if self.last_in_line:
            self.erase()

        try:
            sys.stdout.write(string + "\n")
        except UnicodeEncodeError:
            sys.stdout.write(string.encode("utf-8", errors="replace").decode("utf-8") + "\n")
        sys.stdout.flush()
        self.last_in_line = False

        if do_save:
            self.buffer += string + "\n"

    def status_report(self, response, full_url=False):
        """扫描结果输出 - 精简格式"""
        status = response.status
        length = human_size(response.length)
        # 规范化路径，避免双斜杠
        if full_url:
            target = response.url
        else:
            target = "/" + response.full_path.lstrip("/")
        current_time = time.strftime("%H:%M:%S")

        # 状态码颜色
        if status in (200, 201, 204):
            color = "green"
        elif status == 401:
            color = "yellow"
        elif status == 403:
            color = "blue"
        elif status in range(300, 400):
            color = "cyan"
        elif status in range(500, 600):
            color = "red"
        else:
            color = "magenta"

        time_str = set_color(current_time, fore="white", style="dim")
        status_str = set_color(str(status), fore=color, style="bright")
        length_str = set_color(length.rjust(6, ' '), fore=color)

        message = f"[{time_str}] {status_str} - {length_str} - {target}"

        if response.redirect:
            message += set_color(f"  ->  {response.redirect}", fore="cyan", style="dim")

        self.new_line(message)

    def last_path(self, index, length, current_job, all_jobs, rate, errors):
        """
        更新进度条
        dir_scanner特色：使用不同的进度条样式和颜色
        """
        if length == 0:
            return

        percentage = int(index / length * 100)

        # 进度条使用不同的字符和颜色
        filled = int(percentage / 5)
        bar = set_color("#" * filled, fore="bright_cyan", style="bright")
        bar += set_color("-" * (20 - filled), fore="white", style="dim")

        progress = f"{index}/{length}"

        # 作业信息 - 使用不同的颜色
        job_label = set_color("任务", fore="bright_green", style="bright")
        jobs = f"{job_label}:{current_job}/{all_jobs}"

        # 错误信息
        error_label = set_color("错误", fore="bright_red", style="bright")
        errors_str = f"{error_label}:{errors}"

        # 速率 - 使用亮色
        rate_str = set_color(f"{rate}/s", fore="bright_yellow")

        # 百分比 - 高亮显示
        if percentage >= 100:
            pct = set_color(f"{percentage}%", fore="bright_green", style="bright")
        elif percentage >= 50:
            pct = set_color(f"{percentage}%", fore="bright_cyan", style="bright")
        else:
            pct = set_color(f"{percentage}%", fore="bright_yellow")

        progress_bar = f"[{bar}] {pct} "
        progress_bar += f"{progress.rjust(12, chr(32))} "
        progress_bar += f"{rate_str.rjust(12, chr(32))}  "
        progress_bar += f"{jobs.ljust(18, chr(32))} {errors_str}"

        self.in_line(progress_bar)

    def new_directories(self, directories):
        """显示新发现的目录"""
        message = set_color(
            f"[+] 新目录: {', '.join(directories)}", fore="bright_yellow", style="dim"
        )
        self.new_line(message)

    def error(self, reason):
        """错误输出"""
        message = set_color(f"[!] {reason}", fore="bright_red", style="bright")
        self.new_line("\n" + message)

    def crawl_found(self, path, source=""):
        """爬虫发现的路径"""
        tag = set_color("[待爬取]", fore="bright_yellow", style="bright")
        path_str = set_color(path, fore="bright_cyan")
        msg = f"  {tag} {path_str}"
        if source:
            msg += set_color(f"  ({source})", fore="white", style="dim")
        self.new_line(msg)

    def crawl_test_result(self, path, status, length, content_type=""):
        """爬虫路径自动测试结果"""
        current_time = time.strftime("%H:%M:%S")

        # 状态码颜色
        if status in (200, 201, 204):
            color = "green"
        elif status == 401:
            color = "yellow"
        elif status == 403:
            color = "blue"
        elif status in range(300, 400):
            color = "cyan"
        else:
            color = "magenta"

        size_str = human_size(length).rjust(6)
        time_str = set_color(current_time, fore="white", style="dim")
        status_str = set_color(str(status), fore=color, style="bright")
        size_colored = set_color(size_str, fore=color)
        path_str = set_color(path, fore="bright_cyan")

        ct_str = ""
        if content_type and "json" in content_type:
            ct_str = set_color(" [API]", fore="bright_magenta", style="bright")

        message = f"[{time_str}] {status_str} - {size_colored} - {path_str}{ct_str}"
        self.new_line(message)

    def crawl_test_summary(self, results):
        """爬虫路径测试结果摘要"""
        self.new_line()
        self.new_line(set_color("=" * 60, fore="bright_yellow", style="bright"))
        self.new_line(set_color("  爬虫路径自动测试结果", fore="bright_yellow", style="bright"))
        self.new_line(set_color("-" * 60, fore="white", style="dim"))
        self.new_line(set_color(f"  测试路径: {len(results)} 条", fore="white"))

        # 按状态码分组
        by_status = {}
        for r in results:
            by_status.setdefault(r["status"], []).append(r)

        for status in sorted(by_status.keys()):
            items = by_status[status]
            if status in (200, 201, 204):
                label = set_color("命中存活", fore="black", back="green", style="bright")
                color = "bright_green"
            elif status == 401:
                label = set_color("需鉴权", fore="black", back="yellow", style="bright")
                color = "bright_yellow"
            elif status == 403:
                label = set_color("访问拦截", fore="black", back="red", style="bright")
                color = "bright_red"
            elif status in range(300, 400):
                label = set_color("重定向", fore="black", back="cyan", style="bright")
                color = "bright_cyan"
            else:
                label = set_color("请求异常", fore="black", back="magenta")
                color = "bright_magenta"

            self.new_line(f"\n  {label}  [{status}]  x{set_color(str(len(items)), fore=color, style='bright')}")
            for r in sorted(items, key=lambda x: x["length"], reverse=True):
                size = human_size(r["length"]).rjust(6)
                ct_tag = ""
                if "json" in r.get("type", ""):
                    ct_tag = set_color(" [API]", fore="bright_magenta")
                redirect = ""
                if r.get("redirect"):
                    redirect = set_color(f"  ->  {r['redirect']}", fore="cyan", style="dim")
                self.new_line(f"    {set_color(size, fore=color)}  {set_color(r['path'], fore='bright_cyan')}{ct_tag}{redirect}")

        # 文件类型分类（紧接状态码之后）
        ext_groups = {}
        for r in results:
            ext = r["path"].rsplit(".", 1)[-1].lower() if "." in r["path"].split("/")[-1] else ""
            ext_groups.setdefault(ext or "无扩展名", []).append(r)
        if len(ext_groups) > 1:
            self.new_line(set_color("  ──────────────────────────────", fore="white", style="dim"))
            for ext in sorted(ext_groups.keys(), key=lambda x: len(ext_groups[x]), reverse=True):
                count = len(ext_groups[ext])
                ext_str = set_color(f".{ext:<10}", fore="bright_cyan")
                count_colored = set_color(str(count), fore="bright_green", style="bright")
                self.new_line(f"    {ext_str} {count_colored} 条")

        self.new_line(set_color("=" * 60, fore="bright_yellow", style="bright"))

    def warning(self, message, do_save=True):
        """警告输出"""
        message = set_color(f"[*] {message}", fore="bright_yellow", style="bright")
        self.new_line(message, do_save=do_save)

    def header(self, message):
        """标题输出"""
        message = set_color(message, fore="bright_cyan", style="bright")
        self.new_line(message)

    def print_header(self, headers):
        """打印配置头 - dir_scanner特色格式"""
        msg = []
        for key, value in headers.items():
            new = set_color(f"{key}: ", fore="bright_yellow", style="bright")
            new += set_color(value, fore="bright_cyan")
            msg.append(new)

        self.new_line(set_color(" │ ", fore="white", style="dim").join(msg))

    def config(self, wordlist_size):
        """输出配置信息 - 中文显示"""
        config = {}
        config["扩展名"] = ", ".join(options.get("extensions", []))
        config["HTTP方法"] = options.get("http_method", "GET")
        config["线程数"] = str(options.get("thread_count", 30))
        config["字典大小"] = str(wordlist_size)

        # 显示字典模式
        src_mode = options.get("src_mode", False)
        src_categories = options.get("src_categories")
        if src_mode:
            if src_categories:
                config["字典模式"] = f"SRC分类 ({', '.join(src_categories)})"
            else:
                config["字典模式"] = "SRC模式"
        else:
            config["字典模式"] = "默认模式"

        if options.get("waf_bypass", False):
            config["WAF绕过"] = "已启用"
        if options.get("bypass_403", False):
            config["403绕过"] = "已启用"
        if options.get("crawl", False):
            config["爬虫模式"] = "已启用"

        if options.get("max_rate", 0) > 0:
            config["速率限制"] = f"{options['max_rate']}/s"

        self.print_header(config)

    def target(self, target):
        """输出目标信息"""
        self.new_line()
        self.print_header({"目标": target})

    def output_file(self, file):
        """输出报告文件路径"""
        self.new_line(f"\n输出文件: {file}")

    def scan_summary(self, results, elapsed_time, filtered_count=0, filtered_responses=None, crawled_count=0):
        """扫描结果摘要"""
        self.new_line()
        self.new_line(set_color("=" * 60, fore="bright_cyan", style="bright"))
        self.new_line(set_color("  扫描完成", fore="bright_green", style="bright"))
        self.new_line(set_color("-" * 60, fore="white", style="dim"))

        # 统计各状态码数量
        status_count = {}
        for r in results:
            status_count[r.status] = status_count.get(r.status, 0) + 1

        self.new_line(set_color(f"  耗时: {elapsed_time:.1f}秒", fore="white"))
        self.new_line(set_color(f"  发现: {len(results)} 条有效路径", fore="bright_green", style="bright"))
        if filtered_count > 0:
            self.new_line(set_color(f"  过滤: {filtered_count} 条重复响应(WAF拦截等)", fore="white", style="dim"))
        if crawled_count > 0:
            self.new_line(set_color(f"  爬虫: {crawled_count} 条路径(从响应中提取)", fore="bright_yellow", style="bright"))

        if status_count:
            self.new_line(set_color("  ──────────────────────────────", fore="white", style="dim"))
            for status in sorted(status_count.keys()):
                count = status_count[status]
                if status in (200, 201, 204):
                    label = set_color("命中存活", fore="black", back="green", style="bright")
                    color = "bright_green"
                elif status == 401:
                    label = set_color("需鉴权", fore="black", back="yellow", style="bright")
                    color = "bright_yellow"
                elif status == 403:
                    label = set_color("访问拦截", fore="black", back="red", style="bright")
                    color = "bright_red"
                elif status in range(300, 400):
                    label = set_color("重定向", fore="black", back="cyan", style="bright")
                    color = "bright_cyan"
                else:
                    label = set_color("请求异常", fore="black", back="magenta")
                    color = "bright_magenta"

                count_str = set_color(str(count), fore=color, style="bright")
                self.new_line(f"  {label}  [{status}]  x{count_str}")

        # 文件类型分类统计（紧接状态码之后）
        if results:
            ext_groups = {}
            for r in results:
                path = "/" + r.full_path.lstrip("/")
                ext = path.rsplit(".", 1)[-1].lower() if "." in path.split("/")[-1] else ""
                ext_groups.setdefault(ext or "无扩展名", []).append(r)
            if len(ext_groups) > 1:
                self.new_line(set_color("  ──────────────────────────────", fore="white", style="dim"))
                for ext in sorted(ext_groups.keys(), key=lambda x: len(ext_groups[x]), reverse=True):
                    count = len(ext_groups[ext])
                    ext_str = set_color(f".{ext:<10}", fore="bright_cyan")
                    count_colored = set_color(str(count), fore="bright_green", style="bright")
                    self.new_line(f"    {ext_str} {count_colored} 条")

        self.new_line(set_color("=" * 60, fore="bright_cyan", style="bright"))

        # 显示被过滤的重复响应
        if filtered_responses and options.get("show_filtered", False):
            self.new_line()
            self.new_line(set_color("  被过滤的重复响应", fore="bright_yellow", style="bright"))
            self.new_line(set_color("-" * 60, fore="white", style="dim"))

            # 按(status, path)分组统计
            filtered_groups = {}
            for r in filtered_responses:
                key = (r.status, "/" + r.full_path.lstrip("/"))
                filtered_groups[key] = filtered_groups.get(key, 0) + 1

            for (status, path), count in sorted(filtered_groups.items()):
                count_str = set_color(f"x{count}", fore="white", style="dim")
                self.new_line(f"  [{status}] {path}  {count_str}")

            self.new_line(set_color("=" * 60, fore="bright_cyan", style="bright"))


output = Output()
