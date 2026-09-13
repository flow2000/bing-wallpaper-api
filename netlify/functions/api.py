# -*- coding:utf-8 -*-
# Netlify Functions 入口：使用 Mangum 将 FastAPI ASGI 应用适配到 AWS Lambda 运行时
import sys
import os
import json
import traceback
from urllib.parse import urlparse

# 将项目根目录加入 sys.path，使 api、bing_wallpaper_api 等模块可被导入
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(BASE_DIR)

from mangum import Mangum
from api.main import app

# 将 FastAPI app 包装为 Lambda handler，lifespan="off" 避免无服务器环境的生命周期问题
mangum_handler = Mangum(app, lifespan="off")


def handler(event, context):
    try:
        # Netlify 通过 rewrite 将 /* 转发到 /.netlify/functions/api，
        # 导致 event.path 变成函数路径而非用户请求的原始路径。
        # 优先从 rawUrl 中提取原始路径，让 FastAPI 路由能正确匹配。
        raw_url = event.get("rawUrl") or ""
        if raw_url:
            parsed = urlparse(raw_url)
            path = parsed.path
        else:
            path = event.get("path") or event.get("rawPath") or "/"

        event["path"] = path
        event["rawPath"] = path

        return mangum_handler(event, context)
    except Exception as e:
        # 捕获异常并返回明确的错误信息，便于排查
        error_msg = f"Function error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"code": 500, "msg": error_msg, "data": None}),
        }
