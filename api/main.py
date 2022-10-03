# -*- coding:utf-8 -*-
# @Author: flow2000
import requests
import json
import random
import sys
import os

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import aiohttp
from pymongo import MongoClient
from colorama import init
init(autoreset=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from utils import mogodb_utils

# os.environ["MONGODB_URI"]="mongodb://127.0.0.1:27017/"

app = FastAPI()

# 设置CORS
origins = [
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VERSION="2.0.1"


BINGAPI='https://cn.bing.com/HPImageArchive.aspx?n=1&format=js&idx=0&mkt=zh-CN'
BINGURL='https://cn.bing.com'
W=[1920,1366,1280,1024,800,768,720,640,480,400,320,240]
H=[1200,1080,768,600,480,1280,800,240,320]

@app.get("/",tags=["API"], summary="返回部署成功信息")
async def index():
    '''
    响应字段说明：
    - code:状态码
    - msg:部署信息
    - current_version:当前版本
    - latest_version:最新版本
    '''
    latest_version=""
    try:
        async with aiohttp.ClientSession() as session:
            version_links=[
                "https://blog.panghai.top/code/txt/version/bing-api.txt",
                "https://static.panghai.top/txt/version/bing-api.txt",
            ]
            tasks = [asyncio.create_task(fetch(session, link)) for link in version_links]
            done, pending = await asyncio.wait(tasks)
            for d in done:
                if len(d.result())<10:
                    latest_version = d.result()
                    break
            if latest_version=="":
                raise Exception("无法请求文件")
    except Exception as e:
        print(e)
        return {"code": "200","msg":"BingAPI 获取不到最新版本（仍可使用），请联系：https://github.com/flow2000/bing-api","current_version":VERSION}
    return {"code": "200","msg":"BingAPI 部署成功 ","current_version":VERSION,"latest_version": latest_version}

async def fetch(session, url):
    async with session.get(url, verify_ssl=False) as response:
        return await response.text()

@app.get("/favicon.ico",tags=["INFO"], summary="返回图标")
async def favicon():
    '''
    - 返回图标
    '''
    return StreamingResponse(open('favicon.ico', mode="rb"), media_type="image/jpg")

@app.get("/today",tags=["API"], summary="返回今日壁纸")
async def today(w: str = "1920", h: str = "1080", uhd: bool = False):
    '''
    请求字段说明：
    - w:图片宽度,默认1920
    - h:图片长度,默认1080
    - uhd:是否4k,默认False,为True时请求参数w和h无效
    - 目前支持的分辨率:1920x1200, 1920x1080, 1366x768, 1280x768, 1024x768, 800x600, 800x480, 768x1280, 720x1280, 640x480, 480x800, 400x240, 320x240, 240x320
    '''
    data = json.loads(requests.get(BINGAPI, headers={
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
    }).text)
    query_data=w+'x'+h
    if uhd:
        query_data='UHD'  
    return RedirectResponse(BINGURL+data['images'][0]['url'].replace("&rf=LaDigue_1920x1080.jpg&pid=hp","").replace("1920x1080",query_data))

@app.get("/random",tags=["API"], summary="返回随机壁纸")
async def random_bing(w: str = "1920", h: str = "1080", uhd: bool = False):
    '''
    请求字段说明：
    - w:图片宽度,默认1920
    - h:图片长度,默认1080
    - uhd:是否4k,默认False,为True时请求参数w和h无效
    - 目前支持的分辨率:1920x1200, 1920x1080, 1366x768, 1280x768, 1024x768, 800x600, 800x480, 768x1280, 720x1280, 640x480, 480x800, 400x240, 320x240, 240x320
    '''
    url = mogodb_utils.query_random_one()['url']
    query_data=w+'x'+h
    if uhd:
        query_data='UHD'
    return RedirectResponse(url.replace("1920x1080",query_data))

@app.get("/all",tags=["API"], summary="返回分页数据")
async def all(page: int = 1, limit: int = 10, order: str="desc", w: int = 1920, h: int = 1080, uhd: bool = False):
    '''
    请求字段说明：
    - page:页码,默认1
    - limit:页数,默认10
    - w:图片宽度,默认1920
    - h:图片长度,默认1080
    - uhd:是否4k,默认False,为True时请求参数w和h无效
    - 目前支持的分辨率:1920x1200, 1920x1080, 1366x768, 1280x768, 1024x768, 800x600, 800x480, 768x1280, 720x1280, 640x480, 480x800, 400x240, 320x240, 240x320
    '''
    if order == "desc":
        order = -1
    elif order == "asc":
        order = 1
    else:
        return {'code':500,'msg':'请求参数错误'}
    if page<=0 or limit<=0 or limit >100:
        return {'code':500,'msg':'请求参数错误'}
    query_params={
        "page":page,
        "limit":limit,
        "order":order
    }
    link_str=""
    if uhd==False:
        if W.count(w)==0 or H.count(h)==0:
            return {'code':500,'msg':'请求参数错误'}
        link_str=str(w)+'x'+str(h)
    else:
        link_str="UHD"
    query_result=mogodb_utils.query_data(query_params)
    data=[]
    for item in query_result:
        item['url']=item['url'].replace("1920x1080",link_str)
        data.append(item)
    res_json = {}
    res_json['code']=200
    res_json['msg']='操作成功'
    res_json['data']=data
    return res_json

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8888)
