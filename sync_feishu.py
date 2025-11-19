import os
import requests
import csv
import json

# 从 GitHub Secrets 获取配置
APP_ID = os.environ['FEISHU_APP_ID']
APP_SECRET = os.environ['FEISHU_APP_SECRET']
APP_TOKEN = os.environ['FEISHU_APP_TOKEN']
TABLE_ID = os.environ['FEISHU_TABLE_ID']

def get_tenant_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    payload = {"app_id": APP_ID, "app_secret": APP_SECRET}
    resp = requests.post(url, headers=headers, json=payload)
    return resp.json().get("tenant_access_token")

def get_records(token):
    # 使用 v1 接口获取记录
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}"}
    # page_size 调大，确保一次拿全（如果超过100条需要写分页循环，目前先这样）
    params = {"page_size": 100, "text_field_as_array": False} 
    resp = requests.get(url, headers=headers, params=params)
    return resp.json().get("data", {}).get("items", [])

# === 核心修复：清洗飞书数据的函数 ===
def clean_feishu_value(value):
    """
    把飞书各种复杂的字段格式（List, Dict）转换成纯字符串
    """
    if value is None:
        return ""
        
    # 情况1: 文本字段 (List 包含 Dict) -> [{'text': '内容', 'type': 'text'}]
    if isinstance(value, list):
        texts = []
        for item in value:
            if isinstance(item, dict):
                # 提取 text 字段
                if 'text' in item:
                    texts.append(item['text'])
                # 或者是人员字段里的 name
                elif 'name' in item:
                    texts.append(item['name'])
            else:
                # 如果列表里直接是字符串（比如多选标签）
                texts.append(str(item))
        return "".join(texts) # 拼接起来
    
    # 情况2: 链接字段 (Dict) -> {'link': 'url', 'text': '描述'}
    if isinstance(value, dict):
        if 'link' in value:
            return value['link']
        if 'text' in value:
            return value['text']
            
    # 情况3: 普通字符串或数字
    return str(value)

def main():
    token = get_tenant_access_token()
    records = get_records(token)
    
    # 定义 CSV 表头
    field_names = ['周期', '日期', '竞品品牌', '追踪维度（单选）', '事实描述', '分析', '信息源']
    
    with open('data.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        
        for record in records:
            fields = record['fields']
            
            # 使用 clean_feishu_value 函数清洗每个字段
            row = {
                '周期': clean_feishu_value(fields.get('周期')),
                '日期': clean_feishu_value(fields.get('日期')), 
                # 日期在飞书是个时间戳，如果飞书里是日期字段，这里会拿到 173xxxx 这种数字
                # 如果飞书里日期是文本，就是文本。暂时先转成字符串。
                
                '竞品品牌': clean_feishu_value(fields.get('竞品品牌')),
                '追踪维度（单选）': clean_feishu_value(fields.get('追踪维度（单选）')),
                '事实描述': clean_feishu_value(fields.get('事实描述')),
                '分析': clean_feishu_value(fields.get('分析')),
                '信息源': clean_feishu_value(fields.get('信息源'))
            }
            
            # 针对“日期”做个特殊处理：如果是时间戳(13位数字)，稍微格式化一下（可选）
            # 如果您飞书里日期列就是文本格式 "2025-11-03"，那上面那行就够了。
            
            writer.writerow(row)
            
    print(f"成功同步 {len(records)} 条数据，且已清洗格式。")

if __name__ == "__main__":
    main()
