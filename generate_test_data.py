import random
import json
from datetime import datetime, timedelta

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
        base_375 = 1.2 - concentration * 2.5 + random.uniform(-0.05, 0.05)
        base_405 = 0.12 - concentration * 0.35 + random.uniform(-0.01, 0.01)
        base_450 = 1.0 - concentration * 0.5 + random.uniform(-0.03, 0.03)
        return {
            "a375": round(max(0.05, base_375), 4),
            "a405": round(max(0.01, base_405), 4),
            "a450": round(max(0.02, base_450), 4)
        }

    def generate_history_records(self, n_records=15):
        records = []
        base_time = datetime.now()
        for i in range(n_records):
            conc_range = random.choice(self.concentration_ranges)
            concentration = random.uniform(conc_range[0], conc_range[1])
            absorbance = self.generate_absorbance(concentration)
            model = random.choice(self.model_types)
            timestamp = base_time - timedelta(minutes=random.randint(1, 120))
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
                        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "model_info": {
                        "model_type": model,
                        "test_r2": round(random.uniform(0.92, 0.99), 4),
                        "test_mae": round(random.uniform(0.005, 0.02), 4),
                        "test_mse": round(random.uniform(0.0001, 0.0005), 6)
                    }
                },
                "created_at": timestamp.isoformat()
            }
            records.append(record)
        return records

    def generate_api_test_data(self):
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
            "simulator_measurement": {
                "concentration": 0.15
            },
            "edge_cases": [
                {"a375": 0.15, "a405": 0.06, "a450": 0.69, "description": "低浓度正常"},
                {"a375": 0.14, "a405": 0.03, "a450": 0.08, "description": "轻微溶血"},
                {"a375": 0.12, "a405": 0.025, "a450": 0.07, "description": "中等溶血"},
                {"a375": 0.08, "a405": 0.02, "a450": 0.06, "description": "严重溶血"},
            ],
            "quick_test_cases": [
                {"sample_id": "TEST-001", "a375": 0.1500, "a405": 0.0600, "a450": 0.6900, "expected": "正常"},
                {"sample_id": "TEST-002", "a375": 0.1400, "a405": 0.0300, "a450": 0.0800, "expected": "轻微溶血"},
                {"sample_id": "TEST-003", "a375": 0.1200, "a405": 0.0250, "a450": 0.0700, "expected": "中等溶血"},
                {"sample_id": "TEST-004", "a375": 0.0800, "a405": 0.0200, "a450": 0.0600, "expected": "严重溶血"},
            ]
        }

if __name__ == "__main__":
    generator = TestDataGenerator()
    data = {
        "generated_at": datetime.now().isoformat(),
        "history_records": generator.generate_history_records(15),
        "api_test_data": generator.generate_api_test_data()
    }
    with open("frontend/src/test_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("测试数据已生成!")
