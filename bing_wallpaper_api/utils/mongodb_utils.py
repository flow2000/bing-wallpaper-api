from pymongo import MongoClient
import os
import random

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

'''
根据地区插入一条json数据
@mkt 地区
@obj 插入数据
'''
def insert_one(mkt,obj):
    collection = db_init(mkt)
    collection.insert_one(obj)
    
'''
根据地区插入多条json数据
@mkt 地区
@obj 插入数据
'''
def insert_many(mkt,obj):
    collection = db_init(mkt)
    collection.insert_many(obj)

'''
随机查询一条文档数据
@mkt 地区
'''
def query_random_one(mkt):
    collection = db_init(mkt)
    num = collection.count_documents({})
    if num!=0:
        id = random.sample(list(range(1,num+1)),1)[0]
    else:
        return {}
    return collection.find_one({"id":id},{"datetime":0 })

'''
查询一条最新插入文档数据
@mkt 地区
'''
def query_latest_one(mkt):
    collection = db_init(mkt)
    return collection.find_one(sort=[('datetime', -1)])

'''
查询第一条插入文档数据
@mkt 地区
'''
def query_first_one(mkt):
    collection = db_init(mkt)
    return collection.find_one(sort=[('datetime', 1)])

'''
获取文档数量
@mkt 地区
'''
def get_count(mkt):
    collection = db_init(mkt)
    return collection.count_documents({})

'''
获取全部文档
@mkt 地区
'''
def get_all_data(mkt):
    collection = db_init(mkt)
    return collection.find({},{"_id":0}).sort("datetime",-1)

'''
查询json分页数据
@mkt 地区
@query_params 查询参数
page 页数
order 升序/降序 升序为1 降序为-1
limit 每页数量
year 年份过滤（可选）
'''
def query_data(mkt,query_params):
    collection = db_init(mkt)
    page = query_params['page']
    order = query_params['order']
    limit = query_params['limit']
    
    # 构建查询条件
    query_condition = {}
    
    # 如果指定了年份，添加年份过滤条件
    if 'year' in query_params and query_params['year']:
        year = query_params['year']
        # datetime字段格式为 "YYYY-MM-DD"，通过正则匹配年份
        import re
        query_condition["datetime"] = {"$regex": f"^{year}-"}
    
    return collection.find(query_condition,{"_id":0}).skip((page-1)*limit).sort("datetime",order).limit(limit)
    
'''
获取查询总数
@mkt 地区
@query_params 查询参数（同 query_data）
'''
def get_query_count(mkt, query_params):
    collection = db_init(mkt)
    query_condition = {}

    # 如果指定了年份，添加年份过滤条件
    if 'year' in query_params and query_params['year']:
        year = query_params['year']
        query_condition["datetime"] = {"$regex": f"^{year}-"}

    return collection.count_documents(query_condition)

'''
删除json数据
'''
def del_data(mkt,del_params):
    collection = db_init(mkt)
    collection.delete_many(del_params)

'''
更新json数据
'''
def update_data(mkt,update_params):
    collection = db_init(mkt)
    collection.update_many(del_params)
    