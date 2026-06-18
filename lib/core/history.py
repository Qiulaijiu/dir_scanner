# -*- coding: utf-8 -*-
"""
扫描历史管理模块
记录已扫描目标，支持历史查询和重新扫描
"""

import json
import os
import time

from lib.core.settings import SCRIPT_PATH
from lib.utils.file import FileUtils

HISTORY_FILE = os.path.join(SCRIPT_PATH, "db", "history.json")


def _load_history():
    """加载历史记录"""
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_history(data):
    """保存历史记录"""
    directory = os.path.dirname(HISTORY_FILE)
    if directory:
        FileUtils.create_dir(directory)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def normalize_url(url):
    """规范化URL用于历史匹配"""
    url = url.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url.lower()


def get_history(url):
    """查询目标的历史扫描记录"""
    history = _load_history()
    key = normalize_url(url)
    return history.get(key)


def save_scan_result(url, results, elapsed_time, wordlist_size, mode, categories=None, crawled_results=None):
    """保存扫描结果到历史"""
    history = _load_history()
    key = normalize_url(url)

    entry = {
        "url": key,
        "scan_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": time.time(),
        "elapsed_time": round(elapsed_time, 1),
        "wordlist_size": wordlist_size,
        "mode": mode,
        "categories": categories,
        "total_found": len(results),
        "status_summary": {},
        "results": [],
        "crawled_results": [],
    }

    for r in results:
        entry["status_summary"][str(r.status)] = entry["status_summary"].get(str(r.status), 0) + 1
        item = {
            "path": "/" + r.full_path.lstrip("/"),
            "status": r.status,
            "length": r.length,
            "content_type": r.type,
        }
        if r.redirect:
            item["redirect"] = r.redirect
        entry["results"].append(item)

    # 保存爬虫路径测试结果
    if crawled_results:
        for r in crawled_results:
            entry["crawled_results"].append({
                "path": r["path"],
                "status": r["status"],
                "length": r["length"],
                "content_type": r.get("type", ""),
                "source": r.get("source", ""),
                "redirect": r.get("redirect", ""),
            })

    history[key] = entry
    _save_history(history)
    return entry


def list_history():
    """列出所有历史记录"""
    return _load_history()


def clear_history(url=None):
    """清除历史记录"""
    if url:
        history = _load_history()
        key = normalize_url(url)
        if key in history:
            del history[key]
            _save_history(history)
            return True
        return False
    else:
        _save_history({})
        return True
