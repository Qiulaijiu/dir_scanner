#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dir_scanner - SRC目录扫描工具
整合SRC内部字典和dirsearch通用字典，支持WAF绕过、频率限制、随机UA池

用法:
  # 默认模式 (使用dirsearch通用字典 dicc.txt, 9482条)
  python dir_scanner.py -u http://target.com

  # SRC模式 (使用全部SRC字典, 15个类别, 8181条)
  python dir_scanner.py -u http://target.com --src

  # SRC分类模式 (指定SRC类别)
  python dir_scanner.py -u http://target.com --src-category "管理后台路径,API接口路径"

  # 其他选项
  python dir_scanner.py -u http://target.com --waf-bypass --max-rate 20
  python dir_scanner.py --list
"""

import os
import sys

# Windows控制台UTF-8支持
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 确保能找到lib模块
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from lib.core.data import options
from lib.core.exceptions import QuitInterrupt
from lib.core.options import parse_options
from lib.core.settings import BANNER, VERSION, SRC_WORDLISTS, DEFAULT_WORDLIST
from lib.core.dictionary import list_all_categories
from lib.parse.cmdline import parse_arguments
from lib.view.terminal import output


def main():
    """主入口"""
    # 先解析命令行参数检查特殊选项
    args = parse_arguments()

    # 列出字典类别
    if args.list:
        wordlist_dir = os.path.join(SCRIPT_DIR, "wordlists")
        categories = list_all_categories(wordlist_dir)

        print(f"\n{'='*70}")
        print("  dir_scanner - 可用字典类别")
        print(f"{'='*70}")

        # 默认字典（dirsearch通用字典）
        print(f"\n  [默认模式] 通用字典 (--src 未指定时使用)")
        print(f"  {'─'*50}")
        if categories["default"]:
            default_total = 0
            for name, count in categories["default"]:
                print(f"    {name:<30} ({count} 条)")
                default_total += count
            print(f"    {'─'*40}")
            print(f"    小计: {len(categories['default'])} 个文件, {default_total} 条路径")
        else:
            print("    [!] 未找到通用字典文件")

        # SRC字典
        print(f"\n  [SRC模式] SRC专项字典 (--src 或 --src-category 使用)")
        print(f"  {'─'*50}")
        if categories["src"]:
            src_total = 0
            for name, count in categories["src"]:
                print(f"    {name:<30} ({count} 条)")
                src_total += count
            print(f"    {'─'*40}")
            print(f"    小计: {len(categories['src'])} 个类别, {src_total} 条路径")
        else:
            print("    [!] 未找到SRC字典文件")

        # 总计
        all_total = sum(count for _, count in categories["default"] + categories["src"])
        print(f"\n  {'='*50}")
        print(f"  总计: {len(categories['default']) + len(categories['src'])} 个文件, {all_total} 条路径")
        print(f"  {'='*50}")

        # 使用说明
        print(f"\n使用说明:")
        print(f"  默认模式:  python dir_scanner.py -u http://target.com")
        print(f"  SRC模式:   python dir_scanner.py -u http://target.com --src")
        print(f"  SRC分类:   python dir_scanner.py -u http://target.com --src-category '管理后台路径,API接口路径'")
        print()

        return

    # 列出扩展名
    if args.list_extensions:
        from lib.core.settings import COMMON_EXTENSIONS
        print("\n可用扩展名:")
        print(", ".join(COMMON_EXTENSIONS))
        return

    # 解析完整选项
    parsed_options = parse_options()

    # 检查目标URL
    if not parsed_options.get("urls"):
        print(BANNER)
        print("[!] 请指定目标URL")
        print()
        print("用法:")
        print("  python dir_scanner.py -u http://target.com              # 默认模式(dirsearch字典)")
        print("  python dir_scanner.py -u http://target.com --src        # SRC模式(SRC专项字典)")
        print()
        print("查看所有选项: python dir_scanner.py -h")
        print("列出字典类别: python dir_scanner.py --list")
        return

    # 颜色设置
    if not parsed_options.get("color", True):
        from lib.view.colors import disable_color
        disable_color()

    # 更新全局options
    options.update(parsed_options)

    # 启动控制器
    try:
        from lib.controller.controller import Controller
        Controller()
    except KeyboardInterrupt:
        print("\n[!] 用户中断")
    except QuitInterrupt as e:
        print(f"\n[!] {e.args[0]}")
    except Exception as e:
        print(f"\n[!] 错误: {e}")
        if os.environ.get("DEBUG"):
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
