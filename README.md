# dir_scanner - SRC目录扫描工具

> 整合SRC内部字典和dirsearch通用字典的高性能目录路径探测工具，支持爬虫模式、WAF绕过、频率限制、随机UA池、扫描历史记忆

## 功能特性

| 功能 | 说明 |
|------|------|
| **爬虫模式** | 默认开启，从HTML/JS/robots.txt/sitemap.xml中自动提取路径，爬取结果实时测试可访问性 |
| **双字典模式** | 默认模式(dirsearch通用字典9482条) + SRC模式(SRC专项字典15类别8181条) |
| **多线程并发** | 默认30线程，可配置1-200，异步高效扫描 |
| **WAF绕过** | 随机UA池(13个浏览器指纹)、IP伪造(X-Forwarded-For等10种头)、路径大小写混淆、分号注入、垃圾参数消耗 |
| **速率限制** | 令牌桶算法，精确控制每秒请求数，避免触发WAF阈值 |
| **Wildcard检测** | 双请求基准法自动检测通配符响应，DynamicContentParser动态内容分析，减少99%误报 |
| **智能过滤** | 默认只显示有效状态码(200/301/401/403等)，自动过滤404/500噪声 |
| **状态码分类** | 支持 `2xx`/`3xx`/`4xx`/`5xx` 分类别名，支持 `200-300` 范围格式 |
| **递归扫描** | 支持普通递归、深度递归、强制递归，可配置递归深度 |
| **扫描历史** | 自动记录扫描结果，重复扫描时展示历史，支持 `--force` 强制重新扫描 |
| **403 Bypass** | 扫描完成后自动对403路径尝试23种路径变形 + 120种IP头伪造绕过 |
| **多格式报告** | plain / json / xml / html / csv / markdown 6种输出格式 |
| **代理支持** | HTTP / HTTPS / SOCKS4 / SOCKS5 代理，支持代理池轮换 |

## 爬虫模式

爬虫模式**默认开启**，无需额外参数。扫描时自动从响应中提取路径并测试可访问性：

```bash
# 直接运行，爬虫自动生效
python dir_scanner.py -u http://target.com

# 禁用爬虫
python dir_scanner.py -u http://target.com --no-crawl

# 限制爬虫深度
python dir_scanner.py -u http://target.com --crawl-depth 3
```

### 爬虫工作流程

1. 解析 `robots.txt` 和 `sitemap.xml` 提取路径
2. 从HTML页面提取 `href`、`src`、`action` 等链接属性
3. 从JS文件和内联脚本中提取路由路径（支持Vue/React SPA框架）
4. 从HTML注释中提取隐藏路径
5. 对每个爬取路径自动发送HTTP请求，测试可访问性
6. 实时显示测试结果，标记状态码和响应大小

### 爬虫测试输出

```
[14:30:25] 200 -  1.2KB - /front/index.html
[14:30:26] 200 -  3.5KB - /api/user/list [API]
[14:30:26] 302 -    0 B - /admin
[14:30:27] 403 -  0.3KB - /admin/config
```

## 字典模式

### 默认模式 (dirsearch通用字典)

不指定 `--src` 时自动使用，包含9482条通用Web路径：

```bash
python dir_scanner.py -u http://target.com
```

### SRC模式 (SRC专项字典)

使用 `--src` 参数启用，包含15个分类共8181条SRC专用路径：

```bash
python dir_scanner.py -u http://target.com --src
```

### SRC分类模式 (指定SRC类别)

使用 `--src-category` 参数指定特定类别：

```bash
python dir_scanner.py -u http://target.com --src-category "管理后台路径,API接口路径"
```

## 字典分类

### SRC专项字典 (--src 模式)

