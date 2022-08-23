import requests
import json
import time
import os,stat
import urllib.request
import datetime
"""

Date: 2022-8-10
Author: 庞海
Description: 创建2009-至今的api数据

使用方法: 只需修改本程序保存绝对路径(root_path)和七牛云域名(cnd_url)
本程序需要在有网络环境下运行
python执行错误则需要pip安装以上导入的包

"""
# 本程序保存绝对路径
root_path="/www/scheduled_tasks/"
# 你的七牛云域名，没有则留空 cnd_url=""
cnd_url="cdn.panghai.top"
# json保存路径
save_path="/www/data/json/"
# 当前日期 例如：2022-08-10
now_date = time.strftime('%Y-%m-%d', time.localtime())
headers={
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
}

# 创建json文件夹
if not os.path.exists(save_path):
        os.makedirs(save_path)

# 计算文件数
def file_count():
    count = 0
    for root,dirs,files in os.walk(save_path):    #遍历统计
          for each in files:
                 count += 1
    return count

# 计算当前下载页数
def get_current_page():
    current_page = int(file_count())
    if current_page<=0:
        return 1
    else:
        return current_page

# 获取总页数
def get_total_page():
    url = "http://bing.panghai.top/json/1"
    r = requests.get(url, headers=headers)
    text = r.text  # 获得文本
    data = json.loads(text)
    return data['data']['total_page']

# 读取json
def read_json(name):
    with open(save_path+name,'r') as load_f:
        return json.load(load_f)

# 写入json
def write_json(name,data):
    with open(save_path+name,"w",encoding='utf-8') as f:
        json.dump(data,f, ensure_ascii=False)

# 替换url
def replace_url(url):
    if url.find("cn.bing.com")==-1 and cnd_url!="":
        return url.replace("cdn.panghai.top",cnd_url)
    else:
        return url

# 创建json数据
def create_json(data):
    res={}
    res["code"]=200
    res["data"]=data
    res["msg"]="操作成功"
    return res

total_page=get_total_page()
start_page=get_current_page()
for i in range(start_page,total_page+1):
    print("正在下载第"+str(i)+"页……")
    # 休眠一秒防止api限流
    # time.sleep(1)
    url = "http://bing.panghai.top/json/"+str(i)
    data = json.loads(requests.get(url, headers=headers).text)
    lists = data['data']['data']
    json_data = {}
    json_data["current_page"] = data["data"]["current_page"]
    json_data["total_page"] = data["data"]["total_page"]
    json_list = []
    for j in range(len(lists)):
        pic = {}
        pic["id"] = lists[j]["id"]
        pic["title"] = lists[j]["title"]
        pic["copyright"] = lists[j]["copyright"]
        pic["url"] = replace_url(lists[j]["url"])
        pic["path"] = lists[j]["path"]
        pic["datetime"] = lists[j]["datetime"]
        pic["hsh"] = lists[j]["hsh"]
        pic["view"] = 0
        pic["down"] = 0
        pic["like"] = 0
        pic["created_time"] = now_date
        json_list.append(pic)
    json_data["data"]=json_list
    write_json(str(i)+".json",create_json(json_data))

print("下载完毕……")