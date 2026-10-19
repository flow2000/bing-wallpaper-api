#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从本仓库 data 目录的 {mkt}_all.json 生成 bimg.cc 的 sitemap.xml。

数据流向：本脚本在 bing-wallpaper-api 仓库内运行，直接读取本地 data/*.json；
生成的 sitemap.xml 提交到本仓库 sitemap/sitemap.xml，站点仓库 bing-wallpaper
在构建时（prebuild 钩子）从 GitHub raw 拉取该文件打包进 dist。

包含的页面类型（按 SEO 优先级排序）：
  1. 首页        https://bimg.cc/index.html          priority=1.0  changefreq=daily
  2. 关于页      https://bimg.cc/about.html          priority=0.5  changefreq=monthly
  3. 地区页      https://bimg.cc/region/{mkt}.html   priority=0.9  changefreq=daily
  4. 壁纸详情页  https://bimg.cc/wallpaper/detail/{mkt}-{id}.html
                                                        priority=0.8  changefreq=yearly

URL 格式与壁纸项目 prerender.js 保持一致。

用法：
  python sitemap/generate_sitemap.py                 # 生成所有地区的 sitemap.xml
  python sitemap/generate_sitemap.py zh-CN           # 仅生成指定地区的 sitemap.xml
  python sitemap/generate_sitemap.py -o sitemap.xml  # 指定输出文件路径
"""
import json
import os
import sys
from datetime import date
from xml.dom import minidom
from xml.etree import ElementTree as ET

SITE = "https://bimg.cc"

# 地区列表（与 submit_seo.py、站点 prerender.js 保持一致）
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
DATA_DIR = os.path.join(REPO_ROOT, "data")
DEFAULT_OUTPUT = os.path.join(BASE_DIR, "sitemap.xml")


def _today_str():
    """返回今天的日期字符串 YYYY-MM-DD。"""
    return date.today().isoformat()


def fetch_wallpapers(mkt):
    """
    读取本地 data/{mkt}_all.json，解析壁纸列表。
    返回 [(id, datetime_str), ...]，按 id 降序排列。
    """
    path = os.path.join(DATA_DIR, "{mkt}_all.json".format(mkt=mkt))
    if not os.path.exists(path):
        print("[error] 数据文件不存在: {p}，跳过该地区".format(p=path))
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            body = json.load(f)
    except (ValueError, IOError) as e:
        print("[error] {mkt} 数据文件解析失败: {err}，跳过该地区".format(mkt=mkt, err=e))
        return []

    if body.get("code") != 200:
        print("[error] {mkt} JSON 返回错误: code={code} msg={msg}".format(
            mkt=mkt, code=body.get("code"), msg=body.get("msg")
        ))
        return []

    data = body.get("data", [])
    items = []
    seen = set()
    for item in data:
        pid = item.get("id")
        if pid is None or pid in seen:
            continue
        seen.add(pid)
        dt = item.get("datetime") or item.get("created_time") or ""
        items.append((pid, dt))

    # 按 id 降序排列
    items.sort(key=lambda x: x[0], reverse=True)
    print("[fetch] {mkt}: 共 {n} 条（本地 data/{mkt}_all.json）".format(
        mkt=mkt, n=len(items)
    ))
    return items


def _add_url(urlset, loc, lastmod=None, changefreq=None, priority=None):
    """向 urlset 中添加一个 <url> 节点。"""
    url_elem = ET.SubElement(urlset, "url")

    loc_elem = ET.SubElement(url_elem, "loc")
    loc_elem.text = loc

    if lastmod:
        lastmod_elem = ET.SubElement(url_elem, "lastmod")
        lastmod_elem.text = lastmod

    if changefreq:
        changefreq_elem = ET.SubElement(url_elem, "changefreq")
        changefreq_elem.text = changefreq

    if priority:
        priority_elem = ET.SubElement(url_elem, "priority")
        priority_elem.text = priority


def generate_sitemap(regions, output_path):
    """
    生成 sitemap.xml 文件。

    Args:
        regions: 要包含的地区列表
        output_path: 输出文件路径（含文件名）
    """
    today = _today_str()

    urlset = ET.Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    total = 0
    region_data = {}  # mkt -> [(id, dt), ...]

    # ---------- 1. 首页（优先级最高） ----------
    _add_url(
        urlset,
        loc=SITE + "/index.html",
        lastmod=today,
        changefreq="daily",
        priority="1.0",
    )
    total += 1

    # ---------- 2. 关于页 ----------
    _add_url(
        urlset,
        loc=SITE + "/about.html",
        lastmod=today,
        changefreq="monthly",
        priority="0.5",
    )
    total += 1

    # ---------- 3. 地区页 ----------
    for mkt in regions:
        wallpapers = fetch_wallpapers(mkt)
        region_data[mkt] = wallpapers
        # 地区页的 lastmod 使用该地区最新壁纸的发布日期，没有则用今天
        latest_date = wallpapers[0][1] if wallpapers else today
        _add_url(
            urlset,
            loc="{site}/region/{mkt}.html".format(site=SITE, mkt=mkt),
            lastmod=latest_date or today,
            changefreq="daily",
            priority="0.9",
        )
        total += 1

    # ---------- 4. 壁纸详情页 ----------
    for mkt in regions:
        wallpapers = region_data.get(mkt, [])
        for pid, dt in wallpapers:
            _add_url(
                urlset,
                loc="{site}/wallpaper/detail/{mkt}-{pid}.html".format(
                    site=SITE, mkt=mkt, pid=pid
                ),
                lastmod=dt if dt else None,
                changefreq="yearly",
                priority="0.8",
            )
            total += 1

        print("[sitemap] {mkt}: 地区页 1 + 详情页 {n} 条".format(
            mkt=mkt, n=len(wallpapers)
        ))

    # 写入文件（使用 minidom 美化缩进，保证 XML 格式规范）
    rough_string = ET.tostring(urlset, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(pretty_xml)

    detail_count = total - 2 - len(regions)
    print("[sitemap] 总计 {total} 条 URL（首页 1 + 关于页 1 + 地区页 {nr} + 详情页 {nd}），已写入: {path}".format(
        total=total,
        nr=len(regions),
        nd=detail_count,
        path=output_path,
    ))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="生成 Bing 壁纸 sitemap.xml")
    parser.add_argument(
        "region",
        nargs="?",
        default=None,
        help="指定地区（如 zh-CN），不指定则生成所有地区",
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT,
        help="输出文件路径，默认 sitemap/sitemap.xml",
    )
    args = parser.parse_args()

    # 确定地区列表
    if args.region:
        if args.region not in REGIONS:
            print("[error] 未知地区: {r}，支持的地区: {regions}".format(
                r=args.region, regions=", ".join(REGIONS)
            ))
            sys.exit(1)
        regions = [args.region]
    else:
        regions = REGIONS

    output_path = args.output
    print("[sitemap] 生成地区: {regions}".format(regions=", ".join(regions)))
    generate_sitemap(regions, output_path)


if __name__ == "__main__":
    main()