| 类别 | 条数 | 说明 |
|------|------|------|
| API接口路径 | 1767 | REST API、GraphQL、Webhook等接口端点 |
| Web文件 | 1804 | JSP/ASP/PHP等Web文件路径 |
| 管理后台路径 | 1091 | 后台管理系统入口 |
| 其他路径 | 1279 | 杂项高价值路径 |
| 认证相关路径 | 533 | 登录、注册、OAuth等认证接口 |
| 敏感文件配置 | 483 | .env、.git、配置文件、数据库备份 |
| 上传下载功能 | 436 | 文件上传/下载接口 |
| 配置系统路径 | 259 | 配置管理接口 |
| Spring监控端点 | 189 | Actuator、Druid等Java监控 |
| 数据库相关 | 170 | 数据库管理、备份文件 |
| 编辑器路径 | 76 | FCKeditor、Ueditor等编辑器 |
| 开发测试路径 | 68 | debug、test、demo等开发路径 |
| 目录遍历绕过 | 26 | 目录遍历测试路径 |
| 版本控制相关 | 2 | .git、.svn等版本控制文件 |
| 模板变量路径 | 0 | 模板注入测试路径 |

### 通用字典 (默认模式)

| 文件 | 条数 | 说明 |
|------|------|------|
| dicc.txt | 9482 | dirsearch通用字典，覆盖常见Web路径 |

## 安装

```bash
# 克隆项目
git clone <repo_url> dir_scanner
cd dir_scanner

# 安装依赖
pip install -r requirements.txt
```

## 快速开始

```bash
# 列出所有字典类别
python dir_scanner.py --list

# 默认模式扫描 (爬虫自动开启)
python dir_scanner.py -u http://target.com

# SRC模式扫描 (使用全部SRC字典)
python dir_scanner.py -u http://target.com --src

# SRC分类模式 (指定类别)
python dir_scanner.py -u http://target.com --src-category "管理后台路径,API接口路径"

# WAF绕过模式
python dir_scanner.py -u http://target.com --src --waf-bypass

# WAF绕过 + 限速20请求/秒
python dir_scanner.py -u http://target.com --src --waf-bypass --max-rate 20

# 输出JSON报告
python dir_scanner.py -u http://target.com --src -o result.json --format json

# 查看扫描历史
python dir_scanner.py --history

# 强制重新扫描 (忽略历史)
python dir_scanner.py -u http://target.com --force
```

## 完整参数

### 目标设置

| 参数 | 说明 | 示例 |
|------|------|------|
| `-u, --url` | 目标URL | `-u http://target.com` |
| `-l, --url-file` | 目标URL文件 | `-l urls.txt` |
| `--stdin` | 从stdin读取URL | `cat urls.txt \| python dir_scanner.py --stdin` |

### 字典设置

| 参数 | 说明 | 示例 |
|------|------|------|
| `--src` | SRC模式: 使用全部SRC专项字典(15类别, 8181条) | `--src` |
| `--src-category` | SRC分类模式: 指定SRC类别(逗号分隔) | `--src-category "管理后台路径,API接口路径"` |
| `-w, --wordlists` | 自定义字典文件 | `-w wordlist1.txt wordlist2.txt` |
| `-c, --category` | 字典类别(逗号分隔) | `-c "管理后台路径,API接口路径"` |
| `-e, --extensions` | 扩展名(逗号分隔) | `-e php,jsp,asp` |
| `-f, --force-extensions` | 强制追加扩展名 | `-f` |
| `-O, --overwrite-extensions` | 覆盖已有扩展名 | `-O` |
| `--exclude-extensions` | 排除的扩展名 | `--exclude-extensions css,js` |
| `--prefixes` | 前缀 | `--prefixes .,admin` |
| `--suffixes` | 后缀 | `--suffixes ~,.bak` |
| `-U, --uppercase` | 转大写 | `-U` |
| `-L, --lowercase` | 转小写 | `-L` |
| `-C, --capital` | 首字母大写 | `-C` |

### 通用设置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-t, --threads` | 线程数 | 30 |
| `-r, --recursive` | 递归扫描 | False |
| `--deep-recursive` | 深度递归 | False |
| `--force-recursive` | 强制递归 | False |
| `-R, --recursion-depth` | 递归深度(0=无限) | 0 |
| `--recursion-status` | 递归状态码 | 200-399,401,403 |
| `-i, --include-status` | 包含的状态码 | 200,201,204,301,302,307,308,401,403 |
| `-x, --exclude-status` | 排除的状态码 | 无 |
| `--exclude-sizes` | 排除的响应大小 | 无 |
| `--exclude-text` | 排除的响应文本 | 无 |
| `--exclude-regex` | 排除的正则 | 无 |
| `--exclude-redirect` | 排除的重定向 | 无 |
| `--max-time` | 最大运行时间(秒) | 0(不限) |

