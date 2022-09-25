from pymongo import MongoClient
import os
import random

def db_init():
    URI = os.environ.get("MONGODB_URI")
    client = MongoClient(URI)
    db = client.bing
    collection = db.info
    # collection.create_index([('id',-1)],unique=True)
    return collection

'''
插入一条json数据
返回插入数据的_id值
'''
def insert_one(obj):
    collection = db_init()
    collection.insert_one(obj)
    
'''
插入多条json数据
返回插入数据的_id值
'''
def insert_many(obj):
    collection = db_init()
    collection.insert_many(obj)

'''
随机查询一条文档数据
'''
def query_random_one():
    collection = db_init()
    num = collection.count_documents({})
    id = random.sample(list(range(1,num+1)),1)[0]
    return collection.find_one({"id":id},{"_id":0 })

'''
查询一条最新插入文档数据
'''
def query_latest_one():
    collection = db_init()
    return collection.find_one(sort=[('_id', -1)])

'''
查询第一条插入文档数据
'''
def query_first_one():
    collection = db_init()
    return collection.find_one(sort=[('_id', 1)])

'''
获取文档数量
'''
def get_count():
    collection = db_init()
    return collection.count_documents({})

'''
查询json分页数据
@query_params 查询参数
page 页数
order 升序/降序 升序为1 降序为-1
limit 每页数量
'''
def query_data(query_params):
    collection = db_init()
    page = query_params['page']
    order = query_params['order']
    limit = query_params['limit']
    return collection.find({},{"_id":0}).skip((page-1)*limit).sort("_id",order).limit(limit)

'''
删除json数据
'''
def del_data(del_params):
    collection = db_init()
    collection.delete_many(del_params)

'''
更新json数据
'''
def update_data(update_params):
    collection = db_init()
    collection.update_many(del_params)
    