# -*- coding: UTF-8 -*-
import requests
import json
import time
import os,stat
import urllib.request
import datetime
import logging
import traceback
"""

Date: 2022-8-10
Author: 庞海
Description: 服务端每日任务
步骤：
1、下载当日壁纸到指定文件夹
2、上传壁纸到七牛云
3、构造json数据
4、错误邮件提醒

使用方法: 
1、修改本程序保存绝对路径 root_path(可以不修改)
2、修改壁纸/json保存路径 save_path(可以不修改)
3、修改七牛云域名 cnd_url(建议修改)
4、修改七牛云key和密钥以及bucket_name(必须修改)
5、修改邮件服务器、账号、授权码、接收人、发送人(建议修改，不需要邮箱提醒功能的请关闭 enabled_email设为False)
6、编辑/etc/crontab 添加 0 0 * * * root pyhton绝对路径 本程序绝对路径(必须修改)
例如：
0 0 * * * root /usr/bin/python /www/ScheduledTasks/getTodayBing.py
表示每日0点运行

本程序需要在服务器上运行
python执行错误则需要pip安装以上导入的包

"""

# 本程序保存绝对路径(按需修改)
root_path = "/www/scheduled_tasks/"
# 壁纸/json保存路径(按需修改)
save_path = "/www/data/"
# 七牛云域名，没有则留空 cnd_url=""(按需修改)
cnd_url = "cdn.panghai.top"
# 七牛云key(必填)
accessKey = "your access_key"
# 七牛云密钥(必填)
secretKey = "your secret_key"
# 七牛云存储空间名称(必填)
bucketName = "your bucket_name"
# 是否开启邮箱通知
enabled_email = True
# 是否创建图片副本并压缩（需要安装ffmpeg）
enabled_compress = False
# 邮箱STMP服务器
mail_host="your STMP server"  
# 用户名
mail_user="your email account"
# 授权码
mail_pass="your email pass"   
# 发送者账号
sender = 'your email account'
# 发送者名字
sender_name = 'your name'
# 接收邮件，可设置为你的QQ邮箱或者其他邮箱，可以自己发送给自己
receivers = ['your receiver email']  

#当前年份
year = datetime.datetime.today().year
# 图片保存路径
img_path = save_path+"bing/"+str(year)+"/"
# json保存路径
json_path = save_path+"json/"
# php保存路径
php_path = save_path+"php/"
# 当前日期 例如：2022-08-11
now_date = time.strftime('%Y-%m-%d', time.localtime())
headers={
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
}

# 创建壁纸保存文件夹
def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(path+"+创建成功")

mkdir(root_path)
mkdir(save_path)
mkdir(img_path)
mkdir(json_path)

logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.INFO,
                    filename=root_path+'access.log',
                    filemode='a')

#脚本创建日期
crete_date = datetime.datetime.strptime('2022-08-11', "%Y-%m-%d").date()
#已执行天数
days = (datetime.datetime.strptime(now_date, "%Y-%m-%d").date() - crete_date).days

# 读取必应api的json数据
bing_json_data={}

#上传文件返回的hash值
hash=""

#图片总数
total=4000

# 计算文件数
def file_count(path):
    count = 0
    for root,dirs,files in os.walk(path):    #遍历统计
          for each in files:
                 count += 1
    return count

# 分割出图片名称
def split_url(img_url):
    return img_url.split("th?id=")[1].split("&rf=")[0]

