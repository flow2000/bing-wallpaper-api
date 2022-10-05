import requests
import json
import time
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import settings

# 获取必应接口数据
def get_data(id,url):
    json_data={}
    bing_json_data=json.loads(requests.get(url).text)
    json_data['id']=id+1
    json_data['title']=bing_json_data['images'][0]['title']
    json_data['url']=settings.BINGURL+bing_json_data['images'][0]['url'].replace("&rf=LaDigue_1920x1080.jpg&pid=hp","")
    json_data['datetime']=str(time.strftime('%Y-%m-%d', time.localtime()))
    json_data['copyright']=bing_json_data['images'][0]['copyright']
    json_data['copyrightlink']=bing_json_data['images'][0]['copyrightlink']
    json_data['hsh']=bing_json_data['images'][0]['hsh']
    json_data['created_time']=str(time.strftime('%Y-%m-%d', time.localtime()))
    return json_data

# 检查参数合法性
def check_params(page,limit,order,w,h,uhd,mkt):
    if settings.LOCATION.count(mkt)==0:
        return False
    if order!="desc" and order!="asc":
        return False
    if page<=0 or limit<=0 or limit>settings.LIMIT_DATA:
        return False
    if uhd==False and settings.W.count(w)==0 or settings.H.count(h)==0:
        return False
    return True

# 字符串拼接
def contact_w_h(w,h):
    return str(w)+"x"+str(h)