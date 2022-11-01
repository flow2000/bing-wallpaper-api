# -*- coding:utf-8 -*-
# @Author: flow2000
import sys
import os
import time
import json
import requests
from pymongo import MongoClient
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import settings
from utils import util
if settings.DATABASE=="mongodb":
    from utils.mongodb_utils import *

# 初始化数据库的数据
def init_data_to_database():
    for mkt in settings.LOCATION:
        if get_count(mkt)==0:
            print("初始化"+mkt)
            url = settings.BINGAPI+"&mkt="+mkt
            json_data=util.get_data(0,url)
            insert_one(mkt,json_data)
            print(str(time.strftime('%Y-%m-%d', time.localtime()))+":今日壁纸添加成功，今日壁纸信息\n"+str(json_data)+"\n")
            print("已收录"+json_data['datetime']+"到"+json_data['datetime']+"的壁纸数据，总计1条")
            print("初始化结束\n")

# 添加数据库数据    
def add_data_to_database():
    for mkt in settings.LOCATION:
        count = get_count(mkt)
        url = settings.BINGAPI+"&mkt="+mkt
        json_data=util.get_data(count,url)
        if query_latest_one(mkt)['datetime']!=json_data['datetime']:
            insert_one(mkt,json_data)
            first_data = query_first_one(mkt)
            latest_data = query_latest_one(mkt)
            count = get_count(mkt)
            print(str(time.strftime('%Y-%m-%d', time.localtime()))+":今日壁纸添加成功，今日壁纸信息\n"+str(json_data)+"\n")
            print("已收录"+first_data['datetime']+"到"+latest_data['datetime']+"的壁纸数据，总计"+str(count)+"条")
        else:
            print("集合:"+mkt+":暂无添加数据")

# 添加数据到json 
def add_data_to_json():
    for mkt in settings.LOCATION:
        bing_json_data=read_json(mkt)
        bing_lists=bing_json_data['data']
        timearray=time.strptime(str(bing_lists[0]['enddate']),'%Y%m%d')
        datetime=time.strftime('%Y-%m-%d', timearray)
        url = settings.BINGAPI+"&mkt="+mkt
        json_data=util.get_data(len(bing_lists),url)
        NOW_DATE=json_data['datetime']
        if datetime!=NOW_DATE:
            print(mkt+":已添加"+NOW_DATE+"json数据")
            json_data=json.loads(requests.get(url).text)['images'][0]
            bing_lists.insert(0, json_data)
            bing_json_data['data']=bing_lists
            bing_json_data['update_time']=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
            bing_json_data['total']=len(bing_lists)
            write_json(mkt,bing_json_data)
        else:
            print("json:"+mkt+":暂无添加数据")

def read_json(run_type):
    with open(f'data/{run_type}_all.json', 'r', encoding="utf-8") as f:
        return json.load(f)

def write_json(run_type,data):
    with open(f'data/{run_type}_all.json', 'w', encoding="utf-8") as f:
        json.dump(data,f, indent=2, ensure_ascii=False)
                
if __name__=='__main__':
    init_data_to_database()
    add_data_to_database()
    add_data_to_json()
