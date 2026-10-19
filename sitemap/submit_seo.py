#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提交 bimg.cc 链接到必应 IndexNow 与百度搜索收录。

一、固定页面（每天必提，仅必应 IndexNow；URL 不随壁纸数据变化）：
  首页    https://bimg.cc/index.html
  关于页  https://bimg.cc/about.html
  地区页  https://bimg.cc/region/{mkt}.html
即使当天没有新增壁纸，这些固定页面也会每天向必应 IndexNow 提交一次。

二、本次新增的壁纸详情页（必应 IndexNow + 百度）：
  详情页  https://bimg.cc/wallpaper/detail/{mkt}-{id}.html
新增判定：对比本次 GitHub Actions 运行开始时的基线提交（环境变量
GITHUB_SHA）中的 sitemap/sitemap.xml 与当前工作区刚生成的
sitemap/sitemap.xml，取 URL 差集，仅提交这些新增页面，不再全量提交。

百度每日配额有限（默认 20 条），固定页面不重复占用百度配额，仅提交新增详情页。

IndexNow key 与 keyLocation 与站点 static 目录下的 key 文件保持一致。
百度 token 通过环境变量 BAIDU_TOKEN 注入（GitHub Secrets）。

配额与批次大小均可通过环境变量调整，便于后续变更：
  INDEXNOW_BATCH       必应每批提交条数，默认 10000（官方上限 10000）
  INDEXNOW_DAILY_LIMIT 必应每日提交上限（条），默认 0 = 不限制
  BAIDU_BATCH          百度每批提交条数，默认 20
  BAIDU_DAILY_LIMIT    百度每日提交上限（条），默认 20
