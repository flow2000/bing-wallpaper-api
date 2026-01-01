# -*- coding:utf-8 -*-
# @Author: flow2000
import requests
import json
import random
import sys
import os

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import aiohttp
from colorama import init
init(autoreset=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from bing_wallpaper_api import settings 
from bing_wallpaper_api.utils import util
from api import BingResponse
from api.mongodbapi import *

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
@limiter.limit("10/minute")  # 每分钟最多10个请求
async def index(request: Request):
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
                "https://blog.aqcoder.cn/code/txt/version/bing-wallpaper-api.txt",
                "https://static.aqcoder.cn/txt/version/bing-wallpaper-api.txt",
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
        return BingResponse.error(msg="BingAPI 获取不到最新版本，但仍可使用，请联系：https://github.com/flow2000/bing-wallpaper-api/issues/new",data=data)
    data={
        "current_version":settings.VERSION,
        "latest_version":latest_version
    }
    return BingResponse.success(msg="BingAPI 部署成功，详情可查看文档：https://api-bimg-cc.apifox.cn",data=data)

async def fetch(session, url):
    async with session.get(url, verify_ssl=False) as response:
        return await response.text()

@app.get("/favicon.ico",tags=["INFO"], summary="返回图标")
@limiter.limit("10/minute")  # 每分钟最多10个请求
async def favicon(request: Request):
    '''
    - 返回图标
    '''
    return StreamingResponse(open('favicon.ico', mode="rb"), media_type="image/jpg")

@app.get("/today",tags=["API"], summary="返回今日壁纸")
@limiter.limit("10/minute")  # 每分钟最多10个请求
async def latest(request: Request, w: str = "1920", h: str = "1080", uhd: bool = False, mkt: str = "zh-CN"):
    '''
    请求字段说明：
    - w:图片宽度,默认1920
    - h:图片长度,默认1080
    - uhd:是否4k,默认False,为True时请求参数w和h无效。目前支持的分辨率:1920x1200, 1920x1080, 1080x1920, 1366x768, 1280x768, 1024x768, 800x600, 800x480, 768x1280, 720x1280, 640x480, 480x800, 400x240, 320x240, 240x320
    - mkt:地区，默认zh-CN。目前支持的地区码：zh-CN, de-DE, en-CA, en-GB, en-IN, en-US, fr-FR, it-IT, ja-JP
    '''
    return latest_one(w,h,uhd,mkt)

@app.get("/random",tags=["API"], summary="返回随机壁纸")
@limiter.limit("10/minute")  # 每分钟最多10个请求
async def random(request: Request, w: str = "1920", h: str = "1080", uhd: bool = False, mkt: str = "zh-CN"):
    '''
    请求字段说明：
    - w:图片宽度,默认1920
    - h:图片长度,默认1080
    - uhd:是否4k,默认False,为True时请求参数w和h无效。目前支持的分辨率:1920x1200, 1920x1080, 1080x1920, 1366x768, 1280x768, 1024x768, 800x600, 800x480, 768x1280, 720x1280, 640x480, 480x800, 400x240, 320x240, 240x320
    - mkt:地区，默认zh-CN。目前支持的地区码：zh-CN, de-DE, en-CA, en-GB, en-IN, en-US, fr-FR, it-IT, ja-JP
    '''
    return random_one(w,h,uhd,mkt)

@app.get("/all",tags=["API"], summary="返回分页数据")
@limiter.limit("10/minute")  # 每分钟最多10个请求
async def all(request: Request, page: int = 1, limit: int = 10, order: str="desc", year: int = None, w: int = 1920, h: int = 1080, uhd: bool = False, mkt: str = "zh-CN"):
    '''
    请求字段说明：
    - page:页码,默认1
    - limit:页数,默认10。当指定year参数时，最大可设置为366（闰年天数）
    - order:排序方式,默认desc降序，可选asc升序
    - year:年份过滤,可选。指定后只返回该年份的数据，要求年份>=2016
    - w:图片宽度,默认1920
    - h:图片长度,默认1080
    - uhd:是否4k,默认False,为True时请求参数w和h无效。目前支持的分辨率:1920x1200, 1920x1080, 1080x1920, 1366x768, 1280x768, 1024x768, 800x600, 800x480, 768x1280, 720x1280, 640x480, 480x800, 400x240, 320x240, 240x320
    - mkt:地区，默认zh-CN。目前支持的地区码：zh-CN, de-DE, en-CA, en-GB, en-IN, en-US, fr-FR, it-IT, ja-JP
    
    示例：
    - /all?year=2023  返回2023年的所有壁纸
    - /all?year=2023&limit=200  返回2023年的壁纸，最多200条
    - /all?year=2023&limit=366  返回2023年的所有壁纸（最多366条）
    '''
    # 检查年份参数
    if year is not None:
        if util.check_year_param(year) == False:
            return BingResponse.error('年份参数错误，要求年份>=2016')
    if util.check_params(page,limit,order,w,h,uhd,mkt,year)==False:
        return BingResponse.error('请求参数错误')
    return query_all(page,limit,order,w,h,uhd,mkt,year)

@app.get("/total",tags=["API"], summary="返回数据总数")
@limiter.limit("10/minute")  # 每分钟最多10个请求
async def total(request: Request, mkt: str = "zh-CN"):
    '''
    请求字段说明：
    - mkt:地区，默认zh-CN。目前支持的地区码：zh-CN, de-DE, en-CA, en-GB, en-IN, en-US, fr-FR, it-IT, ja-JP
    '''
    if settings.LOCATION.count(mkt)==0:
        return BingResponse.error('请求参数错误')
    return query_total_num(mkt)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8888)
