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
from bing_wallpaper_api import settings 
from bing_wallpaper_api.utils import util
from api import BingResponse
from api.mongodbapi import *

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
                "https://blog.panghai.top/code/txt/version/bing-wallpaper-api.txt",
                "https://static.panghai.top/txt/version/bing-wallpaper-api.txt",
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
        data={
            "current_version":settings.VERSION
        }
        return BingResponse.error(msg="BingAPI 获取不到最新版本，但仍可使用，请联系：https://github.com/flow2000/bing-wallpaper-api",data=data)
    data={
        "current_version":settings.VERSION,
        "latest_version":latest_version
    }
    return BingResponse.success(msg="BingAPI 部署成功，详情可查看文档：https://www.apifox.cn/apidoc/shared-961673e6-161d-4129-88b6-e7b0a3b86cf1",data=data)

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
async def latest(w: str = "1920", h: str = "1080", uhd: bool = False, mkt: str = "zh-CN"):
    '''
    请求字段说明：
    - w:图片宽度,默认1920
    - h:图片长度,默认1080
    - uhd:是否4k,默认False,为True时请求参数w和h无效。目前支持的分辨率:1920x1200, 1920x1080, 1366x768, 1280x768, 1024x768, 800x600, 800x480, 768x1280, 720x1280, 640x480, 480x800, 400x240, 320x240, 240x320
    - mkt:地区，默认zh-CN。目前支持的地区码：zh-CN, de-DE, en-CA, en-GB, en-IN, en-US, fr-FR, it-IT, ja-JP
    '''
    return latest_one(w,h,uhd,mkt)

@app.get("/random",tags=["API"], summary="返回随机壁纸")
async def random(w: str = "1920", h: str = "1080", uhd: bool = False, mkt: str = "zh-CN"):
    '''
    请求字段说明：
    - w:图片宽度,默认1920
    - h:图片长度,默认1080
    - uhd:是否4k,默认False,为True时请求参数w和h无效。目前支持的分辨率:1920x1200, 1920x1080, 1366x768, 1280x768, 1024x768, 800x600, 800x480, 768x1280, 720x1280, 640x480, 480x800, 400x240, 320x240, 240x320
    - mkt:地区，默认zh-CN。目前支持的地区码：zh-CN, de-DE, en-CA, en-GB, en-IN, en-US, fr-FR, it-IT, ja-JP
    '''
    return random_one(w,h,uhd,mkt)

@app.get("/all",tags=["API"], summary="返回分页数据")
async def all(page: int = 1, limit: int = 10, order: str="desc", w: int = 1920, h: int = 1080, uhd: bool = False, mkt: str = "zh-CN"):
    '''
    请求字段说明：
    - page:页码,默认1
    - limit:页数,默认10
    - w:图片宽度,默认1920
    - h:图片长度,默认1080
    - uhd:是否4k,默认False,为True时请求参数w和h无效。目前支持的分辨率:1920x1200, 1920x1080, 1366x768, 1280x768, 1024x768, 800x600, 800x480, 768x1280, 720x1280, 640x480, 480x800, 400x240, 320x240, 240x320
    - mkt:地区，默认zh-CN。目前支持的地区码：zh-CN, de-DE, en-CA, en-GB, en-IN, en-US, fr-FR, it-IT, ja-JP
    '''
    if util.check_params(page,limit,order,w,h,uhd,mkt)==False:
        return BingResponse.error('请求参数错误')
    return query_all(page,limit,order,w,h,uhd,mkt)

@app.get("/total",tags=["API"], summary="返回数据总数")
async def total(mkt: str = "zh-CN"):
    '''
    请求字段说明：
    - mkt:地区，默认zh-CN。目前支持的地区码：zh-CN, de-DE, en-CA, en-GB, en-IN, en-US, fr-FR, it-IT, ja-JP
    '''
    if settings.LOCATION.count(mkt)==0:
        return BingResponse.error('请求参数错误')
    return query_total_num(mkt)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8888)