# 发生错误时发送邮件
def send_email(subject,text_body="发生错误"):
    # 启用邮箱通知时
    if enabled_email:
        import smtplib
        from email.mime.text import MIMEText
        from email.header import Header
        message = MIMEText(text_body, 'plain', 'utf-8')
        message['From'] = Header(sender, 'utf-8')
        message['To'] =  Header(sender_name, 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')
        
        try:
            smtpObj = smtplib.SMTP() 
            smtpObj.connect(mail_host, 25)    # 25 为 SMTP 端口号
            smtpObj.login(mail_user,mail_pass)  
            smtpObj.sendmail(sender, receivers, message.as_string())
        except smtplib.SMTPException:
            logging.info(traceback.format_exc())

# 上传文件函数  
# filename 上传的文件名 例如：OHR.StatueFlyingApsaras_ZH-CN134905812_958x512.jpg
# file_path 文件所在路径 例如：/www/data/bing/2012/
# upload_path 上传七牛云的路径 例如：bing/2012/
def upload_file(filename="",file_path="",upload_path=""):
    from qiniu import Auth, put_file, etag
    import qiniu.config
    from qiniu import BucketManager
    #需要填写你的 Access Key 和 Secret Key
    access_key = accessKey
    secret_key = secretKey
    #要上传的空间
    bucket_name = bucketName
    #构建鉴权对象
    q = Auth(access_key, secret_key)
    #初始化BucketManager
    bucket = BucketManager(q)
    #上传路径
    path = upload_path
    #上传后保存的文件名
    key = path+filename
    #生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, key, 3600)
    #要上传文件的本地路径
    localfile = file_path+filename
    ret, info = put_file(token, key, localfile, version='v2') 
    code = info.status_code
    if code == 200:
        data = json.loads(info.text_body)
        return data["hash"]
    else:
        send_email("执行python定时任务时发生错误信息:",str(info.error))
        logging.info("\n发生错误信息："+str(info.error))

# 读取json
def read_json(name):
    with open(json_path+name,'r',encoding='utf-8') as load_f:
        return json.load(load_f)

# 写入json
def write_json(name,data):
    with open(json_path+name,"w",encoding='utf-8') as f:
        json.dump(data,f, ensure_ascii=False)

# 修改全部json的total_page属性img_path
def modify_json():
    lists = os.listdir(json_path)
    for i in range(1,len(lists)+1):
        json_data = read_json(str(i)+".json")
        json_data["data"]["total_page"]=len(lists)+1
        write_json(str(i)+".json",json_data)

# 构造图片对象
def create_pic(id,name):
    pic={}
    total=id+1
    pic["id"]=id+1
    pic["title"]=bing_json_data["title"]
    pic["copyright"] = bing_json_data["copyright"]
    pic["url"]="https://cn.bing.com/th?id="+name+"&rf=LaDigue_1920x1080.jpg&pid=hp"
    pic["path"] = "/bing/"+str(year)+"/"+name
    pic["datetime"]=now_date
    pic["hsh"] = hash
    pic["view"] = 0
    pic["down"] = 0
    pic["like"] = 0
    pic["created_time"] = now_date
    return pic

# 构造返回数据对象
def create_dict(filename,page):
    img_list=[]
    img_list.append(create_pic(0,filename))
    tmp_dict={}
    tmp_dict["current_page"]=page+1
    tmp_dict["total_page"]=page+1
    tmp_dict["data"]=img_list
    res_dict={}
    res_dict["code"]=200
    res_dict["msg"]="操作成功"
    res_dict["data"]=tmp_dict
    return res_dict

# 构造json数据并写入
def create_json(filename):
    json_list = os.listdir(json_path)
    page = len(json_list)
    last_date=now_date
    if page!=0:
        json_data = read_json(str(page)+".json")
        url_list = json_data["data"]["data"]
        last_img = url_list[len(url_list)-1]
        last_id = last_img["id"]
        last_date = last_img["datetime"]
    else:
        img_list=[]
        img_list.append(create_pic(0,filename))
        tmp_dict={}
        tmp_dict["current_page"]=page+1
        tmp_dict["total_page"]=page+1
        tmp_dict["data"]=img_list
        res_dict={}
        res_dict["code"]=200
        res_dict["msg"]="操作成功"
        res_dict["data"]=tmp_dict
        write_json(str(page+1)+".json",res_dict)

    # 如果今日图片已添加就不用再次添加   
    if last_date == now_date:
        logging.info("图片已存在 不用构造json")
    # 如果今日图片没有添加且该json数据没有满10个，则添加到该json数据并重新写入
    elif len(url_list)<10:
        url_list.append(create_pic(last_id,filename))
        json_data["data"]["data"]=url_list
        write_json(str(page)+".json",json_data)
    else:
        modify_json()
        img_list=[]
        img_list.append(create_pic(last_id,filename))
        tmp_dict={}
        tmp_dict["current_page"]=page+1
        tmp_dict["total_page"]=page+1
        tmp_dict["data"]=img_list
        res_dict={}
        res_dict["code"]=200
        res_dict["msg"]="操作成功"
        res_dict["data"]=tmp_dict
        write_json(str(page+1)+".json",res_dict)
    
def compress_pictrue(filename,img_path):
    mkdir(img_path.replace("bing","compress-bing"))
    in_path = img_path+filename
    out_path = img_path.replace("bing","compress-bing")+filename
    if not os.path.exists(out_path):
        # 命令编辑
        cmd_line = "ffmpeg -i "+in_path+" -q 20 -vf scale=-1:768 -y "+out_path
        # 调用命令行
        os.system(cmd_line)
        logging.info("制作图片封面："+out_path)

# # 创建图片url链接文件
# def create_rand():
#     url_list=[]
#     lists = os.listdir(json_path)
#     for i in range(1,len(lists)+1):
#         json_data = read_json(str(i)+".json")
#         img_list = json_data["data"]["data"]
#         for j in range(len(img_list)):
#             url_list.append(img_list[j]["url"])
#     with open(php_path+"url.txt","w",encoding='utf-8') as f:
#         f.write(str(url_list))
#         f.close()

try:
    url = "https://cn.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=zh-CN"
    bing_json_data = json.loads(requests.get(url, headers=headers).text)["images"][0]
    img_url = "https://cn.bing.com"+bing_json_data["url"]
    filename = split_url(img_url)
    urllib.request.urlretrieve(img_url,filename=img_path+filename)
    logging.info(img_url+"下载成功")
    hash = upload_file(filename,img_path,"bing/"+str(year)+"/")
    create_json(filename)
    if enabled_compress:
        compress_pictrue(filename,img_path)
    send_email("服务端定时任务：必应每日任务","第"+str(days)+"次执行python定时任务成功！")
except Exception as ex:
    send_email("执行python定时任务时发生错误信息:",traceback.format_exc())
    logging.info("\n发生错误信息："+traceback.format_exc())