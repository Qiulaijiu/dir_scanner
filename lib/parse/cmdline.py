# -*- coding: utf-8 -*-
"""
命令行参数定义
"""

import argparse

from lib.core.settings import VERSION


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description=f"dir_scanner v{VERSION} - SRC Directory Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 默认模式 (使用dirsearch通用字典 dicc.txt, 9482条)
  python dir_scanner.py -u http://target.com

  # SRC模式 (使用全部SRC字典, 15个类别, 8181条)
  python dir_scanner.py -u http://target.com --src

  # SRC分类模式 (指定SRC类别)
  python dir_scanner.py -u http://target.com --src-category "管理后台路径,API接口路径"

  # 其他选项
  python dir_scanner.py -u http://target.com -t 50 -o result.json
  python dir_scanner.py -u http://target.com --waf-bypass --max-rate 20
  python dir_scanner.py -u http://target.com --proxy http://127.0.0.1:7890
  python dir_scanner.py --list
        """,
    )

    # 必需参数
    target = parser.add_argument_group("Target")
    target.add_argument("-u", "--url", help="目标URL")
    target.add_argument("-l", "--url-file", help="目标URL文件")
    target.add_argument("--stdin", action="store_true", help="从stdin读取URL")

    # 字典设置
    dictionary = parser.add_argument_group("Dictionary")
    dictionary.add_argument("--src", action="store_true",
                            help="SRC模式: 使用全部SRC专项字典(15个类别, 8181条)")
    dictionary.add_argument("--src-category",
                            help="SRC分类模式: 指定SRC类别(逗号分隔), 如: '管理后台路径,API接口路径'")
    dictionary.add_argument("-w", "--wordlists", nargs="+", help="自定义字典文件路径")
    dictionary.add_argument("-c", "--category", help="字典类别(逗号分隔)")
    dictionary.add_argument("-e", "--extensions", default="php,jsp,asp,aspx,html,js",
                            help="扩展名(逗号分隔，默认: php,jsp,asp,aspx,html,js)")
    dictionary.add_argument("-f", "--force-extensions", action="store_true",
                            help="强制扩展名")
    dictionary.add_argument("-O", "--overwrite-extensions", action="store_true",
                            help="覆盖扩展名")
    dictionary.add_argument("--exclude-extensions", help="排除的扩展名")
    dictionary.add_argument("--prefixes", help="前缀(逗号分隔)")
    dictionary.add_argument("--suffixes", help="后缀(逗号分隔)")
    dictionary.add_argument("-U", "--uppercase", action="store_true", help="大写")
    dictionary.add_argument("-L", "--lowercase", action="store_true", help="小写")
    dictionary.add_argument("-C", "--capital", action="store_true", help="首字母大写")

    # 通用设置
    general = parser.add_argument_group("General Settings")
    general.add_argument("-t", "--threads", type=int, default=30, help="线程数(默认: 30)")
    general.add_argument("-r", "--recursive", action="store_true", help="递归扫描")
    general.add_argument("--deep-recursive", action="store_true", help="深度递归")
    general.add_argument("--force-recursive", action="store_true", help="强制递归")
    general.add_argument("-R", "--recursion-depth", type=int, default=0, help="递归深度")
    general.add_argument("--recursion-status", default="200-399,401,403",
                         help="递归状态码(默认: 200-399,401,403)")
    general.add_argument("--subdirs", help="子目录(逗号分隔)")
    general.add_argument("--exclude-subdirs", help="排除的子目录")
    general.add_argument("-i", "--include-status",
                         help="包含的状态码 (支持: 200,301 / 200-300 / 2xx,3xx / 混合: 200,3xx,403)")
    general.add_argument("-x", "--exclude-status",
                         help="排除的状态码 (格式同上)")
    general.add_argument("--exclude-sizes", help="排除的响应大小")
    general.add_argument("--exclude-text", help="排除的响应文本")
    general.add_argument("--exclude-regex", help="排除的正则表达式")
    general.add_argument("--exclude-redirect", help="排除的重定向")
    general.add_argument("--exclude-response", help="排除的响应文件")
    general.add_argument("--skip-on-status", help="跳过的状态码")
    general.add_argument("--min-response-size", type=int, help="最小响应大小")
    general.add_argument("--max-response-size", type=int, help="最大响应大小")
    general.add_argument("--max-time", type=int, default=0, help="最大运行时间(秒)")
    general.add_argument("--exit-on-error", action="store_true", help="错误时退出")

    # 请求设置
    request = parser.add_argument_group("Request Settings")
    request.add_argument("-m", "--http-method", default="GET", help="HTTP方法(默认: GET)")
    request.add_argument("-d", "--data", help="请求数据")
    request.add_argument("-H", "--header", action="append", help="自定义请求头")
    request.add_argument("-F", "--follow-redirects", action="store_true", help="跟随重定向")
    request.add_argument("--random-agent", action="store_true", help="随机User-Agent")
    request.add_argument("--user-agent", help="User-Agent")
    request.add_argument("--cookie", help="Cookie")
    request.add_argument("--auth", help="认证(格式: user:password)")
    request.add_argument("--auth-type", default="basic", help="认证类型(basic/digest/bearer)")

    # 连接设置
    connection = parser.add_argument_group("Connection Settings")
    connection.add_argument("--timeout", type=float, default=10, help="超时(默认: 10秒)")
    connection.add_argument("--delay", type=float, default=0, help="请求延迟(秒)")
    connection.add_argument("--proxy", help="代理地址")
    connection.add_argument("--proxy-file", help="代理文件")
    connection.add_argument("--proxy-auth", help="代理认证")
    connection.add_argument("--max-rate", type=int, default=0, help="最大请求速率(每秒)")
    connection.add_argument("--retries", type=int, default=1, help="重试次数(默认: 1)")

    # WAF绕过
    waf = parser.add_argument_group("WAF Bypass")
    waf.add_argument("--waf-bypass", action="store_true",
                     help="启用WAF绕过模式(随机UA + IP伪造 + 路径混淆)")
    waf.add_argument("--bypass-403", action="store_true",
                     help="启用403绕过模式(路径变形+HTTP方法+IP头伪造+URL重写)")
    waf.add_argument("--random-user-agents", action="store_true", help="随机User-Agent池")

    # 视图设置
    view = parser.add_argument_group("View Settings")
    view.add_argument("--full-url", action="store_true", help="显示完整URL")
    view.add_argument("--no-color", action="store_true", help="禁用颜色")
    view.add_argument("--show-filtered", action="store_true", help="显示被过滤的重复响应")
    view.add_argument("-q", "--quiet", action="store_true", help="静默模式")

    # 输出设置
    output = parser.add_argument_group("Output Settings")
    output.add_argument("-o", "--output", help="输出文件路径")
    output.add_argument("--format", default="plain",
                        choices=["plain", "simple", "json", "xml", "md", "csv", "html"],
                        help="输出格式(默认: plain)")
    output.add_argument("--log", help="日志文件路径")

    # 其他
    parser.add_argument("--list", action="store_true", help="列出所有可用字典类别")
    parser.add_argument("--list-extensions", action="store_true", help="列出所有扩展名")

    args = parser.parse_args()

    return args
