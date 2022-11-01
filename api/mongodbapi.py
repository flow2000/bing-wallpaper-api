import sys
import os
import time
import json
import requests
from fastapi.responses import RedirectResponse
from pymongo import MongoClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import settings 
from utils import util
from api import BingResponse
if settings.DATABASE=="mongodb":
    from utils.mongodb_utils import *

def query_all(page,limit,order,w,h,uhd,mkt):
    if order == "desc":
        order = -1
    else:
        order = 1
    link_str=""
    if uhd==False:
        link_str=util.contact_w_h(w,h)
    else:
        link_str="UHD"
    query_params={
        "page":page,
        "limit":limit,
        "order":order
    }
    query_result=query_data(mkt,query_params)
    data=[]
    for item in query_result:
        item['url']=item['url'].replace(util.contact_w_h(settings.DEFAULT_W,settings.DEFAULT_H),link_str)
        data.append(item)
    return BingResponse.success(data=data)

def query_total_num(mkt):
    return BingResponse.success(data=get_count(mkt))

def latest_one(w,h,uhd,mkt):
    if settings.DEPLOY_TYPE=='docker':
        if settings.LOCATION.count(mkt)==0:
            mkt=settings.DEFAULT_MKT
        link_str=w+'x'+h
        if uhd:
            link_str='UHD'
        return RedirectResponse(query_latest_one(mkt)['url'].replace("&rf=LaDigue_1920x1080.jpg&pid=hp","").replace("1920x1080",link_str))
    else:
        url=""
        if settings.LOCATION.count(mkt)>0:
            url=settings.BINGAPI+"&mkt="+mkt
        else:
            url=settings.BINGAPI+"&mkt="+settings.DEFAULT_MKT
        data = json.loads(requests.get(url).text)
        link_str=w+'x'+h
        if uhd:
            link_str='UHD'
        return RedirectResponse(settings.BINGURL+data['images'][0]['url'].replace("&rf=LaDigue_1920x1080.jpg&pid=hp","").replace("1920x1080",link_str))

def random_one(w,h,uhd,mkt):
    url=""
    if settings.LOCATION.count(mkt)>0:
        url=query_random_one(mkt)['url']
    else:
        url=query_random_one("zh-CN")['url']
    link_str=w+'x'+h
    if uhd:
        link_str='UHD'
    return RedirectResponse(url.replace(util.contact_w_h(settings.DEFAULT_W,settings.DEFAULT_H),link_str))