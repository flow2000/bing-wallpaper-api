# -*- coding:utf-8 -*-
# @Author: flow2000
# 补充数据库以及json文件漏下的壁纸信息
from utils import util
import settings
import sys
import os
import time
from datetime import datetime, timedelta
import json
import requests
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
if settings.DATABASE == "mongodb":
    from utils.mongodb_utils import *

# 本次运行处理的地区：通过环境变量 BING_MKT 指定单个地区（供分地区定时任务使用），不指定则处理全部地区
def get_locations():
    mkt = os.environ.get("BING_MKT")
    if mkt:
        if mkt not in settings.LOCATION:
            raise ValueError("不支持的地区 BING_MKT=%s，可选值：%s" % (mkt, ", ".join(settings.LOCATION)))
        return [mkt]
    return settings.LOCATION

"""
获取数据中日期不连续的部分
@json_data 基础数据列表（每条含 datetime 字段，格式 YYYY-MM-DD）
"""
def get_missing_dates(json_data):
    dates = [datetime.strptime(date['datetime'], '%Y-%m-%d') for date in json_data]
    min_date = min(dates)
    max_date = max(dates)
    all_dates = [min_date + timedelta(days=x) for x in range((max_date - min_date).days + 1)]
    return [date.strftime('%Y-%m-%d') for date in all_dates if date not in dates]

"""
获取近期14天壁纸信息
@mkt 地区
@start_id 起始id，新数据id从 start_id+1 开始递增
"""
def fetch_recent_bing_infos(mkt,start_id):
    last_date_bing_infos = []
    count = start_id
    exists_dates = set()
    for i in [0,6]:
        url = settings.BINGAPI+"?n=8&format=js&idx="+str(i)+"&mkt="+mkt
        try:
            response = requests.get(url, timeout=util.REQUEST_TIMEOUT)
            response.raise_for_status()
            bing_json_data_set = json.loads(response.text)
            images = bing_json_data_set.get('images', []) if isinstance(bing_json_data_set, dict) else []
        except (requests.RequestException, ValueError) as e:
            print(mkt+":获取近期壁纸失败，跳过 idx="+str(i)+"："+str(e))
            continue
        for bing_json_data in images:
            try:
                bing_date = datetime.strptime(bing_json_data['enddate'], "%Y%m%d").strftime("%Y-%m-%d")
                if bing_date in exists_dates:
                    continue
                json_data={}
                json_data['title']=bing_json_data['title']
                json_data['url']=settings.BINGURL+bing_json_data['url'].replace("&rf=LaDigue_1920x1080.jpg&pid=hp","")
                json_data['datetime']=bing_date
                json_data['copyright']=bing_json_data['copyright']
                json_data['copyrightlink']=bing_json_data['copyrightlink']
                json_data['hsh']=bing_json_data['hsh']
                # 字段全部提取成功后再占用一个 id，避免畸形条目空耗 id
                exists_dates.add(bing_date)
                count = count + 1
                json_data['id']=count
                json_data['created_time']=str(time.strftime('%Y-%m-%d', time.localtime()))
                last_date_bing_infos.append(json_data)
            except (KeyError, TypeError, ValueError) as e:
                print(mkt+":跳过一条结构异常的壁纸数据："+str(e))
    return last_date_bing_infos

"""
补充数据库漏下的壁纸信息
1、获取数据库数据
2、找出日期不连续的部分
3、获取近期14天壁纸信息
4、将日期符合不连续部分的壁纸信息插入到数据库
"""
def fix_database_omission_bing():
    for mkt in get_locations():
        print("=======》》》》操作的国家：",mkt)
        # 1、获取数据库数据
        fix_data_list = get_all_data(mkt)
        # 2、找出日期不连续的部分
        missing_dates = get_missing_dates(fix_data_list)
        print("需要补充的日期：",missing_dates)
        # 3、获取近期14天壁纸信息
        last_date_bing_infos = fetch_recent_bing_infos(mkt, get_count(mkt))
        # 4、将日期符合不连续部分的壁纸信息插入到数据库
        for json_data in last_date_bing_infos:
            if json_data['datetime'] in missing_dates:
                insert_one(mkt, json_data)
                print(json_data['datetime'] + ":壁纸补充成功，补充壁纸信息\n"+str(json_data)+"\n")

    pass


"""
补充json文件漏下的壁纸信息
1、获取基础数据（有 MONGODB_URI 时读数据库，否则读 data/<mkt>_all.json）
2、无 MONGODB_URI 时找出日期不连续部分并从必应接口增量追加
3、写入json文件
"""
def fix_file_omission_bing():
    for mkt in get_locations():
        if os.environ.get("MONGODB_URI"):
            json_data=list(get_all_data(mkt))
        else:
            json_data = read_json(mkt)['data'] if os.path.exists(f'data/{mkt}_all.json') else []
            last_date_bing_infos = fetch_recent_bing_infos(mkt, max((item['id'] for item in json_data), default=0))
            missing_dates = get_missing_dates(json_data) if json_data else []
            print("需要补充的日期：",missing_dates)
            for json_item in last_date_bing_infos:
                if not json_data or json_item['datetime'] in missing_dates:
                    json_data.append(json_item)
                    print(json_item['datetime'] + ":壁纸补充成功，补充壁纸信息\n"+str(json_item)+"\n")
            json_data.sort(key=lambda x: x['datetime'], reverse=True)
        write_bing_json(mkt,json_data)

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

def read_json(run_type):
    with open(f'data/{run_type}_all.json', 'r', encoding="utf-8") as f:
        return json.load(f)

def write_json(run_type,data):
    with open(f'data/{run_type}_all.json', 'w', encoding="utf-8") as f:
        json.dump(data,f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    if not os.environ.get("MONGODB_URI"):
        print("未配置 MONGODB_URI 环境变量，跳过 MongoDB 数据库操作，改为直接从必应接口增量追加到 JSON 文件")
    else:
        # 补充数据库漏下的壁纸信息
        fix_database_omission_bing()

    # 补充json文件漏下的壁纸信息
    fix_file_omission_bing()