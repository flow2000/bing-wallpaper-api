# -*- coding:utf-8 -*-
import sys
import os
import json
import random
import requests
from fastapi.responses import RedirectResponse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from bing_wallpaper_api import settings
from bing_wallpaper_api.utils import util
from api import BingResponse

USE_MONGODB = bool(os.environ.get("MONGODB_URI"))
if USE_MONGODB:
    try:
        from bing_wallpaper_api.utils.mongodb_utils import *
    except ImportError:
        USE_MONGODB = False

def _read_json_data(mkt):
    json_path = os.path.join(BASE_DIR, 'data', f'{mkt}_all.json')
    if not os.path.exists(json_path):
        return []
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('data', [])
    except (json.JSONDecodeError, KeyError):
        return []

def query_all(page, limit, order, w, h, uhd, mkt, year=None):
    if order == "desc":
        order = -1
    else:
        order = 1

    link_str = ""
    if uhd == False:
        link_str = util.contact_w_h(w, h)
    else:
        link_str = "UHD"

    if USE_MONGODB:
        query_params = {
            "page": page,
            "limit": limit,
            "order": order,
            "year": year
        }
        query_result = query_data(mkt, query_params)
        data = []
        for item in query_result:
            item['url'] = item['url'].replace(util.contact_w_h(settings.DEFAULT_W, settings.DEFAULT_H), link_str)
            data.append(item)
        total = get_query_count(mkt, query_params)
        return BingResponse.table_success(data=data, total=total)
    else:
        all_data = _read_json_data(mkt)
        if year:
            all_data = [item for item in all_data if item.get('datetime', '').startswith(f'{year}-')]
        all_data.sort(key=lambda x: x.get('datetime', ''), reverse=(order == -1))
        total = len(all_data)
        start = (page - 1) * limit
        end = start + limit
        page_data = all_data[start:end]
        data = []
        for item in page_data:
            item['url'] = item['url'].replace(util.contact_w_h(settings.DEFAULT_W, settings.DEFAULT_H), link_str)
            data.append(item)
        return BingResponse.table_success(data=data, total=total)

def query_total_num(mkt):
    if USE_MONGODB:
        return BingResponse.success(data=get_count(mkt))
    else:
        all_data = _read_json_data(mkt)
        return BingResponse.success(data=len(all_data))

def latest_one(w, h, uhd, mkt):
    if settings.DEPLOY_TYPE == 'docker':
        if settings.LOCATION.count(mkt) == 0:
            mkt = settings.DEFAULT_MKT
        link_str = w + 'x' + h
        if uhd:
            link_str = 'UHD'
        if USE_MONGODB:
            return RedirectResponse(query_latest_one(mkt)['url'].replace("&rf=LaDigue_1920x1080.jpg&pid=hp", "").replace("1920x1080", link_str))
        else:
            all_data = _read_json_data(mkt)
            if all_data:
                return RedirectResponse(all_data[0]['url'].replace(util.contact_w_h(settings.DEFAULT_W, settings.DEFAULT_H), link_str))
            return BingResponse.error(msg="暂无数据")
    else:
        url = ""
        if settings.LOCATION.count(mkt) > 0:
            url = settings.BINGAPI + "?n=1&format=js&idx=0&mkt=" + mkt
        else:
            url = settings.BINGAPI + "?n=1&format=js&idx=0&mkt=" + settings.DEFAULT_MKT
        data = json.loads(requests.get(url, timeout=util.REQUEST_TIMEOUT).text)
        link_str = w + 'x' + h
        if uhd:
            link_str = 'UHD'
        return RedirectResponse(settings.BINGURL + data['images'][0]['url'].replace("&rf=LaDigue_1920x1080.jpg&pid=hp", "").replace("1920x1080", link_str))

def random_one(w, h, uhd, mkt):
    link_str = w + 'x' + h
    if uhd:
        link_str = 'UHD'
    if USE_MONGODB:
        if settings.LOCATION.count(mkt) > 0:
            url = query_random_one(mkt)['url']
        else:
            url = query_random_one("zh-CN")['url']
        return RedirectResponse(url.replace(util.contact_w_h(settings.DEFAULT_W, settings.DEFAULT_H), link_str))
    else:
        target_mkt = mkt if settings.LOCATION.count(mkt) > 0 else "zh-CN"
        all_data = _read_json_data(target_mkt)
        if all_data:
            url = random.choice(all_data)['url']
            return RedirectResponse(url.replace(util.contact_w_h(settings.DEFAULT_W, settings.DEFAULT_H), link_str))
        return BingResponse.error(msg="暂无数据")
