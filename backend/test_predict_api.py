"""测试预测API"""
import requests
import json

url = "http://localhost:5000/api/predict"
data = {
    "absorbance": {
        "a375": 0.1500,
        "a405": 0.2100,
        "a450": 0.1100
    },
    "sample_info": {
        "sample_id": "NEW-001",
        "sample_type": "验证样本",
        "notes": "重启后验证数据持久化"
    },
    "model_type": "rf"
}

response = requests.post(url, json=data)
print("状态码:", response.status_code)
print("响应内容:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