### 请求设置

| 参数 | 说明 | 示例 |
|------|------|------|
| `-m, --http-method` | HTTP方法 | `-m POST` |
| `-d, --data` | POST数据 | `-d "user=admin"` |
| `-H, --header` | 自定义请求头 | `-H "Authorization: Bearer xxx"` |
| `-F, --follow-redirects` | 跟随重定向 | `-F` |
| `--random-agent` | 随机User-Agent | `--random-agent` |
| `--user-agent` | 自定义UA | `--user-agent "Custom UA"` |
| `--cookie` | Cookie | `--cookie "session=abc"` |
| `--auth` | 认证 | `--auth "user:pass"` |
| `--auth-type` | 认证类型 | `--auth-type digest` |

### 连接设置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--timeout` | 超时(秒) | 10 |
| `--delay` | 请求延迟(秒) | 0 |
| `--proxy` | 代理地址 | 无 |
| `--proxy-file` | 代理文件 | 无 |
| `--max-rate` | 最大请求速率(每秒) | 0(不限) |
| `--retries` | 重试次数 | 1 |

### 爬虫设置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--no-crawl` | 禁用爬虫模式 | False(默认开启) |
| `--crawl-depth` | 爬虫提取路径的最大深度(0=不限制) | 0 |
| `--no-robots` | 禁用robots.txt解析 | False |
| `--no-sitemap` | 禁用sitemap.xml解析 | False |

### WAF绕过

| 参数 | 说明 |
|------|------|
| `--waf-bypass` | 启用WAF绕过模式(随机UA + IP伪造 + 路径混淆 + 垃圾参数) |
| `--bypass-403` | 启用403绕过模式(路径变形+HTTP方法+IP头伪造+URL重写，共23种路径+120种IP头) |
| `--random-user-agents` | 仅启用随机User-Agent池 |

### 输出设置

| 参数 | 说明 | 可选值 |
|------|------|--------|
| `-o, --output` | 输出文件路径 | 任意路径 |
| `--format` | 输出格式 | plain, json, xml, html, csv, md, simple |
| `--log` | 日志文件路径 | 任意路径 |

### 视图设置

| 参数 | 说明 |
|------|------|
| `--full-url` | 显示完整URL |
| `--no-color` | 禁用颜色输出 |
| `--show-filtered` | 显示被过滤的重复响应 |
| `-q, --quiet` | 静默模式 |

### 历史记录

| 参数 | 说明 |
|------|------|
| `--history` | 查看所有扫描历史 |
| `--clear-history` | 清除全部历史记录 |
| `--clear-history URL` | 清除指定目标的历史 |
| `--force` | 强制重新扫描(忽略历史记录) |

## 状态码过滤

### 默认行为

默认只显示有效状态码，自动过滤无用响应(404/500等)：

```
默认显示: 200, 201, 204, 301, 302, 307, 308, 401, 403
自动过滤: 404, 500, 502, 503 等
```

### 支持格式

| 格式 | 示例 | 说明 |
|------|------|------|
| 单个状态码 | `200,301,403` | 精确匹配 |
| 范围格式 | `200-300` | 200到300之间(含两端) |
| 分类别名 | `2xx` | 200-299全部 |
| 混合格式 | `200,3xx,403` | 组合使用 |

### 用法示例

```bash
# 只显示2xx成功状态码
python dir_scanner.py -u http://target.com --src -i 2xx

# 显示2xx和4xx
python dir_scanner.py -u http://target.com --src -i 2xx,4xx

# 显示200到300之间的状态码
python dir_scanner.py -u http://target.com --src -i 200-300

# 排除3xx重定向
python dir_scanner.py -u http://target.com --src -x 3xx

# 混合: 显示200、全部3xx、403
python dir_scanner.py -u http://target.com --src -i 200,3xx,403

# 显示所有状态码(不过滤)
python dir_scanner.py -u http://target.com --src -i 100-599
```

## 输出说明

### 终端输出

扫描结果按状态码分类显示，带中文标签和时间戳：

```
[14:30:15] 200 -  1.2KB - /admin
[14:30:15] 301 -    0 B - /old-page  ->  /new-page
[14:30:16] 401 -  0.5KB - /api/user
[14:30:16] 403 -  0.3KB - /admin/config
```

