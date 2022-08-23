import requests
import json
import time
import os,stat
import urllib.request
import datetime
import threading
"""

Date: 2022-8-10
Author: 庞海
Description: 下载2009-至今的壁纸

使用方法: 
只需将本程序保存绝对路径上传到指定路径root_path

本程序需要在有网络环境下运行
python执行错误则需要pip安装以上导入的包

"""
# 本程序保存绝对路径
root_path="/www/scheduled_tasks/"
# 图片保存路径
save_path="/www/data/"

headers={
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
}
hash_list=[]

# 创建壁纸保存文件夹
def mkdir(path):
    path = path.rsplit("/",1)[0]
    if not os.path.exists(path):
        os.makedirs(path)
        print(path+"+创建成功")
    return path.rsplit("/",1)[1]

# 计算已下载的壁纸数
def file_count():
    count = 0
    for root,dirs,files in os.walk(save_path+"bing"):    #遍历统计
          for each in files:
                 count += 1
    return count

# 计算当前下载页数
def get_current_page():
    current_page = int(file_count()/10)
    if current_page<=0:
        return 1
    else:
        return current_page

# 获取总页数
def get_total_page():
    url = "https://bing.panghai.top/json/1"
    r = requests.get(url, headers=headers)
    text = r.text  # 获得文本
    data = json.loads(text)
    return data['data']['total_page']

mkdir(root_path)
mkdir(save_path)
total_page=get_total_page()
start_page=get_current_page()
cnt = file_count()
for i in range(start_page,total_page+1):
    print("正在下载第"+str(i)+"页……")
    # 休眠一秒防止api限流
    time.sleep(1)
    url = "https://bing.panghai.top/json/"+str(i)
    r = requests.get(url, headers=headers)
    text = r.text  # 获得文本
    data = json.loads(text)
    lists = data['data']['data']
    for j in range(len(lists)):
        img_url = lists[j]["url"]
        img_path = save_path+lists[j]["path"]
        filename = mkdir(img_path)
        if not os.path.exists(img_path):
            print(img_path+"下载中……")
            urllib.request.urlretrieve(img_url,filename=img_path)
            cnt=cnt+1
        else:
            print(img_path+"已存在，跳过……")

print("下载完毕……")
print("已下载"+str(file_count())+"张图片")