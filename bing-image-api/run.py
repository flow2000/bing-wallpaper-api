# -*- coding:utf-8 -*-
# @Author: flow2000
import requests
import json
import random
import sys
import os
import time
now_date = time.strftime('%Y-%m-%d', time.localtime())

from pymongo import MongoClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from utils import mogodb_utils

# os.environ["MONGODB_URI"]="mongodb://127.0.0.1:27017/"

JSON_URL="https://bing.json1.shinie.top/"
IMG_URL="https://cn.bing.com/HPImageArchive.aspx?n=1&format=js&idx=0&mkt=zh-CN"
BING_URL="https://cn.bing.com"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
}


def add_all_data():
    print("初始化数据中……")
    time_begin = time.time()
    data=json.loads(requests.get(JSON_URL+"1.json",headers=headers).text)
    end_page=data['data']['total_page']
    start_page=279 #只选择有必应图片链接的数据
    id=1
    tmp_lists=[]
    for i in range(start_page,end_page+1):
        # 休眠0.3秒防止api限流
        time.sleep(0.3)
        data=json.loads(requests.get(JSON_URL+str(i)+".json",headers=headers).text)
        lists=data['data']['data']
        for j in range(len(lists)):
            if lists[j]['url'].find("https://cn.bing.com")!=-1:
                lists[j].pop("path","None")
                lists[j].pop("hsh","None")
                lists[j].pop("view","None")
                lists[j].pop("down","None")
                lists[j].pop("like","None")
                lists[j]['id']=id
                lists[j]['created_time']=now_date
                id=id+1
                lists[j]['url']=lists[j]['url'].replace("&rf=LaDigue_1920x1080.jpg&pid=hp","")
                tmp_lists.append(lists[j])
    mogodb_utils.insert_many(tmp_lists)
                
def add_data():
    data = mogodb_utils.query_latest_one()
    count = mogodb_utils.get_count()
    if data['datetime'] != now_date:
        json_data={}
        bing_json_data=json.loads(requests.get(IMG_URL).text)
        json_data['id']=count+1
        json_data['title']=bing_json_data['images'][0]['title']
        json_data['copyright']=bing_json_data['images'][0]['copyright']
        json_data['url']=BING_URL+bing_json_data['images'][0]['url']
        json_data['datetime']=str(now_date)
        json_data['created_time']=str(now_date)
        mogodb_utils.insert_one(json_data)
        print(str(now_date)+":今日壁纸添加成功，今日壁纸信息\n"+str(json_data)+"\n")
    else:
        print("暂无添加数据")
                
if __name__=='__main__':
    if mogodb_utils.get_count()==0:
        add_all_data()
    elif mogodb_utils.query_latest_one()['datetime']!=now_date:
        add_data()
    count = mogodb_utils.get_count()
    first_data = mogodb_utils.query_first_one()
    latest_data = mogodb_utils.query_latest_one()
    print("已收录"+first_data['datetime']+"到"+latest_data['datetime']+"的壁纸数据，总计"+str(count)+"条")