### 状态码标签

| 标签 | 颜色 | 含义 |
|------|------|------|
| `命中存活` | 绿底黑字 | 成功访问(200/201/204) |
| `重定向` | 青底黑字 | 重定向(301/302/307/308) |
| `需鉴权` | 黄底黑字 | 需要认证(401) |
| `访问拦截` | 红底黑字 | 禁止访问(403) |
| `请求异常` | 紫底黑字 | 服务端错误(5xx) |

### 扫描摘要

扫描结束后显示统计信息：

```
============================================================
  扫描完成
------------------------------------------------------------
  耗时: 12.5秒
  发现: 8 条有效路径
  爬虫: 15 条路径(从响应中提取)
  ──────────────────────────────
  命中存活  [200]  x3
  重定向    [301]  x2
  需鉴权    [401]  x1
  访问拦截  [403]  x2
============================================================
  爬虫路径自动测试结果
------------------------------------------------------------
  测试路径: 15 条

  命中存活  [200]  x10
    1.2KB  /front/index.html
    3.5KB  /api/user/list [API]
  ...
============================================================
```

### 自动保存结果

扫描结束后自动保存结果到 `results/` 目录，文件名格式 `scan_{host}_{时间戳}.txt`：

```
[*] 结果已保存: D:\gongju\dir_scanner\results\scan_107.174.48.120_8080_20260618_143025.txt
```

使用 `-o` 指定输出文件时不会自动保存。支持 `--format` 指定格式（json/xml/html/csv/md）。

## 高级用法

### 字典模式详解

```bash
# 默认模式 - 使用dirsearch通用字典(9482条)
# 适用场景: 通用Web路径扫描
python dir_scanner.py -u http://target.com

# SRC模式 - 使用全部SRC专项字典(15类别, 8181条)
# 适用场景: SRC漏洞挖掘，需要全面覆盖
python dir_scanner.py -u http://target.com --src

# SRC分类模式 - 指定SRC类别
# 适用场景: 针对性扫描，节省时间
python dir_scanner.py -u http://target.com --src-category "管理后台路径,API接口路径"

# 自定义字典 - 使用自己的字典文件
# 适用场景: 特殊需求
python dir_scanner.py -u http://target.com -w my_wordlist.txt
```

### WAF绕过详解

```bash
# 启用全部WAF绕过技术
python dir_scanner.py -u http://target.com --src --waf-bypass

# 绕过技术包含:
# 1. 随机UA池 - 13个主流浏览器指纹随机切换
# 2. IP伪造 - X-Forwarded-For/X-Real-IP/CF-Connecting-IP等10种头
# 3. 路径混淆 - 大小写随机、分号注入、%09/%20/%00填充
# 4. 垃圾参数 - 随机追加_?t=xxx消耗WAF算力
# 5. 迷惑头 - Sec-Fetch-*、Cache-Control等正常浏览器头
# 6. HTTP方法覆盖 - X-HTTP-Method-Override头
```

### 403 Bypass详解

```bash
# 启用403绕过模式
python dir_scanner.py -u http://target.com --bypass-403

# 原理: 扫描完成后，对所有返回403的路径自动尝试以下绕过技术:

# 路径变形 (23种):
#   /path//, /path/./, //path, //path//, /%2e/path
#   /path/*, /path/*/, /path/..;, //path/..;
#   /path%20, /path%09, /path%00
#   /path.json, /path.css, /path.html
#   /path?, /path??, /path???, /path?testparam
#   /path#, /path#test, /path/.

# HTTP方法: POST替代GET

# IP头伪造 (8种头 x 15种值 = 120种):
#   X-Forwarded-For, X-Real-IP, X-Remote-IP等
#   值: 127.0.0.1, localhost, 0x7F000001, 10.0.0.0等

# URL重写头:
#   X-Original-URL: /path
#   X-Rewrite-URL: /path
```

### 递归扫描

```bash
# 普通递归 - 只递归目录
python dir_scanner.py -u http://target.com --src -r

# 深度递归 - 递归每一级目录
python dir_scanner.py -u http://target.com --src --deep-recursive

# 强制递归 - 强制对所有路径递归
python dir_scanner.py -u http://target.com --src --force-recursive

# 限制递归深度
python dir_scanner.py -u http://target.com --src -r -R 3
```

