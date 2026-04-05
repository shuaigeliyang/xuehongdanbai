"""
血浆游离血红蛋白检测系统 - 自动化测试脚本
作者: 哈雷酱大小姐 (￣▽￣)／

使用方法:
    python auto_test.py

功能: 自动测试核心API接口，验证系统可用性
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

# ============ 配置 ============
BASE_URL = "http://localhost:8000"
TEST_RESULTS = []

# ============ 颜色输出 ============
class Colors:
    OK = '\033[92m'      # 绿色
    FAIL = '\033[91m'    # 红色
    WARN = '\033[93m'    # 黄色
    INFO = '\033[94m'    # 蓝色
    BOLD = '\033[1m'     # 加粗
    END = '\033[0m'      # 结束

# ============ 测试函数 ============

def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.INFO}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.INFO}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.INFO}{'='*60}{Colors.END}\n")

def print_test(name: str, status: bool, details: str = ""):
    """打印测试结果"""
    status_icon = f"{Colors.OK}✓{Colors.END}" if status else f"{Colors.FAIL}✗{Colors.END}"
    status_text = f"{Colors.OK}通过{Colors.END}" if status else f"{Colors.FAIL}失败{Colors.END}"

    print(f"{status_icon} {name:50s} [{status_text}]")
    if details:
        print(f"  └─ {details}")

    TEST_RESULTS.append({
        "name": name,
        "status": status,
        "details": details
    })

def test_health_check() -> bool:
    """测试健康检查接口"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        data = response.json()

        is_ok = (
            response.status_code == 200 and
            data.get("status") == "healthy" and
            "simulator_connected" in data
        )

        print_test(
            "健康检查接口",
            is_ok,
            f"状态={data.get('status')}, 模拟器连接={data.get('simulator_connected')}"
        )
        return is_ok

    except Exception as e:
        print_test("健康检查接口", False, str(e))
        return False

def test_prediction(a375: float, a405: float, a450: float, expected_range: Tuple[float, float]) -> bool:
    """测试预测接口"""
    try:
        payload = {
            "absorbance": {
                "a375": a375,
                "a405": a405,
                "a450": a450
            },
            "model_type": "rf"
        }

        response = requests.post(f"{BASE_URL}/api/predict", json=payload, timeout=10)
        data = response.json()

        concentration = data.get("prediction", {}).get("concentration", 0)
        is_in_range = expected_range[0] <= concentration <= expected_range[1]
        has_confidence = "confidence" in data.get("prediction", {})

        test_name = f"浓度预测 (A375={a375}, A405={a405}, A450={a450})"
        is_ok = response.status_code == 200 and is_in_range and has_confidence

        print_test(
            test_name,
            is_ok,
            f"预测浓度={concentration:.4f} g/L, 置信度={data.get('prediction', {}).get('confidence', 0)}"
        )
        return is_ok

    except Exception as e:
        print_test(f"浓度预测 (A375={a375}, A405={a405}, A450={a450})", False, str(e))
        return False

def test_simulator(concentration: float) -> bool:
    """测试模拟器接口"""
    try:
        payload = {
            "concentration": concentration,
            "noise_level": 0.01
        }

        response = requests.post(f"{BASE_URL}/api/simulator/measure", json=payload, timeout=10)
        data = response.json()

        has_absorbance = "absorbance" in data
        has_correct_keys = all(k in data.get("absorbance", {}) for k in ["a375", "a405", "a450"])

        if has_absorbance:
            abs_data = data["absorbance"]
            # 验证 A405 > A375 (符合朗伯-比尔定律)
            ratio_valid = abs_data.get("a405", 0) > abs_data.get("a375", 0)
        else:
            ratio_valid = False

        test_name = f"模拟器测量 (浓度={concentration} g/L)"
        is_ok = response.status_code == 200 and has_absorbance and has_correct_keys and ratio_valid

        print_test(
            test_name,
            is_ok,
            f"A375={abs_data.get('a375', 0):.4f}, A405={abs_data.get('a405', 0):.4f}, A450={abs_data.get('a450', 0):.4f}"
        )
        return is_ok

    except Exception as e:
        print_test(f"模拟器测量 (浓度={concentration} g/L)", False, str(e))
        return False

def test_model_info() -> bool:
    """测试模型信息接口"""
    try:
        response = requests.get(f"{BASE_URL}/api/model/info", timeout=5)
        data = response.json()

        has_performance = "performance_metrics" in data
        has_feature_importance = "feature_importance" in data

        is_ok = response.status_code == 200 and has_performance and has_feature_importance

        print_test(
            "模型信息查询",
            is_ok,
            f"R²={data.get('performance_metrics', {}).get('test_r2', 0):.4f}"
        )
        return is_ok

    except Exception as e:
        print_test("模型信息查询", False, str(e))
        return False

