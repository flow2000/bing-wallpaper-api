## 必应图片API

### 简介

​		必应搜索每日都会有一张精美的图片，我们可以

​		1、保存下来搭建api用于图片展示

​		2、放在博客当博客背景

​		于是便有了本项目的诞生。本项目借助python实现：

​		1、服务端获取必应壁纸接口数据，存储到本地 JSON 文件（`data/<mkt>_all.json`）

​		2、提供json接口和图片接口

> **v3.0.0 更新说明**：数据来源由 MongoDB 改为本地 JSON 文件，部署无需再配置数据库。`data/*.json` 由 GitHub Actions 每日自动拉取并提交更新。

### 壁纸资源

自搭建服务需要必应壁纸资源的话可去到博客自取：

[分享2009-至今的必应壁纸](https://blog.aqcoder.cn/posts/6b5b8616/)

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
|  year  |  `Int`   |    否    |   年份过滤，要求年份>=2016      |

```markdown
// 已知分辨率
resolutions: [
    '1920x1200',
    '1920x1080',
    '1080x1920',
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

> **数据来源说明**：`/random`、`/all`、`/total` 接口读取项目根目录下 `data/<mkt>_all.json` 本地数据文件；`/today` 接口实时请求必应官方接口。`data/*.json` 由 GitHub Actions（`.github/workflows/matser.yml`）每日定时拉取必应最新壁纸并提交更新，无需手动维护。

#### Linux 本地部署

1、安装 Python 3.8+

2、（可选）拉取最新壁纸数据：
```shell
python bing_wallpaper_api/run.py
python bing_wallpaper_api/run_fix_last_day.py
```

3、使用项目根目录下的启动脚本一键启动（自动检查并安装依赖）：
```shell
chmod +x start.sh
./start.sh
```
脚本默认监听 `8888` 端口，可通过环境变量自定义：
```shell
PORT=9127 ./start.sh
```

4、访问 `http://服务器IP:8888` 即可使用，接口文档地址 `http://服务器IP:8888/docs`

5、（可选）后台运行：
```shell
nohup ./start.sh > bing-api.log 2>&1 &
```

#### vercel部署

1、在[Vercel](https://vercel.com/signup)申请 Vercel帐号

2、点击部署<a href="https://vercel.com/import/project?template=https://github.com/flow2000/bing-wallpaper-api/tree/master" target="_blank" rel="noopener noreferrer"><img src="https://vercel.com/button" alt="vercel deploy"></a>

3、进入 Overview，点击 Domains 下方的链接，添加一个子域名，并在域名解析添加一个`CNAME`解析：`cname.vercel-dns.com.`，等待刷新完成即可获得一个`https`的接口

> 注意：Vercel 部署不再需要配置任何环境变量（无需 MongoDB）。

#### netlify部署

> 由于 Netlify Functions 不支持 Python 运行时，本项目使用 JavaScript 函数实现，直接读取本地 `data/*.json` 数据。

1、在 [Netlify](https://app.netlify.com/signup) 申请 Netlify 帐号

2、将本项目 Fork 到你的 GitHub，然后在 Netlify 中点击 "Add new site" → "Import an existing project"，选择 Fork 后的仓库

3、构建设置保持默认即可（`netlify.toml` 已配置好），点击 "Deploy site"

4、部署完成后，点击 Site overview 中的链接即可访问 API，接口路径与 Vercel 部署一致（`/today`、`/random`、`/all`、`/total`）

> 注意：Netlify 部署不再需要配置任何环境变量（无需 MongoDB）。

#### docker部署

```shell
docker run -itd --name bimg --restart=always -p 9127:8888 flow2000/bimg
```

> v4.0.0 起 Docker 部署不再需要 `MONGODB_URI` 环境变量。

### 未来计划

- [√] 补充前端展示必应壁纸 [必应壁纸 | 每天都有不一样的心情](https://bimg.cc/)

- [x] 使用本地部署，加快api速度 https://api.bimg.cc/

### 鸣谢

感谢[hexo-circle-of-friends](https://github.com/Rock-Candy-Tea/hexo-circle-of-friends)的自动化思路

感谢[Bing-Wallpaper-Action](https://github.com/zkeq/Bing-Wallpaper-Action)的分地区思路以及仓库的初始化数据
