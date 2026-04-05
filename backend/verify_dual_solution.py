"""
双溶液检测功能验证脚本
作者: 哈雷酱大小姐 (￣▽￣)／
用途：快速验证双溶液预测功能是否正常工作
"""

import requests
import json
import sys
from pathlib import Path

# API配置
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 10

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health_check():
    """测试健康检查"""
    print_section("[1/5] 健康检查")

    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=TIMEOUT)
        data = response.json()

        print(f"✓ 系统状态: {data.get('status', 'unknown')}")
        print(f"✓ 消息: {data.get('message', 'N/A')}")
        print(f"✓ 模型已加载: {data.get('models_loaded', False)}")

        return data.get('status') == 'healthy'
    except Exception as e:
        print(f"✗ 健康检查失败: {e}")
        return False

def test_get_solutions():
    """测试获取溶液信息"""
    print_section("[2/5] 获取溶液信息")

    try:
        response = requests.get(f"{API_BASE_URL}/api/solutions", timeout=TIMEOUT)
        data = response.json()

        print(f"✓ 溶液总数: {data.get('count', 0)}")
        print(f"✓ 已加载模型数: {data.get('models_loaded', 0)}")

        solutions = data.get('solutions', {})
        for key, info in solutions.items():
            print(f"\n  溶液: {info.get('name', key)}")
            print(f"  描述: {info.get('description', 'N/A')}")
            print(f"  精度: R²={info.get('accuracy', 0):.4f}")
            print(f"  可用: {'是' if info.get('available') else '否'}")

        return len(solutions) > 0
    except Exception as e:
        print(f"✗ 获取溶液信息失败: {e}")
        return False

def test_solution_a_prediction():
    """测试溶液A预测"""
    print_section("[3/5] 溶液A预测测试")

    try:
        # 溶液A测试数据（高吸光度）
        test_data = {
            "a375": 1.9702,
            "a405": 0.6393,
            "a450": 1.0960,
            "solution_type": "solution_a",
            "sample_id": "TEST-A-001",
            "sample_type": "溶液A样本",
            "notes": "验证测试"
        }

        print(f"输入数据:")
        print(f"  A375: {test_data['a375']}")
        print(f"  A405: {test_data['a405']}")
        print(f"  A450: {test_data['a450']}")
        print(f"  溶液类型: {test_data['solution_type']}")

        response = requests.post(
            f"{API_BASE_URL}/api/predict/dual",
            json=test_data,
            timeout=TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 预测成功!")
            print(f"  预测浓度: {data['prediction']['concentration']:.4f} g/L")
            print(f"  置信度: {data['prediction']['confidence']:.4f}")
            print(f"  使用溶液: {data['solution_name']}")
            print(f"  模型类型: {data['prediction']['model_type']}")
            return True
        else:
            print(f"✗ 预测失败: HTTP {response.status_code}")
            print(f"  错误信息: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 溶液A预测失败: {e}")
        return False

def test_solution_b_prediction():
    """测试溶液B预测"""
    print_section("[4/5] 溶液B预测测试")

    try:
        # 溶液B测试数据（低吸光度）
        test_data = {
            "a375": 0.0875,
            "a405": 0.0146,
            "a450": 0.0535,
            "solution_type": "solution_b",
            "sample_id": "TEST-B-001",
            "sample_type": "溶液B样本",
            "notes": "验证测试"
        }

        print(f"输入数据:")
        print(f"  A375: {test_data['a375']}")
        print(f"  A405: {test_data['a405']}")
        print(f"  A450: {test_data['a450']}")
        print(f"  溶液类型: {test_data['solution_type']}")

        response = requests.post(
            f"{API_BASE_URL}/api/predict/dual",
            json=test_data,
            timeout=TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 预测成功!")
            print(f"  预测浓度: {data['prediction']['concentration']:.4f} g/L")
            print(f"  置信度: {data['prediction']['confidence']:.4f}")
            print(f"  使用溶液: {data['solution_name']}")
            print(f"  模型类型: {data['prediction']['model_type']}")
            return True
        else:
            print(f"✗ 预测失败: HTTP {response.status_code}")
            print(f"  错误信息: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 溶液B预测失败: {e}")
        return False

def test_invalid_solution():
    """测试无效溶液类型"""
    print_section("[5/5] 无效溶液类型测试")

    try:
        test_data = {
            "a375": 1.0,
            "a405": 0.5,
            "a450": 0.8,
            "solution_type": "solution_invalid",
            "sample_id": "TEST-INVALID"
        }

        response = requests.post(
            f"{API_BASE_URL}/api/predict/dual",
            json=test_data,
            timeout=TIMEOUT
        )

        if response.status_code == 400:
            print("✓ 正确拒绝无效溶液类型")
            print(f"  错误信息: {response.json().get('detail', 'N/A')}")
            return True
        else:
            print(f"✗ 未正确处理无效溶液类型: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def main():
    """主测试流程"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   双溶液血浆游离血红蛋白检测系统 - 功能验证              ║
║   Dual-Solution FHb Detection System - Verification      ║
║                                                           ║
║   作者: 哈雷酱大小姐 (￣▽￣)／                            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # 检查后端是否运行
    print(f"正在连接到 {API_BASE_URL} ...")

    results = {
        "健康检查": test_health_check(),
        "获取溶液信息": test_get_solutions(),
        "溶液A预测": test_solution_a_prediction(),
        "溶液B预测": test_solution_b_prediction(),
        "无效溶液处理": test_invalid_solution()
    }

    # 总结
    print_section("验证结果总结")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！双溶液功能正常工作！")
        print("   可以开始使用前端界面进行检测。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查后端服务状态。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
