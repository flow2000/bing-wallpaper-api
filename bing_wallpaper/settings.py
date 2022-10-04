############################## 项目配置 start ################################

# 存储方式
DATABASE = "mongodb"

# 部署方式
DEPLOY_TYPE = "github"

############################## 项目配置 end ##################################




##############################项目固定配置，请勿修改################################

# 版本号
VERSION="3.0.0"

# 必应接口
BINGAPI='https://cn.bing.com/HPImageArchive.aspx?n=1&format=js&idx=0'

# 必应URL
BINGURL='https://cn.bing.com'

# 地区
LOCATION=["de-DE", "en-CA", "en-GB", "en-IN", "en-US", "fr-FR", "it-IT", "ja-JP", "zh-CN"]

# 图片宽度
W=[1920, 1366, 1280, 1024, 800, 768, 720, 640, 480, 400, 320, 240]

# 图片高度
H=[1200, 1080, 768, 600, 480, 1280, 800, 240, 320]

# 默认图片宽度
DEFAULT_W=1920

# 默认图片高度
DEFAULT_H=1080

# 默认地区
DEFAULT_MKT="zh-CN"

# 默认返回数据数量
DEFAULT_LIMIT=10

# 返回的最大数据数量
LIMIT_DATA=100
