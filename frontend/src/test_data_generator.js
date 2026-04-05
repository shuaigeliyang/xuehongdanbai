"""
测试数据生成器
用于为血浆游离血红蛋白检测系统生成测试数据
"""

import random
import json
from datetime import datetime, timedelta
import math

class TestDataGenerator:
    def __init__(self):
        self.concentration_ranges = [
            (0.0, 0.05, "正常水平"),
            (0.05, 0.15, "轻微升高"),
            (0.15, 0.25, "中等升高"),
            (0.25, 0.35, "较高水平"),
        ]
        
        self.sample_types = ["待测样本", "质控样本", "标准品"]
        self.model_types = ["rf", "svr"]

    def generate_absorbance(self, concentration):
        """根据浓度生成吸光度值（基于实际数据规律）"""
        base_375 = 1.2 - concentration * 2.5 + random.uniform(-0.05, 0.05)
        base_405 = 0.12 - concentration * 0.35 + random.uniform(-0.01, 0.01)
        base_450 = 1.0 - concentration * 0.5 + random.uniform(-0.03, 0.03)
        
        return {
            "a375": round(max(0.05, base_375), 4),
            "a405": round(max(0.01, base_405), 4),
            "a450": round(max(0.02, base_450), 4)
        }

    def generate_single_prediction(self, sample_id=None, concentration=None, model_type="rf"):
        """生成单条预测数据"""
        if concentration is None:
            conc_range = random.choice(self.concentration_ranges)
            concentration = random.uniform(conc_range[0], conc_range[1])
        
        absorbance = self.generate_absorbance(concentration)
        
        if sample_id is None:
            sample_id = f"SAMPLE-{random.randint(1000, 9999)}"
        
        return {
            "sample_id": sample_id,
            "sample_type": random.choice(self.sample_types),
            "absorbance": absorbance,
            "model_type": model_type,
            "expected_concentration": round(concentration, 4)
        }

    def generate_test_suite(self, n_samples=20):
        """生成完整的测试套件数据"""
        test_suite = []
        
        for i in range(n_samples):
            conc_range = self.concentration_ranges[i % len(self.concentration_ranges)]
            concentration = random.uniform(conc_range[0], conc_range[1])
            model = self.model_types[i % len(self.model_types)]
            
            sample = self.generate_single_prediction(
                sample_id=f"TEST-{i+1:03d}",
                concentration=concentration,
                model_type=model
            )
            test_suite.append(sample)
        
        return test_suite

    def generate_history_records(self, n_records=15):
        """生成历史记录数据（模拟已经预测过的记录）"""
        records = []
        base_time = datetime.now()
        
        for i in range(n_records):
            conc_range = random.choice(self.concentration_ranges)
            concentration = random.uniform(conc_range[0], conc_range[1])
            absorbance = self.generate_absorbance(concentration)
            model = random.choice(self.model_types)
            
            record = {
                "id": f"REC-{datetime.now().strftime('%Y%m%d')}{i+1:03d}",
                "request": {
                    "absorbance": absorbance,
                    "sample_info": {
                        "sample_id": f"HS-{i+1:04d}",
                        "sample_type": random.choice(self.sample_types),
                        "notes": f"常规检测样本 #{i+1}"
                    },
                    "model_type": model
                },
                "result": {
                    "sample_info": {
                        "sample_id": f"HS-{i+1:04d}",
                        "sample_type": random.choice(self.sample_types)
                    },
                    "prediction": {
                        "concentration": round(concentration + random.uniform(-0.01, 0.01), 4),
                        "confidence": round(random.uniform(0.85, 0.98), 4),
                        "model_type": model,
                        "timestamp": (base_time - timedelta(minutes=random.randint(1, 120))).strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "model_info": {
                        "model_type": model,
                        "test_r2": round(random.uniform(0.92, 0.99), 4),
                        "test_mae": round(random.uniform(0.005, 0.02), 4),
                        "test_mse": round(random.uniform(0.0001, 0.0005), 6)
                    }
                },
                "created_at": (base_time - timedelta(minutes=random.randint(1, 120))).isoformat()
            }
            records.append(record)
        
        return records

    def generate_api_test_data(self):
        """生成可直接用于API测试的数据"""
        return {
            "single_prediction": {
                "absorbance": {
                    "a375": 0.1523,
                    "a405": 0.0895,
                    "a450": 0.7342
                },
                "sample_info": {
                    "sample_id": "API-TEST-001",
                    "sample_type": "待测样本",
                    "notes": "API测试样本"
                },
                "model_type": "rf"
            },
            "batch_prediction": [
                {
                    "absorbance": self.generate_absorbance(0.05),
                    "sample_info": {"sample_id": f"BATCH-{i+1:03d}", "sample_type": "待测样本"},
                    "model_type": "rf"
                }
                for i in range(5)
            ],
            "simulator_measurement": {
                "concentration": 0.15
            },
            "edge_cases": [
                {"a375": 0.15, "a405": 0.06, "a450": 0.69, "expected": "低浓度正常"},
                {"a375": 0.80, "a405": 0.02, "a450": 0.99, "expected": "高浓度样本"},
                {"a375": 0.17, "a405": 0.08, "a450": 0.70, "expected": "零浓度边界"},
                {"a375": 1.20, "a405": 0.12, "a450": 1.04, "expected": "最大吸光度"},
            ]
        }

    def save_test_data(self, filename="test_data.json"):
        """保存所有测试数据到文件"""
        data = {
            "generated_at": datetime.now().isoformat(),
            "test_suite": self.generate_test_suite(20),
            "history_records": self.generate_history_records(15),
            "api_test_data": self.generate_api_test_data()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"测试数据已保存到: {filename}")
        return data

def print_test_guide():
    """打印测试指南"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           血浆游离血红蛋白检测系统 - 测试数据指南             ║
╚══════════════════════════════════════════════════════════════╝

【测试数据说明】

1. 单次预测测试数据:
   - 样本编号: API-TEST-001
   - 375nm吸光度: 0.1523
   - 405nm吸光度: 0.0895  
   - 450nm吸光度: 0.7342
   - 模型类型: rf (Random Forest)

2. 边界测试数据:
   ┌─────────────────────────────────────────────────────────┐
   │ 场景          │ A375    │ A405    │ A450    │ 预期结果 │
   ├─────────────────────────────────────────────────────────┤
   │ 低浓度正常    │ 0.1500  │ 0.0600  │ 0.6900  │ ~0.0 g/L │
   │ 轻微溶血      │ 0.1400  │ 0.0300  │ 0.0800  │ ~0.05 g/L│
   │ 中等溶血      │ 0.1200  │ 0.0250  │ 0.0700  │ ~0.15 g/L│
   │ 严重溶血      │ 0.0800  │ 0.0200  │ 0.0600  │ ~0.25 g/L│
   │ 最大吸光度    │ 1.2000  │ 0.1200  │ 1.0400  │ ~0.0 g/L │
   └─────────────────────────────────────────────────────────┘

3. 推荐测试场景:
   - 测试正常样本 (浓度 < 0.05 g/L)
   - 测试轻微溶血 (浓度 0.05-0.15 g/L)
   - 测试中等溶血 (浓度 0.15-0.25 g/L)
   - 测试严重溶血 (浓度 > 0.25 g/L)

4. API测试端点:
   - POST /api/predict - 单次预测
   - POST /api/predict/batch - 批量预测
   - POST /api/simulator/measure - 模拟测量
   - GET /api/history - 获取历史记录
   - GET /api/model/compare - 模型对比
   - GET /api/statistics/summary - 统计摘要

""")

if __name__ == "__main__":
    generator = TestDataGenerator()
    data = generator.save_test_data("frontend/test_data.json")
    print_test_guide()
    
    print("\n【快速测试数据 - 可直接复制使用】\n")
    print("1. 低浓度正常样本:")
    print(f"   A375=0.1500, A405=0.0600, A450=0.6900")
    print("\n2. 轻微溶血样本:")
    print(f"   A375=0.1400, A405=0.0300, A450=0.0800")
    print("\n3. 中等溶血样本:")
    print(f"   A375=0.1200, A405=0.0250, A450=0.0700")
    print("\n4. 严重溶血样本:")
    print(f"   A375=0.0800, A405=0.0200, A450=0.0600")