"""
import os
import re
import subprocess
import time
from xml.etree import ElementTree as ET

import requests

SITE = "https://bimg.cc"
HOST = "bimg.cc"

# 地区列表（与 generate_sitemap.py、站点 prerender.js 保持一致，按优先级排序）
REGIONS = [
    "zh-CN",
    "en-US",
    "ja-JP",
    "de-DE",
    "en-GB",
    "fr-FR",
    "it-IT",
    "en-CA",
    "en-IN",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.join(BASE_DIR, "..")
SITEMAP_PATH = os.path.join(REPO_ROOT, "sitemap", "sitemap.xml")
SITEMAP_GIT_PATH = "sitemap/sitemap.xml"

INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "").strip()
INDEXNOW_API = "https://api.indexnow.org/IndexNow"

BAIDU_API = "http://data.zz.baidu.com/urls?site={site}&token={token}".format(
    site=SITE, token="{token}"
)

# ---- 可配置的配额 / 批次大小（环境变量覆盖） ----
INDEXNOW_BATCH = int(os.environ.get("INDEXNOW_BATCH", 10000))
INDEXNOW_DAILY_LIMIT = int(os.environ.get("INDEXNOW_DAILY_LIMIT", 0))  # 0 = 不限制

BAIDU_BATCH = int(os.environ.get("BAIDU_BATCH", 20))
BAIDU_DAILY_LIMIT = int(os.environ.get("BAIDU_DAILY_LIMIT", 20))

# sitemap 命名空间
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def _extract_urls(xml_text):
    """从 sitemap XML 文本中提取所有 <loc> URL。"""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return set()
    return {loc.text for loc in root.findall("sm:url/sm:loc", NS) if loc.text}


def _git_show(ref, rel_path):
    return subprocess.run(
        ["git", "show", "{ref}:{path}".format(ref=ref, path=rel_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def baseline_ref():
    ref = os.environ.get("GITHUB_SHA", "").strip()
    return ref or "HEAD^"


def ref_exists(ref):
    try:
        subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except Exception:
        return False


def _detail_sort_key(url):
    """按地区和壁纸 id 排序详情页 URL（与 REGIONS 优先级一致，id 小的在前）。"""
    m = re.search(r"/wallpaper/detail/([a-zA-Z-]+)-(\d+)\.html", url)
    if not m:
        return (len(REGIONS), 0)
    mkt, pid = m.group(1), int(m.group(2))
    try:
        region_rank = REGIONS.index(mkt)
    except ValueError:
        region_rank = len(REGIONS)
    return (region_rank, pid)


def collect_new_urls():
    """对比基线 sitemap 与当前 sitemap，收集新增的壁纸详情页 URL。"""
    ref = baseline_ref()
    if not ref_exists(ref):
        print(
            "[collect] 无法确定基线提交 {ref}，跳过本次提交"
            "（本地调试请确认已 git fetch）".format(ref=ref)
        )
        return []

    if not os.path.exists(SITEMAP_PATH):
        print("[collect] 当前 sitemap 不存在: {p}，跳过".format(p=SITEMAP_PATH))
        return []

    with open(SITEMAP_PATH, "r", encoding="utf-8") as f:
        current_urls = _extract_urls(f.read())

    try:
        baseline_urls = _extract_urls(_git_show(ref, SITEMAP_GIT_PATH))
    except Exception:
        # 基线提交中不存在 sitemap（首次运行），无法判定新增，跳过以免全量提交
        print("[collect] 基线提交 {ref} 中无 sitemap，跳过新增提交".format(ref=ref))
        return []

    added = sorted(
        (u for u in current_urls - baseline_urls if "/wallpaper/detail/" in u),
        key=_detail_sort_key,
    )
    if added:
        print("[collect] 新增详情页 {n} 条，示例: {sample}".format(
            n=len(added), sample=", ".join(added[:5])
        ))
    else:
        print("[collect] 本次无新增详情页")
    return added


def collect_fixed_urls():
    """收集 bimg.cc 固定页面 URL：首页、关于页、各地区页。

    这些 URL 不随壁纸数据增减而变化，但首页/地区页内容每日更新，
    因此每天都向必应 IndexNow 提交一次，提示搜索引擎重新抓取。
    URL 与 generate_sitemap.py 保持一致。
    """
    urls = [
        "{site}/index.html".format(site=SITE),
        "{site}/about.html".format(site=SITE),
    ]
    urls.extend(
        "{site}/region/{mkt}.html".format(site=SITE, mkt=mkt)
        for mkt in REGIONS
    )
    return urls


def _truncate(urls, limit):
    """按每日上限截断 URL 列表，返回截断后的列表。"""
    if limit and limit > 0 and len(urls) > limit:
        print(
            "[limit] 待提交 {total} 条，超过每日上限 {limit}，"
            "仅提交前 {limit} 条".format(total=len(urls), limit=limit)
        )
        return urls[:limit]
    return urls


def submit_indexnow(urls):
    if not INDEXNOW_KEY:
        print("[IndexNow] 未设置 INDEXNOW_KEY，跳过必应收录提交")
        return
    total = len(urls)
    if total == 0:
        print("[IndexNow] 无待提交链接，跳过")
        return

    urls = _truncate(urls, INDEXNOW_DAILY_LIMIT)
    total_submit = len(urls)

    ok = 0
    base = {
        "host": HOST,
        "key": INDEXNOW_KEY,
        "keyLocation": "{site}/{key}.txt".format(site=SITE, key=INDEXNOW_KEY),
    }
    batch_size = max(1, INDEXNOW_BATCH)
    batches = (total_submit + batch_size - 1) // batch_size
    for i in range(0, total_submit, batch_size):
        chunk = urls[i : i + batch_size]
        body = dict(base, urlList=chunk)
        batch_no = i // batch_size + 1
        try:
            r = requests.post(INDEXNOW_API, json=body, timeout=30)
            print(
                "[IndexNow] batch {batch}/{batches} ({n} 条): HTTP {code} {text}".format(
                    batch=batch_no,
                    batches=batches,
                    n=len(chunk),
                    code=r.status_code,
                    text=r.text.strip()[:300],
                )
            )
            if r.status_code in (200, 202):
                ok += len(chunk)
            else:
                print(
                    "[IndexNow] 警告：第 {batch} 批提交失败（HTTP {code}）".format(
                        batch=batch_no, code=r.status_code
                    )
                )
        except Exception as e:
            print("[IndexNow] batch {batch} error: {err}".format(batch=batch_no, err=e))
        time.sleep(1)
    print("[IndexNow] 成功提交 {ok}/{total} 条".format(ok=ok, total=total_submit))


def submit_baidu(urls):
    token = os.environ.get("BAIDU_TOKEN", "").strip()
    if not token:
        print("[Baidu] 未设置 BAIDU_TOKEN，跳过百度提交")
        return
    total = len(urls)
    if total == 0:
        print("[Baidu] 无新增链接，跳过")
        return

    # 先按每日配额上限截断
    urls = _truncate(urls, BAIDU_DAILY_LIMIT)
    total_submit = len(urls)

    ok = 0
    remain_quota = None  # 服务端返回的当日剩余配额
    api = BAIDU_API.format(token=token)
    batch_size = max(1, BAIDU_BATCH)
    batches = (total_submit + batch_size - 1) // batch_size

    for i in range(0, total_submit, batch_size):
        chunk = urls[i : i + batch_size]
        batch_no = i // batch_size + 1

        # 如果已知剩余配额，且本批条数超过剩余配额，缩小本批
        if remain_quota is not None and remain_quota < len(chunk):
            if remain_quota <= 0:
                print("[Baidu] 剩余配额为 0，停止提交")
                break
            chunk = chunk[:remain_quota]
            print(
                "[Baidu] 剩余配额不足，本批调整为 {n} 条".format(n=len(chunk))
            )

        body = "\n".join(chunk)
        try:
            r = requests.post(
                api,
                data=body.encode("utf-8"),
                headers={"Content-Type": "text/plain; charset=utf-8"},
                timeout=60,
            )
            resp = None
            try:
                resp = r.json()
            except ValueError:
                resp = None

            print(
                "[Baidu] batch {batch}/{batches} ({n} 条): HTTP {code}".format(
                    batch=batch_no,
                    batches=batches,
                    n=len(chunk),
                    code=r.status_code,
                )
            )

            if r.status_code == 200 and resp is not None:
                # 成功响应
                success = int(resp.get("success", 0) or 0)
                remain = resp.get("remain")
                not_same_site = resp.get("not_same_site") or []
                not_valid = resp.get("not_valid") or []

                ok += success
                if remain is not None:
                    remain_quota = int(remain)
                    print(
                        "[Baidu] 本批成功 {success} 条，当日剩余配额 remain={remain}".format(
                            success=success, remain=remain
                        )
                    )
                else:
                    print("[Baidu] 本批成功 {success} 条".format(success=success))

                if not_same_site:
                    print(
                        "[Baidu] 非本站 URL（{n} 条）：{urls}".format(
                            n=len(not_same_site),
                            urls=", ".join(not_same_site[:5]) + ("..." if len(not_same_site) > 5 else ""),
                        )
                    )
                if not_valid:
                    print(
                        "[Baidu] 不合法 URL（{n} 条）：{urls}".format(
                            n=len(not_valid),
                            urls=", ".join(not_valid[:5]) + ("..." if len(not_valid) > 5 else ""),
                        )
                    )

                # 配额用尽，提前退出
                if remain_quota is not None and remain_quota <= 0:
                    print("[Baidu] 当日配额已用尽，停止后续批次")
                    break
            else:
                # 失败响应（4xx 等）
                err_code = None
                err_msg = None
                if resp is not None:
                    err_code = resp.get("error")
                    err_msg = resp.get("message")
                if err_code is not None or err_msg is not None:
                    print(
                        "[Baidu] 错误：error={code} message={msg}".format(
                            code=err_code, msg=err_msg
                        )
                    )
                else:
                    print("[Baidu] 错误：HTTP {code} {text}".format(
                        code=r.status_code, text=r.text[:300]
                    ))
                # 4xx 通常是配置问题，没必要继续后续批次
                if r.status_code >= 400 and r.status_code < 500:
                    print("[Baidu] 客户端错误，停止后续批次")
                    break
        except Exception as e:
            print("[Baidu] batch {batch} error: {err}".format(batch=batch_no, err=e))
        time.sleep(2)

    print("[Baidu] 成功提交 {ok}/{total} 条".format(ok=ok, total=total_submit))


def main():
    new_urls = collect_new_urls()
    fixed_urls = collect_fixed_urls()
    print("固定页面 URL（每天提交必应）：{n} 条".format(n=len(fixed_urls)))
    print("本次新增详情页 URL：{n} 条".format(n=len(new_urls)))

    print(
        "[config] IndexNow: batch={ib}, daily_limit={idl} | "
        "Baidu: batch={bb}, daily_limit={bdl}".format(
            ib=INDEXNOW_BATCH,
            idl=INDEXNOW_DAILY_LIMIT or "unlimited",
            bb=BAIDU_BATCH,
            bdl=BAIDU_DAILY_LIMIT,
        )
    )

    # 必应 IndexNow：固定页面排在前面（每日上限截断时优先保留），叠加本次新增详情页；
    # 即使当天没有新增壁纸，固定页面也会每天提交
    submit_indexnow(fixed_urls + new_urls)

    # 百度每日配额有限，仅提交本次新增详情页，固定页面不重复占用配额
    submit_baidu(new_urls)


if __name__ == "__main__":
    main()