### 扫描历史

```bash
# 查看所有扫描历史
python dir_scanner.py --history

# 扫描已记录的目标时，自动展示历史结果
python dir_scanner.py -u http://target.com
# 输出: [*] 已扫描过此目标 (使用 --force 强制重新扫描)

# 强制重新扫描
python dir_scanner.py -u http://target.com --force

# 清除指定目标的历史
python dir_scanner.py --clear-history http://target.com

# 清除全部历史
python dir_scanner.py --clear-history
```

### 代理配置

```bash
# 单个代理
python dir_scanner.py -u http://target.com --src --proxy http://127.0.0.1:7890

# 代理文件(随机轮换)
python dir_scanner.py -u http://target.com --src --proxy-file proxies.txt

# SOCKS5代理
python dir_scanner.py -u http://target.com --src --proxy socks5://127.0.0.1:1080
```

### 报告输出

```bash
# JSON格式
python dir_scanner.py -u http://target.com --src -o result.json --format json

# HTML格式(带颜色分类)
python dir_scanner.py -u http://target.com --src -o result.html --format html

# CSV格式(可导入Excel)
python dir_scanner.py -u http://target.com --src -o result.csv --format csv

# Markdown格式
python dir_scanner.py -u http://target.com --src -o result.md --format md

# XML格式
python dir_scanner.py -u http://target.com --src -o result.xml --format xml
```

## 项目结构

```
dir_scanner/
├── dir_scanner.py              # 主入口
├── config.ini                  # 配置文件
├── requirements.txt            # Python依赖
├── README.md                   # 本文档
├── db/                         # 数据目录
│   ├── history.json            # 扫描历史记录
│   ├── 400_blacklist.txt
│   ├── 403_blacklist.txt
│   └── 500_blacklist.txt
├── wordlists/                  # 字典目录
│   ├── dicc.txt                # dirsearch通用字典(9482条)
│   ├── API接口路径.txt          # SRC字典
│   ├── Spring监控端点.txt
│   ├── Web文件.txt
│   ├── 上传下载功能.txt
│   ├── 其他路径.txt
│   ├── 开发测试路径.txt
│   ├── 敏感文件配置.txt
│   ├── 数据库相关.txt
│   ├── 模板变量路径.txt
│   ├── 版本控制相关.txt
│   ├── 目录遍历绕过.txt
│   ├── 管理后台路径.txt
│   ├── 编辑器路径.txt
│   ├── 认证相关路径.txt
│   └── 配置系统路径.txt
├── results/                    # 自动保存的扫描结果
├── end/                        # 测试输出目录
│   └── test_scan.py            # 自动化测试脚本
├── reports/                    # 报告输出目录
└── lib/                        # 核心库
    ├── core/                   # 核心模块
    │   ├── settings.py         # 全局常量和配置
    │   ├── data.py             # 全局数据存储
    │   ├── options.py          # 选项解析
    │   ├── dictionary.py       # 字典加载和处理
    │   ├── fuzzer.py           # 扫描引擎
    │   ├── scanner.py          # Wildcard检测器
    │   ├── crawler.py          # 爬虫模块(HTML/JS/robots/sitemap)
    │   ├── history.py          # 扫描历史管理
    │   ├── pass403.py          # 403绕过引擎
    │   ├── waf_bypass.py       # WAF绕过模块
    │   ├── rate_limiter.py     # 令牌桶限速器
    │   ├── exceptions.py       # 异常定义
    │   ├── decorators.py       # 装饰器
    │   ├── structures.py       # 数据结构
    │   └── logger.py           # 日志模块
    ├── connection/             # 网络连接
    │   ├── requester.py        # HTTP请求器
    │   └── response.py         # 响应封装
    ├── controller/             # 控制器
    │   └── controller.py       # 主控制器(流程编排)
    ├── parse/                  # 解析器
    │   ├── cmdline.py          # 命令行参数
    │   └── url.py              # URL解析
    ├── reports/                # 报告系统
    │   ├── base.py             # 报告基类
    │   ├── json_report.py      # JSON报告
    │   ├── html_report.py      # HTML报告
    │   ├── xml_report.py       # XML报告
    │   ├── csv_report.py       # CSV报告
    │   ├── markdown_report.py  # Markdown报告
    │   ├── plain_text_report.py # 纯文本报告
    │   └── simple_report.py    # 简单报告
    ├── utils/                  # 工具函数
    │   ├── common.py           # 通用工具
    │   ├── file.py             # 文件工具
    │   ├── diff.py             # 差异分析
    │   └── random.py           # 随机生成
    └── view/                   # 终端视图
        ├── terminal.py         # 终端输出
        └── colors.py           # 颜色处理
```

