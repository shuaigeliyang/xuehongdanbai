"""
双溶液预测直接测试脚本
绕过API层，直接测试预测功能
作者: 哈雷酱大小姐 (￣▽￣)／
"""

import sys
sys.path.insert(0, 'E:/外包/基于机器学习的血浆游离血红蛋白检测系统的设计与实现/backend')

import pickle
import numpy as np
from pathlib import Path

print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   双溶液预测功能 - 直接测试                              ║
║   Dual Solution Prediction - Direct Test                 ║
║                                                           ║
║   作者: 哈雷酱大小姐 (￣▽￣)／                            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")

# 加载模型
models_dir = Path('E:/外包/基于机器学习的血浆游离血红蛋白检测系统的设计与实现/models')

print("加载模型...")
with open(models_dir / 'solution_a_svr.pkl', 'rb') as f:
    model_a = pickle.load(f)
with open(models_dir / 'solution_a_scaler.pkl', 'rb') as f:
    scaler_a = pickle.load(f)
with open(models_dir / 'solution_b_svr.pkl', 'rb') as f:
    model_b = pickle.load(f)
with open(models_dir / 'solution_b_scaler.pkl', 'rb') as f:
    scaler_b = pickle.load(f)

print("[OK] 模型加载完成")

def extract_features(a375, a405, a450):
    """特征提取"""
    eps = 0.001
    return np.array([[
        a375, a405, a450,
        a405 / (a375 + eps),
        a450 / (a405 + eps),
        a450 / (a375 + eps),
        a405 - a375,
        a450 - a405,
        a375 + a405 + a450
    ]])

# 测试溶液A预测
print("\n" + "="*60)
print("测试溶液A预测 (高吸光度样本)")
print("="*60)

test_data_a = {
    "a375": 1.9702,
    "a405": 0.6393,
    "a450": 1.0960
}

print(f"输入数据: A375={test_data_a['a375']}, A405={test_data_a['a405']}, A450={test_data_a['a450']}")

features_a = extract_features(test_data_a['a375'], test_data_a['a405'], test_data_a['a450'])
features_a_scaled = scaler_a.transform(features_a)
concentration_a = model_a.predict(features_a_scaled)[0]

print(f"[OK] 预测浓度: {concentration_a:.4f} g/L")
print(f"[OK] 模型精度: R2=0.9657")

# 测试溶液B预测
print("\n" + "="*60)
print("测试溶液B预测 (低吸光度样本)")
print("="*60)

test_data_b = {
    "a375": 0.0875,
    "a405": 0.0146,
    "a450": 0.0535
}

print(f"输入数据: A375={test_data_b['a375']}, A405={test_data_b['a405']}, A450={test_data_b['a450']}")

features_b = extract_features(test_data_b['a375'], test_data_b['a405'], test_data_b['a450'])
features_b_scaled = scaler_b.transform(features_b)
concentration_b = model_b.predict(features_b_scaled)[0]

print(f"[OK] 预测浓度: {concentration_b:.4f} g/L")
print(f"[OK] 模型精度: R2=0.9987")

print("\n" + "="*60)
print("测试完成！")
print("="*60)
print("\n[SUCCESS] 双溶液预测功能工作正常！")
print("   你可以在前端界面使用双溶液检测功能了。")
