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

# 初始化数据库的数据
def init_data_to_database():
    for mkt in settings.LOCATION:
        if get_count(mkt)==0:
            print("初始化"+mkt)
            url = settings.BINGAPI+"&mkt="+mkt
            json_data=util.get_data(0,url)
            insert_one(mkt,json_data)
            print(mkt+"地区："+str(time.strftime('%Y-%m-%d', time.localtime()))+":今日壁纸添加成功，今日壁纸信息\n"+str(json_data)+"\n")
            print("已收录"+mkt+"地区："+json_data['datetime']+"到"+json_data['datetime']+"的壁纸数据，总计1条")
            print("初始化结束\n")

# 添加数据库数据    
def add_data_to_database():
    for mkt in settings.LOCATION:
        count = get_count(mkt)
        url = settings.BINGAPI+"&mkt="+mkt
        json_data=util.get_data(count,url)
        if cal_date_diff(query_latest_one(mkt)['datetime'],json_data['datetime'])>=1:
            insert_one(mkt,json_data)
            first_data = query_first_one(mkt)
            latest_data = query_latest_one(mkt)
            count = get_count(mkt)
            print(mkt+"地区："+str(time.strftime('%Y-%m-%d', time.localtime()))+":今日壁纸添加成功，今日壁纸信息\n"+str(json_data)+"\n")
            print("已收录"+mkt+"地区："+first_data['datetime']+"到"+latest_data['datetime']+"的壁纸数据，总计"+str(count)+"条")
        else:
            print("集合:"+mkt+":暂无添加数据")

# 添加数据到json 
def add_data_to_json():
    for mkt in settings.LOCATION:
        NOW_DATE=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
        json_data=[]
        for item in get_all_data(mkt):
            json_data.append(item)
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

def cal_date_diff(d1,d2):
    date1 = datetime.datetime.strptime(d1, "%Y-%m-%d").date()  
    date2 = datetime.datetime.strptime(d2, "%Y-%m-%d").date()  
    return (date2 - date1).days
                
if __name__=='__main__':
    init_data_to_database()
    add_data_to_database()
    add_data_to_json()
