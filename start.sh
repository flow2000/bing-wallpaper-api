#!/bin/bash
# ============================================================
# Bing Wallpaper API - Linux 本地启动脚本
# 数据来源：本地 JSON 文件（data/<mkt>_all.json）
# 无需 MongoDB 数据库
# ============================================================

# 切换到脚本所在目录（项目根目录）
cd "$(dirname "$0")" || exit 1

# 端口配置，可通过环境变量 PORT 覆盖，默认 8888
PORT="${PORT:-8888}"

echo "=========================================="
echo "  Bing Wallpaper API v4.0.0"
echo "  数据来源: 本地 JSON (无需 MongoDB)"
echo "  监听端口: ${PORT}"
echo "=========================================="

# 检查 Python 是否可用
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[错误] 未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

# 优先使用 python3
PYTHON="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON="python"
fi

echo "[1/3] 检查依赖..."
# 检查是否已安装关键依赖，未安装则自动安装
$PYTHON -c "import fastapi, uvicorn, requests, aiohttp, slowapi, colorama" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "      依赖缺失，正在安装 requirements.txt ..."
    $PYTHON -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败，请检查 pip 或网络"
        exit 1
    fi
else
    echo "      依赖已就绪"
fi

echo "[2/3] 检查数据文件..."
DATA_COUNT=$(ls data/*_all.json 2>/dev/null | wc -l)
if [ "$DATA_COUNT" -eq 0 ]; then
    echo "[警告] data/ 目录下暂无 JSON 数据文件"
    echo "       接口 /today 仍可用（实时请求必应）"
    echo "       /random、/all、/total 将返回暂无数据"
    echo "       可手动运行: $PYTHON bing_wallpaper_api/run.py 拉取数据"
else
    echo "      已加载 ${DATA_COUNT} 个地区的 JSON 数据"
fi

echo "[3/3] 启动服务..."
echo "      访问地址: http://0.0.0.0:${PORT}"
echo "      接口文档: http://0.0.0.0:${PORT}/docs"
echo "      按 Ctrl+C 停止服务"
echo "------------------------------------------"

# 启动 FastAPI 服务
exec $PYTHON api/main.py
