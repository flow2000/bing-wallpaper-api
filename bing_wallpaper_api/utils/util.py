import requests
import json
import time
import os
import sys
from datetime import datetime, timedelta
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import settings

# 必应接口返回结构异常（非合法 JSON、images 为空、缺少 fullstartdate 等必需字段）时抛出，
# 由调用方按地区捕获并跳过本次抓取；不回退为本地日期，避免给壁纸打上错误日期写入脏数据
class BingResponseError(ValueError):
    pass

# 构造壁纸记录必需的字段（fullstartdate 用于换算壁纸所属的当地日期）
IMAGE_REQUIRED_FIELDS = ("fullstartdate", "title", "url", "copyright", "copyrightlink", "hsh")

def _preview(payload):
    try:
        return json.dumps(payload, ensure_ascii=False)[:300]
    except (TypeError, ValueError):
        return repr(payload)[:300]

# 校验响应结构并取出 images[0]：必须是含非空 images 列表的 JSON 对象，且首条含全部必需字段
def _first_image(bing_json_data):
    if not isinstance(bing_json_data, dict):
        raise BingResponseError("必应接口返回不是 JSON 对象：%s" % _preview(bing_json_data))
    images = bing_json_data.get("images")
    if not isinstance(images, list) or not images:
        raise BingResponseError("必应接口返回的 images 为空或缺失：%s" % _preview(bing_json_data))
    image = images[0]
    if not isinstance(image, dict):
        raise BingResponseError("必应接口返回的 images[0] 不是对象：%s" % _preview(image))
    missing = [key for key in IMAGE_REQUIRED_FIELDS if key not in image]
    if missing:
        raise BingResponseError("必应接口返回缺少字段 %s：%s" % (missing, _preview(bing_json_data)))
    return image

# 壁纸所属的当地日期：fullstartdate 是壁纸上线的 UTC 时刻（= 当地午夜），其小时部分编码了市场时区偏移。
# UTC+ 市场的午夜落在 UTC 前一天下午/晚间（小时>=12），UTC- 市场落在 UTC 当天上午（小时<12），
# 因此 +12 小时后取日期即得当地日期。对全部市场（UTC-8 ~ UTC+9）及夏令时切换均成立，
# 且不依赖时区数据库，兼容 Python 3.8。不能用 enddate（UTC 日期）：UTC- 市场会多记一天
def to_local_date(fullstartdate):
    try:
        return (datetime.strptime(fullstartdate, "%Y%m%d%H%M") + timedelta(hours=12)).strftime("%Y-%m-%d")
    except ValueError as e:
        raise BingResponseError("必应接口返回的 fullstartdate 格式异常：%r" % fullstartdate) from e

# 以必应接口返回的 fullstartdate 换算出的当地日期为准，
# 不能用 runner 本地日期：分地区任务在各时区凌晨触发时，UTC 可能仍停留在前一天
def parse_bing_date(bing_json_data):
    return to_local_date(_first_image(bing_json_data)["fullstartdate"])

# 构造必应壁纸信息数据
def build_json_data(id, bing_json_data):
    image = _first_image(bing_json_data)
    bing_date = to_local_date(image["fullstartdate"])
    json_data={}
    json_data['id']=id+1
    json_data['title']=image['title']
    json_data['url']=settings.BINGURL+image['url'].replace("&rf=LaDigue_1920x1080.jpg&pid=hp","")
    json_data['datetime']=bing_date
    json_data['copyright']=image['copyright']
    json_data['copyrightlink']=image['copyrightlink']
    json_data['hsh']=image['hsh']
    json_data['created_time']=str(time.strftime('%Y-%m-%d', time.localtime()))
    return json_data

# 必应接口请求超时时间（秒），避免网络抖动时任务无限挂起
REQUEST_TIMEOUT = 30

# 获取必应接口数据
def get_data(id,url):
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        bing_json_data=json.loads(response.text)
    except requests.RequestException as e:
        raise BingResponseError("必应接口请求失败：%s" % e) from e
    except ValueError as e:
        raise BingResponseError("必应接口返回内容不是合法 JSON：%s" % e) from e
    return build_json_data(id, bing_json_data)

# 检查参数合法性
def check_params(page,limit,order,w,h,uhd,mkt,year=None):
    if settings.LOCATION.count(mkt)==0:
        return False
    if order!="desc" and order!="asc":
        return False
    # 判断limit是否超过限制（支持年份查询时扩展limit限制）
    max_limit = settings.YEAR_LIMIT if year else settings.LIMIT_DATA
    if page<=0 or limit<=0 or limit>max_limit:
        return False
    if w == h:
        return False
    if uhd==False and settings.W.count(w)==0 or settings.H.count(h)==0:
        return False
    return True

# 检查年份参数合法性
def check_year_param(year):
    """
    检查年份参数是否合法
    要求：年份必须为整数且大于等于2016
    """
    try:
        year_int = int(year)
        if year_int < 2016:
            return False
        return True
    except (TypeError, ValueError):
        return False

# 字符串拼接
def contact_w_h(w,h):
    return str(w)+"x"+str(h)