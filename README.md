## 必应图片API

### 简介

​		必应搜索每日都会有一张精美的图片，我们可以

​		1、保存下来搭建api用于图片展示

​		2、放在博客当博客背景

​		于是便有了本项目的诞生。本项目借助python实现：

​		1、服务端获取2018-至今的壁纸接口数据，并存储到Mongodb

​		2、提供json接口和图片接口

### API接口说明

#### 获取今日壁纸

```shell
https://api.bimg.cc/today?w=1920&h=1080&mkt=zh-CN
```

| 参数名 |   类型   | 是否必要 |        备注        |
| :----: | :------: | :------: | :----------------: |
|   w    |  `Int`   |    否    | 图片宽度，默认1920 |
|   h    |  `Int`   |    否    | 图片高度，默认1080 |
|  uhd   |  `Bool`  |    否    | 是否4k，默认False  |
|  mkt   | `String` |    否    |  地区，默认zh-CN   |

#### 获取随机壁纸

```shell
https://api.bimg.cc/random?w=1920&h=1080&mkt=zh-CN
```

| 参数名 |   类型   | 是否必要 |        备注        |
| :----: | :------: | :------: | :----------------: |
|   w    |  `Int`   |    否    | 图片宽度，默认1920 |
|   h    |  `Int`   |    否    | 图片高度，默认1080 |
|  uhd   |  `Bool`  |    否    | 是否4k，默认False  |
|  mkt   | `String` |    否    |  地区，默认zh-CN   |

#### 获取壁纸JSON数据

```shell
https://api.bimg.cc/all?page=1&order=asc&limit=10&w=1920&h=1080&mkt=zh-CN
```

| 参数名 |   类型   | 是否必要 |              备注               |
| :----: | :------: | :------: | :-----------------------------: |
|  page  |  `Int`   |    否    |           页数，默认1           |
| limit  |  `Int`   |    否    |   每页数据量，默认10（1-20）    |
|   w    |  `Int`   |    否    |       图片宽度，默认1920        |
|   h    |  `Int`   |    否    |       图片高度，默认1080        |
| order  | `string` |    否    | 排序，默认降序`desc`，升序`asc` |
|  mkt   | `String` |    否    |         地区，默认zh-CN         |

```markdown
// 已知分辨率
resolutions: [
    '1920x1200',
    '1920x1080',
    '1366x768',
    '1280x768',
    '1024x768',
    '800x600',
    '800x480',
    '768x1280',
    '720x1280',
    '640x480',
    '480x800',
    '400x240',
    '320x240',
    '240x320'
]
// 已知国家地区
locations: [
    "de-DE",
    "en-CA",
    "en-GB",
    "en-IN",
    "en-US",
    "fr-FR",
    "it-IT",
    "ja-JP",
    "zh-CN"
]
```

#### 获取壁纸数量

```shell
https://api.bimg.cc/total?mkt=zh-CN
```

| 参数名 |   类型   | 是否必要 |      备注       |
| :----: | :------: | :------: | :-------------: |
|  mkt   | `String` |    否    | 地区，默认zh-CN |

### 部署

#### vercel部署

1、在 [MongoDB](https://www.mongodb.com/cloud/atlas/register) 申请 MongoDB 帐号，具体可查看我的博客教程：[如何申请一个永久免费的 Mongodb 数据库 - 详细版](https://blog.panghai.top/posts/b267/)

2、在[Vercel](https://vercel.com/signup)申请 Vercel帐号

3、创建数据库用户名和密码，在IPAccess List添加`0.0.0.0`（代表允许所有 IP 地址的连接），在 Clusters 页面点击 CONNECT，选择第二个：Connect your application，并记录数据库连接字符串，请将连接字符串中的 `user`修改为数据库用户，`<password>` 修改为数据库密码

3、点击部署<a href="https://vercel.com/import/project?template=https://github.com/flow2000/bing-wallpaper-api/tree/master" target="_blank" rel="noopener noreferrer"><img src="https://vercel.com/button" alt="vercel deploy"></a>

4、进入 Settings - Environment Variables，添加环境变量 `MONGODB_URI`，值为第 3 步的数据库连接字符串

5、进入 Overview，点击 Domains 下方的链接，添加一个子域名，并在域名解析添加一个`CNAME`解析：`cname.vercel-dns.com.`，等待刷新完成即可获得一个`https`的接口

#### docker部署

```shell
docker run -itd --name bimg --restart=always --env MONGODB_URI= -p 9127:8888 flow2000/bimg
```

`MONGODB_URI`：存储方式为mongodb时的环境变量

### 未来计划

- [x] 补充前端展示必应壁纸 [必应壁纸 | 每天都有不一样的心情](https://bimg.cc/)

- [x] 使用本地部署，加快api速度 https://api.bimg.cc/

### 鸣谢

感谢[hexo-circle-of-friends](https://github.com/Rock-Candy-Tea/hexo-circle-of-friends)的自动化思路

感谢[Bing-Wallpaper-Action](https://github.com/zkeq/Bing-Wallpaper-Action)的分地区思路以及仓库的初始化数据