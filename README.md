## 必应每日图片api拓展开发

### 简介

​		必应搜索每日都会有一张精美的图片，我们可以

​		1、保存下来搭建api用于图片展示

​		2、放在博客当博客背景

​		于是便有了本项目的诞生。本项目借助python实现：

​		1、服务端下载2016-至今的壁纸并创建json数据，搭建图片api

​		2、服务端上传图片至七牛云搭建cdn外链并邮件提醒

​		3、服务端每日下载最新壁纸、创建json数据、上传七牛云并更新图片api

### 效果

现目前已搭建两个api，如想直接使用请自取：

```yml
https://bing.panghai.top/php/random.php # 获取随机壁纸
https://bing.panghai.top/php/today.php  # 获取今日壁纸
https://bing.panghai.top/json/474       # 获取json数据，474代表页数
```

![](https://bing.panghai.top/php/random.php)

![](https://bing.panghai.top/php/today.php)

https://bing.panghai.top/json/474

现给出搭建教程

### 更换服务器python环境

```shell
cd /usr/bin
rm -rf pip
rm -rf python
ln -s pip3.6 pip
ln -s python3.6 python
```

{%note info no-icon%}

针对`CentOS7.6`版本

{%endnote%}

### 安装七牛云依赖包

```shell
cd ~
pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install qiniu -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 安装php环境

```markdown
https://www.php.cn/linux-462962.html
```

### 安装nginx

这里给出一键安装脚本：

```shell
#!/bin/sh
echo "----------------------------------start install nginx -----------------------------"
yum install -y gcc-c++  
yum -y install openssl openssl-devel
yum install -y zlib zlib-devel
yum install -y pcre pcre-devel
if [ 'grep "nginx" /etc/passwd | wc -l' ]; then
echo "adding user nginx"
groupadd nginx
useradd -s /sbin/nologin -M -g nginx nginx
else
echo "user nginx exsits"
fi

echo "-----------------------------------downloading nginx-------------------------------"
wget http://nginx.org/download/nginx-1.21.3.tar.gz
tar -xvf nginx-1.21.3.tar.gz
cd nginx-1.21.3

echo "------------------------------------configuring nginx,plz wait----------------------"
./configure --prefix=/usr/local/nginx --with-http_ssl_module --with-http_realip_module --with-http_stub_status_module

if [ $? -ne 0 ];then
echo "configure failed ,please check it out!"
else
echo "make nginx, please wait for 20 minutes"
make
fi

if [ $? -ne 0 ];then
echo "make failed ,please check it out!"
else
echo "install nginx, please wait for 20 minutes"
make install
fi

chown -R nginx.nginx /usr/local/nginx
ln -s /lib64/libpcre.so.0.0.1 /lib64/libpcre.so.1
cp /usr/local/nginx/sbin/nginx /usr/bin
nginx
iptables -I INPUT 3 -s 0.0.0.0/0 -p tcp --dport 80 -j ACCEPT
echo "----------------------------------start install nginx success-----------------------------"
```

新建`install.sh`，粘贴内容，`sh install.sh`即可

nginx的安装路径在`/usr/local/nginx`

### 克隆项目

```powershell
git clone git@github.com:flow2000/bing-api.git
```

将.py文件放入服务器/www/scheduled_tasks中（没有/www/scheduled_tasks创建一个）：

![](https://blog.panghai.top/img/af9f/1661227733296.png)

创建以下文件夹：

![](https://blog.panghai.top/img/af9f/1661228170970.png)

### 下载全部壁纸

指定程序保存路径，服务器执行：

```shell
cd /www/scheduled_tasks
python download_all_wallpaper.py
```

嫌麻烦可以使用云盘：

```markdown
百度云链接：链接: https://pan.baidu.com/s/1l1DmpT4ZLeuwkQsbLFK2SA?pwd=6666
天翼云盘链接：https://cloud.189.cn/web/share?code=zQr2yyauAFbe（访问码：8jpk）
```

### 创建json数据

创建json数据后可以不用数据库存储壁纸信息，直接返回json即可

指定程序保存路径，补充自己的七牛云自定义加速域名（最好填写）服务器端执行：

```shell
cd /www/scheduled_tasks
python create_json.py
```

### 运行每日任务测试结果

指定程序保存路径，在daily_task.py中添加七牛云key和密钥以及存储桶名称，有需求可添加邮箱提醒，修改服务器执行：

```shell
cd /www/scheduled_tasks
python daily_task.py
```

### 服务器创建定时任务

编辑/etc/crontab，添加：

```shell
0 0 * * * root /usr/bin/python /www/scheduled_tasks/daily_task.py
```

`0 0 * * *`代表每天0点执行。

### 创建api

将`today.php`和`random.php`放入`/www/data/php`

### 修改nginx配置

修改`/usr/local/nginx/conf/nginx.conf`：

http配置：

```conf
server {
    listen 		80;
    server_name yourdomain;

    # include vhosts/*.conf;
    #当请求网站下php文件的时候，反向代理到php-fpm
    location ~ .*\.php?$ {
        root   /www/data/;
        # try_files $uri $uri/ $uri.php?$args;
        index  api.php;
        try_files $uri = 404; #预先请求是否存在该文件，不存在返回404页面
        include fastcgi.conf;
        fastcgi_pass 127.0.0.1:9000;
    }

    # 创建json数据Api
        location /json {
        root /www/data/;
        try_files $uri $uri $uri.json?$args; #去掉.json后缀
    }
}

```

https配置：

```conf
    server {
        listen 80;
        server_name yourdomain;
        return  301 https://$server_name$request_uri;
    }

	server {
		listen 		443 ssl;
		server_name yourdomain;
        ssl_certificate /etc/ssl/yourdomain/yourdomain.pem;
        ssl_certificate_key /etc/ssl/yourdomain/yourdomain.key;
        ssl_session_cache    shared:SSL:4m;
        ssl_session_timeout  10m;
        ssl_ciphers  HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # include vhosts/*.conf;
        #当请求网站下php文件的时候，反向代理到php-fpm
        location ~ .*\.php?$ {
            root   /www/data/;
            # try_files $uri $uri/ $uri.php?$args;
            index  today.php;
            try_files $uri = 404; #预先请求是否存在该文件，不存在返回404页面
            include fastcgi.conf;
            fastcgi_pass 127.0.0.1:9000;
        }

        # 创建json数据Api
        location /json {
            root /www/data/;
            try_files $uri $uri $uri.json?$args; #去掉.json后缀
        }
        
	}
```

### 开发思路

​		首先必应提供了一个api，https://cn.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=zh-CN

参数意义：

| 参数名称 |                            值含义                            |
| :------: | :----------------------------------------------------------: |
|  format  |       返回数据格式。xml和js(一般用js格式返回json数据)        |
|   idx    | 请求图片截止天数。0：今天 -1 ：中明天 （预准备的） 1： 昨天，2：前天。类推（目前最多获取到7天前的图片） |
|    n     |            1-8 返回请求数量，目前最多一次获取8张             |
|   mkt    |                         地区。zh-CN                          |

#### 下载2009-至今的壁纸

​		前期可通过他人的api下载，后面可自己搭建图片到七牛云储存

#### 自建必应壁纸api

​		这里采用构建json文件，通过访问服务器返回json文件

#### 上传七牛云

​		使用七牛云的python版本的sdk

#### 仿照别人的部分api

​	用python爬下每一页的api样式，选取合适的键值，构造json文件

​	将文件保存到服务器

#### 编写php代码

​	可以根据需求自行编写php代码实现

#### 编写python代码

​	获取当天壁纸，下载，拼接图片名称，上传到七牛云，追加到json文件，提供错误邮件通知

#### 配置nginx

​	增加反向代理给服务器的php环境解析php，结果再通过nginx返回客户端