import json
import time
import os
from pymongo import MongoClient

############### 数据初始化，修改数据库链接后，直接运行本程序 ####################

############################## 工具配置 start ################################

# mongodb连接字符串
MONGODB_URI='mongodb://127.0.0.1:27017/'

############################## 工具配置 end ##################################



# 地区
LOCATION=["de-DE", "en-CA", "en-GB", "en-IN", "en-US", "fr-FR", "it-IT", "ja-JP", "zh-CN"]
# 必应接口
BINGAPI='https://cn.bing.com/HPImageArchive.aspx?n=1&format=js&idx=0'
# 必应URL
BINGURL='https://cn.bing.com'

'''
初始化连接
@mkt 地区，默认zh-CN
'''
def db_init(mkt="zh-CN"):
    URI = os.environ.get("MONGODB_URI")
    client = MongoClient(URI)
    db = client.bing
    if mkt=="zg-CN":
        return db['cn']
    if mkt=="ja-JP":
        return db['jp']
    if mkt=="it-IT":
        return db['it']
    if mkt=="fr-FR":
        return db['fr']
    if mkt=="en-US":
        return db['us']
    if mkt=="en-IN":
        return db['in']
    if mkt=="en-GB":
        return db['gb']
    if mkt=="en-CA":
        return db['ca']
    if mkt=="de-DE":
        return db['de'] 
    return db['cn']
    return collection

'''
根据地区插入多条json数据
@mkt 地区
@obj 插入数据
'''
def insert_many(mkt,obj):
    collection = db_init(mkt)
    collection.insert_many(obj)

def read_json(run_type):
    with open(f'{run_type}_all.json', 'r', encoding="utf-8") as f:
        return json.load(f)['data']

# 格式化必应接口数据
def format_data(lists):
    res=[]
    lists=lists[::-1]
    id=1
    for bing_json_data in lists:
        timearray=time.strptime(str(bing_json_data['enddate']),'%Y%m%d')
        datetime=time.strftime('%Y-%m-%d', timearray)
        json_data={}
        json_data['id']=id
        json_data['title']=bing_json_data['title']
        json_data['url']=BINGURL+bing_json_data['url'].replace("&rf=LaDigue_1920x1080.jpg&pid=hp","")
        json_data['datetime']=datetime
        json_data['copyright']=bing_json_data['copyright']
        json_data['copyrightlink']=bing_json_data['copyrightlink']
        json_data['hsh']=bing_json_data['hsh']
        json_data['created_time']=str(time.strftime('%Y-%m-%d', time.localtime()))
        res.append(json_data)
        id=id+1
    return res

# 初始化数据
def init_data():
    for mkt in LOCATION:
        print("初始化"+mkt)
        lists=read_json(mkt)
        lists=format_data(lists)
        insert_many(mkt,lists)
        print("初始化结束\n")

# 删除数据库，慎用
def del_database():
    URI = os.environ.get("MONGODB_URI")
    client = MongoClient(URI)
    client.drop_database('bing')

if __name__=='__main__':
    os.environ['MONGODB_URI']=MONGODB_URI
    del_database()
    init_data()