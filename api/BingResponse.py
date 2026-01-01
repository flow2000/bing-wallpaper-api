def success(msg="操作成功",data=None):
    res_json = {}
    res_json['code']=200
    res_json['msg']=msg
    if data!=None:
        res_json['data']=data
    return res_json

def table_success(msg="操作成功",data=None,total=None):
    res_json = {}
    res_json['code']=200
    res_json['msg']=msg
    if data!=None:
        res_json['data']=data
    if total!=None:
        res_json['total']=total
    return res_json

def error(msg="操作失败",data=None):
    res_json = {}
    res_json['code']=500
    res_json['msg']=msg
    if data!=None:
        res_json['data']=data
    return res_json
