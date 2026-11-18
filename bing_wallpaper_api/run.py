# -*- coding:utf-8 -*-
# @Author: flow2000
import sys
import os
import time
import datetime
import json
import requests
from pymongo import MongoClient
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import settings
from utils import util
if settings.DATABASE=="mongodb":
    from utils.mongodb_utils import *

# 本次运行处理的地区：通过环境变量 BING_MKT 指定单个地区（供分地区定时任务使用），不指定则处理全部地区
def get_locations():
    mkt = os.environ.get("BING_MKT")
    if mkt:
        if mkt not in settings.LOCATION:
            raise ValueError("不支持的地区 BING_MKT=%s，可选值：%s" % (mkt, ", ".join(settings.LOCATION)))
        return [mkt]
    return settings.LOCATION

# 初始化数据库的数据
def init_data_to_database():
    for mkt in get_locations():
        try:
            if get_count(mkt)==0:
                print("初始化"+mkt)
                url = settings.BINGAPI+"?n=1&format=js&idx=0&mkt="+mkt
                json_data=util.get_data(0,url)
                insert_one(mkt,json_data)
                print(str(time.strftime('%Y-%m-%d', time.localtime()))+":今日壁纸添加成功，今日壁纸信息\n"+str(json_data)+"\n")
                print("已收录"+json_data['datetime']+"到"+json_data['datetime']+"的壁纸数据，总计1条")
                print("初始化结束\n")
        except util.BingResponseError as e:
            print("跳过"+mkt+"：必应接口数据异常，本次不初始化："+str(e))

# 添加数据库数据
def add_data_to_database():
    for mkt in get_locations():
        try:
            count = get_count(mkt)
            url = settings.BINGAPI+"?n=1&format=js&idx=0&mkt="+mkt
            json_data=util.get_data(count,url)
            if cal_date_diff(query_latest_one(mkt)['datetime'],json_data['datetime'])>=1:
                insert_one(mkt,json_data)
                first_data = query_first_one(mkt)
                latest_data = query_latest_one(mkt)
                count = get_count(mkt)
                print(str(time.strftime('%Y-%m-%d', time.localtime()))+":今日壁纸添加成功，今日壁纸信息\n"+str(json_data)+"\n")
                print("已收录"+first_data['datetime']+"到"+latest_data['datetime']+"的壁纸数据，总计"+str(count)+"条")
            else:
                print("集合:"+mkt+":暂无添加数据")
        except util.BingResponseError as e:
            print("跳过"+mkt+"：必应接口数据异常，本次不更新："+str(e))

# 把 data/<mkt>_all.json 中数据库缺失的日期补进数据库（只新增，不改动已有记录）
# 用于历史缺口补录：JSON 先补齐，再由每日任务同步进数据库，避免被数据库回写覆盖
def merge_json_missing_dates_to_database():
    for mkt in get_locations():
        path = f'data/{mkt}_all.json'
        if not os.path.exists(path):
            continue
        try:
            db_data = list(get_all_data(mkt))
            db_dates = {item['datetime'] for item in db_data}
            used_ids = {item.get('id') for item in db_data}
            next_id = max([item.get('id') or 0 for item in db_data], default=0)
            for item in read_json(mkt)['data']:
                if item['datetime'] in db_dates:
                    continue
                item = dict(item)
                item.pop('_id', None)
                if item.get('id') in used_ids:
                    while next_id in used_ids:
                        next_id += 1
                    item['id'] = next_id
                used_ids.add(item.get('id'))
                next_id = max(next_id, item.get('id') or 0)
                insert_one(mkt, item)
                db_dates.add(item['datetime'])
                print(mkt+":"+item['datetime']+":JSON 独有日期已补入数据库")
        except Exception as e:
            print("跳过"+mkt+"：JSON 缺失日期补入数据库失败，本次跳过："+str(e))

# 封装json响应结构并写入json文件
def write_bing_json(mkt,json_data):
    NOW_DATE=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
    bing_json_data={}
    bing_json_data['code']=200
    bing_json_data['msg']="操作成功"
    bing_json_data['total']=len(json_data)
    bing_json_data['data']=json_data
    write_json(mkt,bing_json_data)
    print(mkt+":已同步"+NOW_DATE+"json数据")

# 添加数据到json（有 MONGODB_URI 时读数据库）
def add_data_to_json():
    for mkt in get_locations():
        json_data=list(get_all_data(mkt))
        write_bing_json(mkt,json_data)

# 未配置 MONGODB_URI 时：从本地json读取基础数据，直接从必应接口获取今日壁纸并增量追加到json
def add_data_to_json_without_db():
    for mkt in get_locations():
        try:
            json_data = read_json(mkt)['data'] if os.path.exists(f'data/{mkt}_all.json') else []
            exists_dates = {item['datetime'] for item in json_data}
            url = settings.BINGAPI+"?n=1&format=js&idx=0&mkt="+mkt
            json_item = util.get_data(max((item['id'] for item in json_data), default=0), url)
            if json_item['datetime'] not in exists_dates:
                json_data.append(json_item)
                print(mkt+":"+json_item['datetime']+":壁纸追加成功，壁纸信息\n"+str(json_item)+"\n")
            json_data.sort(key=lambda x: x['datetime'], reverse=True)
            write_bing_json(mkt,json_data)
        except util.BingResponseError as e:
            print("跳过"+mkt+"：必应接口数据异常，本次不更新json："+str(e))

def read_json(run_type):
    with open(f'data/{run_type}_all.json', 'r', encoding="utf-8") as f:
        return json.load(f)

def write_json(run_type,data):
    with open(f'data/{run_type}_all.json', 'w', encoding="utf-8") as f:
        json.dump(data,f, indent=2, ensure_ascii=False)

def cal_date_diff(d1,d2):
    date1 = datetime.datetime.strptime(d1, "%Y-%m-%d").date()  
    date2 = datetime.datetime.strptime(d2, "%Y-%m-%d").date()  
    return (date2 - date1).days
                
if __name__=='__main__':
    if not os.environ.get("MONGODB_URI"):
        print("未配置 MONGODB_URI 环境变量，跳过 MongoDB 数据库操作，改为直接从必应接口增量追加到 JSON 文件")
        # 添加数据到json 
        add_data_to_json_without_db()
    else:
        # 初始化数据库数据
        init_data_to_database()
        # 添加数据库数据
        add_data_to_database()
        # 把 JSON 中数据库缺失的日期补进数据库
        merge_json_missing_dates_to_database()
        # 添加数据到json 
        add_data_to_json()