## 架构设计

```
dir_scanner.py (入口)
    │
    ▼
lib.core.options (选项解析)
    │
    ▼
lib.controller.controller (主控制器)
    │
    ├──► lib.core.crawler (爬虫模块)
    │       ├── robots.txt / sitemap.xml 解析
    │       ├── HTML链接属性提取
    │       ├── JS路径提取(支持Vue/React SPA)
    │       └── 爬取路径自动测试可访问性
    │
    ├──► lib.core.dictionary (字典处理)
    │       ├── 默认模式 → wordlists/dicc.txt
    │       ├── SRC模式 → wordlists/SRC字典*.txt
    │       └── SRC分类模式 → wordlists/指定类别.txt
    │
    ├──► lib.core.fuzzer (扫描引擎)
    │       ├── lib.core.scanner (Wildcard检测)
    │       └── lib.connection.requester (HTTP请求)
    │               └── lib.core.waf_bypass (WAF绕过)
    │
    ├──► lib.core.pass403 (403绕过引擎)
    │
    ├──► lib.core.history (扫描历史)
    │
    ├──► lib.reports.* (报告生成)
    │
    └──► lib.view.terminal (终端输出)
```

## 字典模式对比

| 模式 | 参数 | 字典来源 | 条数 | 适用场景 |
|------|------|----------|------|----------|
| 默认模式 | (无) | dicc.txt | 9482 | 通用Web路径扫描 |
| SRC模式 | `--src` | 15个SRC字典 | 8181 | SRC漏洞挖掘 |
| SRC分类模式 | `--src-category` | 指定SRC类别 | 按类别 | 针对性扫描 |
| 自定义模式 | `-w` | 用户指定 | 按文件 | 特殊需求 |

## 与dirsearch对比

| 特性 | dir_scanner | dirsearch |
|------|-------------|-----------|
| 爬虫模式 | 默认开启，自动提取路径并测试 | 支持爬虫 |
| 内置字典 | 双字典模式(通用9482 + SRC 8181) | 通用字典9482 |
| 字典选择 | 支持SRC模式/分类模式/自定义 | 仅支持自定义 |
| WAF绕过 | 6种绕过技术 | 基础UA轮换 |
| 限速控制 | 令牌桶算法 | 滑动窗口 |
| IP伪造 | 10种IP头随机组合 | 无 |
| 路径混淆 | 大小写/分号/编码 | 无 |
| 垃圾参数 | 随机追加消耗WAF | 无 |
| 403 Bypass | 23种路径变形 + 120种IP头 | 无 |
| 状态码过滤 | 默认智能过滤 + 分类别名(2xx) | 显示全部 |
| 输出标签 | 命中存活/重定向/需鉴权/访问拦截 | 无分类 |
| 扫描历史 | 支持历史记录/强制重扫 | 无 |
| 报告格式 | 6种 | 8种 |

## 注意事项

1. **合法授权** - 请确保已获得目标系统的合法授权
2. **爬虫模式** - 默认开启，使用 `--no-crawl` 可禁用
3. **模式选择** - 默认使用dirsearch通用字典，使用 `--src` 启用SRC专项字典
4. **速率控制** - 建议使用 `--max-rate` 限制请求速率，避免对目标造成过大压力
5. **WAF绕过** - `--waf-bypass` 会增加请求的随机性，但可能降低扫描速度
6. **字典选择** - 使用 `--src-category` 指定相关类别，避免扫描无关路径
7. **代理使用** - 建议在测试时使用代理，避免暴露真实IP
8. **状态码过滤** - 默认只显示有效状态码，使用 `-i 100-599` 显示全部
9. **扫描历史** - 重复扫描同一目标时会提示历史记录，使用 `--force` 强制重新扫描

## License

MIT License