def test_model_compare() -> bool:
    """测试模型对比接口"""
    try:
        response = requests.get(f"{BASE_URL}/api/model/compare", timeout=5)
        data = response.json()

        has_rf = "random_forest" in data
        has_svr = "svr" in data
        has_recommendation = "recommendation" in data

        is_ok = response.status_code == 200 and has_rf and has_svr and has_recommendation

        print_test(
            "模型性能对比",
            is_ok,
            f"推荐模型={data.get('recommendation', 'N/A')}"
        )
        return is_ok

    except Exception as e:
        print_test("模型性能对比", False, str(e))
        return False

def test_history() -> bool:
    """测试历史记录接口"""
    try:
        response = requests.get(f"{BASE_URL}/api/history?limit=100", timeout=5)
        data = response.json()

        has_total = "total" in data
        has_records = "records" in data

        is_ok = response.status_code == 200 and has_total and has_records

        print_test(
            "历史记录查询",
            is_ok,
            f"总记录数={data.get('total', 0)}"
        )
        return is_ok

    except Exception as e:
        print_test("历史记录查询", False, str(e))
        return False

def test_statistics() -> bool:
    """测试统计摘要接口"""
    try:
        response = requests.get(f"{BASE_URL}/api/statistics/summary", timeout=5)
        data = response.json()

        has_total = "total_predictions" in data
        has_avg = "avg_concentration" in data

        is_ok = response.status_code == 200 and has_total and has_avg

        print_test(
            "统计摘要查询",
            is_ok,
            f"总预测数={data.get('total_predictions', 0)}, 平均浓度={data.get('avg_concentration', 0):.4f}"
        )
        return is_ok

    except Exception as e:
        print_test("统计摘要查询", False, str(e))
        return False

def run_all_tests():
    """运行所有测试"""
    print_header("血浆游离血红蛋白检测系统 - 自动化测试")

    print(f"{Colors.INFO}测试目标: {BASE_URL}{Colors.END}")
    print(f"{Colors.INFO}开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}\n")

    # ============ 测试组 1: 系统健康 ============
    print(f"{Colors.BOLD}[1/4] 系统健康检查{Colors.END}")
    test_health_check()
    time.sleep(1)

    # ============ 测试组 2: 预测功能 ============
    print(f"\n{Colors.BOLD}[2/4] 浓度预测功能{Colors.END}")
    test_prediction(0.025, 0.035, 0.020, (0.01, 0.05))   # 低浓度
    test_prediction(0.125, 0.175, 0.100, (0.10, 0.15))   # 中浓度
    test_prediction(0.225, 0.315, 0.180, (0.20, 0.30))   # 高浓度
    test_prediction(0.000, 0.000, 0.000, (0.00, 0.01))   # 零浓度
    time.sleep(1)

    # ============ 测试组 3: 模拟器功能 ============
    print(f"\n{Colors.BOLD}[3/4] 数据模拟器{Colors.END}")
    test_simulator(0.05)   # 低浓度
    test_simulator(0.15)   # 中浓度
    test_simulator(0.25)   # 高浓度
    time.sleep(1)

    # ============ 测试组 4: 数据查询 ============
    print(f"\n{Colors.BOLD}[4/4] 数据查询功能{Colors.END}")
    test_model_info()
    test_model_compare()
    test_history()
    test_statistics()

    # ============ 统计结果 ============
    print_header("测试结果汇总")

    total = len(TEST_RESULTS)
    passed = sum(1 for r in TEST_RESULTS if r["status"])
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"总测试数: {total}")
    print(f"{Colors.OK}通过数: {passed}{Colors.END}")
    print(f"{Colors.FAIL}失败数: {failed}{Colors.END}")
    print(f"通过率: {pass_rate:.1f}%\n")

    if failed > 0:
        print(f"{Colors.FAIL}失败的测试用例:{Colors.END}")
        for result in TEST_RESULTS:
            if not result["status"]:
                print(f"  • {result['name']}: {result['details']}")
        print()

    # ============ 最终评价 ============
    print(f"{Colors.BOLD}测试结论:{Colors.END}")
    if pass_rate == 100:
        print(f"  {Colors.OK}✓ 所有测试通过！系统运行正常，可以放心使用。{Colors.END}")
    elif pass_rate >= 80:
        print(f"  {Colors.WARN}⚠ 大部分测试通过，系统基本可用，存在少量问题。{Colors.END}")
    elif pass_rate >= 50:
        print(f"  {Colors.WARN}⚠ 部分测试失败，建议检查配置和依赖。{Colors.END}")
    else:
        print(f"  {Colors.FAIL}✗ 大量测试失败，系统存在严重问题，需要修复。{Colors.END}")

    print(f"\n{Colors.INFO}结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    print(f"{Colors.INFO}耗时: {time.time() - start_time:.2f} 秒{Colors.END}\n")

# ============ 主程序 ============
if __name__ == "__main__":
    start_time = time.time()

    try:
        run_all_tests()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARN}测试被用户中断{Colors.END}")
    except Exception as e:
        print(f"\n\n{Colors.FAIL}测试过程中发生错误: {e}{Colors.END}")
