# -*- coding:utf-8 -*-
# 一次性迁移：修正 en-US / en-CA 历史壁纸日期
# 背景：采集逻辑曾按必应 enddate（UTC 日期）记录壁纸日期，UTC- 时区市场（en-US/en-CA）
#       的记录值比当地展示日期多 1 天（例如当地 10-18 的壁纸被记为 10-19）
# 规则：以 copyrightlink 中的 HpDate（壁纸上线的 UTC 时刻）为基准，换算当地日期后重写 datetime；
#       同一当地日期出现重复壁纸（同一 hsh，历史上重复收录所致）时只保留一条；
#       若同一日期出现不同壁纸（hsh 不同）则中止写入并报告，避免误删
# 幂等：已修正的记录 HpDate 换算结果与 datetime 一致，重复执行无副作用
# 数据流：有 MONGODB_URI 时先修正 MongoDB，再由 Mongo 导出 JSON 文件；否则只修正本地 JSON 文件
import os
import sys
import re
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from utils.util import to_local_date

REGIONS = ["en-US", "en-CA"]
HP_DATE_PATTERN = re.compile(r'HpDate%3a%22(\d{8})_(\d{4})')

# 以 HpDate 换算当地日期重写 datetime，返回 (修正数, 无HpDate跳过数)
def shift_records(data):
    fixed = 0
    no_hp = 0
    for item in data:
        m = HP_DATE_PATTERN.search(item.get('copyrightlink', ''))
        if not m:
            no_hp += 1  # 无基准时刻（如参考数据回填的记录）：保守跳过
            continue
        true_date = to_local_date(m.group(1) + m.group(2))
        if true_date != item['datetime']:
            item['datetime'] = true_date
            fixed += 1
    return fixed, no_hp

# 同一壁纸的判定：OHR 图片标识与 HpDate 都一致（同一壁纸可能被重复收录且 hsh 不同，hsh 会随抓取时间变化）
def wallpaper_key(item):
    m = re.search(r'id=(OHR\.[^_&]+)', item.get('url', ''))
    ohr = m.group(1) if m else item.get('url', '')
    hp = HP_DATE_PATTERN.search(item.get('copyrightlink', ''))
    return (ohr, hp.group(1) if hp else '')

# 按日期倒序排序；同一日期的重复记录要求 OHR 图片标识与 HpDate 一致（同一壁纸重复收录）才去重保留一条，
# 否则中止；最后重排 id（保持 id = 从旧到新序号 的约定）。返回 (保留的记录列表, 去重条数)
def normalize(data):
    data.sort(key=lambda x: (x['datetime'], x.get('hsh', '')), reverse=True)
    kept = []
    dropped = 0
    for item in data:
        if kept and kept[-1]['datetime'] == item['datetime']:
            if wallpaper_key(kept[-1]) != wallpaper_key(item):
                raise ValueError("日期%s出现不同壁纸（OHR或HpDate不一致），已中止写入，请人工核查：%s vs %s" % (
                    item['datetime'], kept[-1].get('url', ''), item.get('url', '')))
            dropped += 1  # 同一壁纸重复收录，丢弃本条
            continue
        kept.append(item)
    for i, item in enumerate(kept):
        item['id'] = len(kept) - i
    return kept, dropped

# 修正 MongoDB 中指定地区的记录，返回 (修正后的完整数据（不含 _id）, 修正数, 无HpDate数, 去重数)
def fix_mongo(mkt):
    from utils.mongodb_utils import db_init
    collection = db_init(mkt)
    docs = list(collection.find({}))
    fixed, no_hp = shift_records(docs)
    kept, dropped = normalize(docs)
    kept_ids = {doc['_id'] for doc in kept}
    for doc in docs:
        if doc['_id'] in kept_ids:
            collection.update_one({'_id': doc['_id']}, {'$set': {'datetime': doc['datetime'], 'id': doc['id']}})
        else:
            collection.delete_one({'_id': doc['_id']})
    for doc in kept:
        doc.pop('_id', None)
    return kept, fixed, no_hp, dropped

# 封装 json 响应结构并写入 data/<mkt>_all.json（与 run.py 的 write_bing_json 格式一致）
def write_bing_json(mkt, json_data):
    payload = {'code': 200, 'msg': '操作成功', 'total': len(json_data), 'data': json_data}
    with open(f'data/{mkt}_all.json', 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(mkt + ":已同步json数据")

if __name__ == '__main__':
    use_mongo = bool(os.environ.get("MONGODB_URI"))
    print("数据源：MongoDB" if use_mongo else "数据源：本地JSON文件（未配置 MONGODB_URI）")
    for mkt in REGIONS:
        if use_mongo:
            data, fixed, no_hp, dropped = fix_mongo(mkt)
        else:
            with open(f'data/{mkt}_all.json', 'r', encoding='utf-8') as f:
                data = json.load(f)['data']
            fixed, no_hp = shift_records(data)
            data, dropped = normalize(data)
        write_bing_json(mkt, data)
        print(mkt + ":现存" + str(len(data)) + "条，日期修正" + str(fixed) + "条，去除重复收录" + str(dropped) + "条，无HpDate跳过" + str(no_hp) + "条")
