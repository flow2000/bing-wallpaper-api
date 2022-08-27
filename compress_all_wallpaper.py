import os

root_path=""
out_path="./out"
pic_path="./bing"

# 调用ffmpeg
def Picture_Zoom(in_path, out_path):
    if not os.path.exists(out_path):
        # 命令编辑
        cmd_line = 'ffmpeg -i '+in_path+' -q 20 -vf scale=-1:768 -y '+out_path
        # 调用命令行
        os.system(cmd_line)

def replace_path(path):
    res = path.replace("\\","/")
    return res.replace("./bing","./out")

# 创建壁纸保存文件夹
def mkdir(path):
    path = replace_path(path)
    if not os.path.exists(path):
        os.makedirs(path)
        print(path+"+创建成功")
    return path


for root,dirs,files in os.walk(pic_path): 
    if len(files)!=0:
        out_dir = mkdir(root)
        for i in range(0,len(files)):
            name = files[i]
            Picture_Zoom(root.replace("\\","/")+"/"+name,out_dir+"/"+name)

