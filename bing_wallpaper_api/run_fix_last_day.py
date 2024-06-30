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

"""
补充数据库漏下的壁纸信息
1、获取数据库数据
2、获取数据的日期字段信息
3、找出日期不连续的部分
4、获取近期14天壁纸信息
5、找出壁纸信息的日期是否符合日期不连续列表
6、将不连续日期的壁纸信息插入到数据库
"""
def fix_database_omission_bing():
    for mkt in settings.LOCATION:
        print("=======》》》》操作的国家：",mkt)
        # 1、获取数据库数据
        fix_data_list = get_all_data(mkt)
        # 2、获取数据的日期字段信息
        dates = [datetime.strptime(date['datetime'], '%Y-%m-%d') for date in fix_data_list]
        min_date = min(dates)
        max_date = max(dates)
        all_dates = [min_date + timedelta(days=x) for x in range((max_date - min_date).days + 1)]
        # 3、找出日期不连续的部分
        missing_dates = [date.strftime('%Y-%m-%d') for date in all_dates if date not in dates]
        print("需要补充的日期：",missing_dates)
        # 4、获取近期14天壁纸信息
        last_date_bing_infos = []
        for i in [0,6]:
            url = settings.BINGAPI+"?n=8&format=js&idx="+str(i)+"&mkt="+mkt
            count = get_count(mkt)
            bing_json_data_set = json.loads(requests.get(url).text)
            for bing_json_data in bing_json_data_set['images']:
                json_data={}
                count = count + 1
                json_data['id']=count+1
                json_data['title']=bing_json_data['title']
                json_data['url']=settings.BINGURL+bing_json_data['url'].replace("&rf=LaDigue_1920x1080.jpg&pid=hp","")
                json_data['datetime']=datetime.strptime(bing_json_data['enddate'], "%Y%m%d").strftime("%Y-%m-%d")
                json_data['copyright']=bing_json_data['copyright']
                json_data['copyrightlink']=bing_json_data['copyrightlink']
                json_data['hsh']=bing_json_data['hsh']
                json_data['created_time']=str(time.strftime('%Y-%m-%d', time.localtime()))
                last_date_bing_infos.append(json_data)

        # 5、找出壁纸信息的日期是否符合日期不连续列表
        for json_data in last_date_bing_infos:
            if json_data['datetime'] in missing_dates:
                # 6、将不连续日期的壁纸信息插入到数据库
                insert_one(mkt, json_data)
                print(json_data['datetime'] + ":壁纸补充成功，补充壁纸信息\n"+str(json_data)+"\n")

    pass


"""
补充json文件漏下的壁纸信息
1、获取数据库所有壁纸信息
2、写入json文件
"""
def fix_file_omission_bing():
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


def write_json(run_type,data):
    with open(f'data/{run_type}_all.json', 'w', encoding="utf-8") as f:
        json.dump(data,f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    # 补充数据库漏下的壁纸信息
    fix_database_omission_bing()

    # 补充json文件漏下的壁纸信息
    fix_file_omission_bing()