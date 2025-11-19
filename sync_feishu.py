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
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page_size": 100} # 每次取100条，如果数据多需要分页逻辑
    resp = requests.get(url, headers=headers, params=params)
    return resp.json().get("data", {}).get("items", [])

def main():
    token = get_tenant_access_token()
    records = get_records(token)
    
    # 定义 CSV 表头（必须和飞书里的列名对应，也必须和网页代码对应）
    # 请确保飞书表格里有这些列：周期, 日期, 竞品品牌, 追踪维度（单选）, 事实描述, 分析, 信息源
    field_names = ['周期', '日期', '竞品品牌', '追踪维度（单选）', '事实描述', '分析', '信息源']
    
    with open('data.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        
        for record in records:
            fields = record['fields']
            # 处理可能为空的字段，防止报错
            row = {
                '周期': fields.get('周期', ''),
                '日期': fields.get('日期', ''), # 如果是日期格式可能需要转换时间戳
                '竞品品牌': fields.get('竞品品牌', ''),
                '追踪维度（单选）': fields.get('追踪维度（单选）', ''),
                '事实描述': fields.get('事实描述', ''),
                '分析': fields.get('分析', ''),
                '信息源': fields.get('信息源', {}).get('link', '') if isinstance(fields.get('信息源'), dict) else fields.get('信息源', '')
            }
            writer.writerow(row)
            
    print(f"成功同步 {len(records)} 条数据到 data.csv")

if __name__ == "__main__":
    main()
