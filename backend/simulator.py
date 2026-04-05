"""
血浆游离血红蛋白检测系统 - 光谱仪模拟器（双溶液版本）
作者: 哈雷酱大小姐 (￣▽￣)／
功能: 模拟三波长光谱检测仪，生成测试数据，支持双溶液模式
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime


# 双溶液吸光度参数配置
SOLUTION_PARAMS = {
    'solution_a': {
        'name': '溶液A',
        'description': '2025年7月31日测量的标准溶液（高吸光度）',
        # 基于实际测量数据的统计参数
        'base_absorbance': {
            375: {'mean': 1.9702, 'std': 0.1},
            405: {'mean': 0.6393, 'std': 0.05},
            450: {'mean': 1.0960, 'std': 0.08}
        },
        # 浓度-吸光度关系参数（线性回归系数）
        'calibration': {
            375: {'slope': 6.5, 'intercept': 0.05},
            405: {'slope': 2.1, 'intercept': 0.02},
            450: {'slope': 3.6, 'intercept': 0.04}
        },
        # 浓度范围
        'concentration_range': (0.05, 0.3)
    },
    'solution_b': {
        'name': '溶液B',
        'description': '2025年8月12日测量的实验溶液（低吸光度）',
        'base_absorbance': {
            375: {'mean': 0.0875, 'std': 0.01},
            405: {'mean': 0.0146, 'std': 0.003},
            450: {'mean': 0.0535, 'std': 0.008}
        },
        'calibration': {
            375: {'slope': 0.28, 'intercept': 0.003},
            405: {'slope': 0.048, 'intercept': 0.001},
            450: {'slope': 0.17, 'intercept': 0.002}
        },
        'concentration_range': (0.02, 0.2)
    }
}


class SpectrometerSimulator:
    """光谱仪模拟器 - 基于朗伯-比尔定律"""

    def __init__(self, noise_level: float = 0.01, solution_type: str = 'solution_a'):
        """
        初始化模拟器

        Args:
            noise_level: 测量噪声水平（标准差）
            solution_type: 溶液类型 ('solution_a' 或 'solution_b')
        """
        self.noise_level = noise_level
        self.solution_type = solution_type
        self.current_solution = SOLUTION_PARAMS.get(solution_type, SOLUTION_PARAMS['solution_a'])

        # 三波长摩尔吸光系数（基于FHb特性）
        self.wavelengths = [375, 405, 450]
        self.epsilon = {
            375: 0.85,  # 紫外区
            405: 1.25,  # Soret带（特征峰）
            450: 0.65    # 可见区
        }

        # 仪器参数
        self.path_length = 1.0  # 光程（cm）
        self.is_connected = False
        self.last_calibration_date = None

    def set_solution_type(self, solution_type: str):
        """设置溶液类型"""
        if solution_type in SOLUTION_PARAMS:
            self.solution_type = solution_type
            self.current_solution = SOLUTION_PARAMS[solution_type]
            return True
        return False

    def connect(self) -> Dict[str, str]:
        """模拟连接设备"""
        self.is_connected = True
        return {
            "status": "success",
            "message": f"光谱仪模拟器已启动（{self.current_solution['name']}模式）",
            "device_info": {
                "model": "Simulated Spectrometer V2.0 (双溶液版)",
                "wavelengths": self.wavelengths,
                "manufacturer": "哈雷酱科技 (￣▽￣)／",
                "serial_number": f"SIMP-{datetime.now().strftime('%Y%m%d')}",
                "current_solution": self.solution_type,
                "solution_name": self.current_solution['name']
            }
        }

    def disconnect(self) -> Dict[str, str]:
        """断开设备连接"""
        self.is_connected = False
        return {
            "status": "success",
            "message": "设备已断开连接"
        }

    def auto_zero(self) -> Dict[str, str]:
        """自动调零"""
        if not self.is_connected:
            return {"status": "error", "message": "设备未连接"}

        return {
            "status": "success",
            "message": "调零完成",
            "baseline": {
                375: 0.000,
                405: 0.000,
                450: 0.000
            }
        }

    def measure_sample(self, concentration: float, solution_type: Optional[str] = None) -> Dict[str, float]:
        """
        测量单个样本（支持双溶液）

        Args:
            concentration: FHb浓度 (g/L)
            solution_type: 溶液类型（可选，如果不指定则使用当前设置的类型）

        Returns:
            三个波长的吸光度值
        """
        if not self.is_connected:
            raise ValueError("设备未连接，请先调用 connect()")

        # 如果指定了溶液类型，临时切换
        if solution_type and solution_type in SOLUTION_PARAMS:
            current = self.current_solution
            self.current_solution = SOLUTION_PARAMS[solution_type]
        else:
            current = self.current_solution

        if concentration < 0 or concentration > 6:
            raise ValueError("浓度超出测量范围 (0-6 g/L)")

        absorbance = {}

        for wavelength in self.wavelengths:
            cal = current['calibration'][wavelength]
            # 使用校准曲线计算吸光度
            theoretical_A = cal['slope'] * concentration + cal['intercept']

            # 添加高斯噪声（模拟测量误差）
            noise = np.random.normal(0, self.noise_level * theoretical_A)
            measured_A = max(0, theoretical_A + noise)

            absorbance[wavelength] = round(measured_A, 4)

        return absorbance

    def measure_sample_dual(self, concentration: float) -> Dict:
        """
        双溶液模式测量（返回详细信息）

        Args:
            concentration: FHb浓度 (g/L)

        Returns:
            包含吸光度和溶液信息的字典
        """
        absorbance = self.measure_sample(concentration)

        return {
            'absorbance': absorbance,
            'concentration': concentration,
            'solution_type': self.solution_type,
            'solution_name': self.current_solution['name'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def batch_measure(self, concentrations: List[float], solution_type: Optional[str] = None) -> pd.DataFrame:
        """
        批量测量样本

        Args:
            concentrations: 浓度列表
            solution_type: 溶液类型（可选）

        Returns:
            测量结果DataFrame
        """
        results = []

        for i, conc in enumerate(concentrations):
            try:
                absorbance = self.measure_sample(conc, solution_type)
                sol_info = self.current_solution
                results.append({
                    '样本编号': i + 1,
                    '浓度(g/L)': conc,
                    '375nm': absorbance[375],
                    '405nm': absorbance[405],
                    '450nm': absorbance[450],
                    '溶液类型': sol_info['name'],
                    '测量时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            except ValueError as e:
                print(f"样本 {i+1} 测量失败: {e}")

        return pd.DataFrame(results)

    def generate_dual_solution_data(self, n_samples: int = 20) -> Dict[str, pd.DataFrame]:
        """
        生成双溶液测试数据

        Args:
            n_samples: 每种溶液的样本数量

        Returns:
            包含两种溶液数据的字典
        """
        results = {}

        for sol_type, params in SOLUTION_PARAMS.items():
            # 设置溶液类型
            self.set_solution_type(sol_type)

            # 随机生成浓度
            conc_range = params['concentration_range']
            concentrations = np.random.uniform(conc_range[0], conc_range[1], n_samples)

            # 批量测量
            df = self.batch_measure(concentrations.tolist())
            results[sol_type] = df

        return results

    def generate_calibration_data(self,
                                  n_points: int = 10,
                                  concentration_range: Tuple[float, float] = (0, 0.3),
                                  solution_type: Optional[str] = None) -> pd.DataFrame:
        """
        生成校准数据

        Args:
            n_points: 校准点数
            concentration_range: 浓度范围
            solution_type: 溶液类型

        Returns:
            校准数据
        """
        if solution_type:
            self.set_solution_type(solution_type)

        concentrations = np.linspace(concentration_range[0], concentration_range[1], n_points)
        return self.batch_measure(concentrations.tolist())

    def generate_test_dataset(self,
                             n_samples: int = 50,
                             concentration_range: Tuple[float, float] = (0, 0.3),
                             solution_type: Optional[str] = None,
                             save_path: str = None) -> pd.DataFrame:
        """
        生成完整测试数据集

        Args:
            n_samples: 样本数量
            concentration_range: 浓度范围
            solution_type: 溶液类型
            save_path: 保存路径（可选）

        Returns:
            测试数据集
        """
        if solution_type:
            self.set_solution_type(solution_type)

        # 随机生成浓度（模拟实际检测场景）
        concentrations = np.random.uniform(
            concentration_range[0],
            concentration_range[1],
            n_samples
        )

        # 添加一些重复样本（模拟质控）
        n_qc = int(n_samples * 0.1)  # 10%质控样本
        qc_concentrations = [0.1, 0.2] * (n_qc // 2 + 1)
        qc_concentrations = qc_concentrations[:n_qc]

        all_concentrations = np.concatenate([concentrations, qc_concentrations])
        np.random.shuffle(all_concentrations)

        # 批量测量
        df = self.batch_measure(all_concentrations.tolist())

        # 添加样本类型
        df['样本类型'] = df['浓度(g/L)'].apply(
            lambda x: '质控样本' if round(x, 2) in [0.1, 0.2] else '待测样本'
        )

        # 保存
        if save_path:
            df.to_excel(save_path, index=False, encoding='utf-8-sig')
            print(f"测试数据集已保存: {save_path}")

        return df


class DualSolutionSimulator:
    """双溶液专用模拟器"""

    @staticmethod
    def get_solution_params() -> Dict:
        """获取所有溶液参数"""
        return {
            sol_type: {
                'name': params['name'],
                'description': params['description'],
                'concentration_range': params['concentration_range']
            }
            for sol_type, params in SOLUTION_PARAMS.items()
        }

    @staticmethod
    def generate_sample_data(solution_type: str, concentration: float, noise_level: float = 0.01) -> Dict:
        """
        为指定溶液生成样本数据

        Args:
            solution_type: 溶液类型
            concentration: 浓度
            noise_level: 噪声水平

        Returns:
            样本数据
        """
        if solution_type not in SOLUTION_PARAMS:
            raise ValueError(f"未知的溶液类型: {solution_type}")

        params = SOLUTION_PARAMS[solution_type]

        absorbance = {}
        for wavelength in [375, 405, 450]:
            cal = params['calibration'][wavelength]
            theoretical_A = cal['slope'] * concentration + cal['intercept']
            noise = np.random.normal(0, noise_level * theoretical_A)
            measured_A = max(0, theoretical_A + noise)
            absorbance[f'a{wavelength}'] = round(measured_A, 4)

        return {
            'a375': absorbance['a375'],
            'a405': absorbance['a405'],
            'a450': absorbance['a450'],
            'concentration': concentration,
            'solution_type': solution_type,
            'solution_name': params['name'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    @staticmethod
    def generate_batch_data(solution_type: str, n_samples: int = 10, noise_level: float = 0.01) -> List[Dict]:
        """
        生成批量样本数据

        Args:
            solution_type: 溶液类型
            n_samples: 样本数量
            noise_level: 噪声水平

        Returns:
            样本数据列表
        """
        if solution_type not in SOLUTION_PARAMS:
            raise ValueError(f"未知的溶液类型: {solution_type}")

        params = SOLUTION_PARAMS[solution_type]
        conc_range = params['concentration_range']
        concentrations = np.random.uniform(conc_range[0], conc_range[1], n_samples)

        return [
            DualSolutionSimulator.generate_sample_data(solution_type, conc, noise_level)
            for conc in concentrations
        ]


class SpectralDataGenerator:
    """光谱数据生成器 - 用于前端演示"""

    @staticmethod
    def generate_spectrum(concentration: float,
                         wavelength_range: Tuple[int, int] = (350, 500),
                         resolution: int = 1) -> pd.DataFrame:
        """
        生成连续光谱数据（用于绘图）

        Args:
            concentration: 浓度
            wavelength_range: 波长范围
            resolution: 波长间隔（nm）

        Returns:
            光谱数据
        """
        wavelengths = np.arange(wavelength_range[0], wavelength_range[1] + 1, resolution)

        # 模拟FHb吸收光谱（高斯峰形）
        absorbance = []
        for wl in wavelengths:
            # 主峰在405nm（Soret带）
            peak1 = 1.25 * np.exp(-((wl - 405) ** 2) / (2 * 15 ** 2))

            # 次峰在375nm
            peak2 = 0.85 * np.exp(-((wl - 375) ** 2) / (2 * 12 ** 2))

            # 基线吸收
            baseline = 0.1 * (concentration / 0.3)

            A = (peak1 + peak2 + baseline) * concentration
            A = max(0, A + np.random.normal(0, 0.005))  # 添加噪声
            absorbance.append(round(A, 4))

        return pd.DataFrame({
            '波长(nm)': wavelengths,
            '吸光度': absorbance
        })

    @staticmethod
    def generate_time_series(concentration: float,
                            duration_minutes: int = 10,
                            interval_seconds: int = 30,
                            solution_type: str = 'solution_a') -> pd.DataFrame:
        """
        生成时间序列数据（模拟稳定性测试）

        Args:
            concentration: 浓度
            duration_minutes: 测量时长
            interval_seconds: 测量间隔
            solution_type: 溶液类型

        Returns:
            时间序列数据
        """
        n_points = int(duration_minutes * 60 / interval_seconds)
        timestamps = pd.date_range(
            start=datetime.now(),
            periods=n_points,
            freq=f'{interval_seconds}S'
        )

        simulator = SpectrometerSimulator(noise_level=0.008, solution_type=solution_type)
        simulator.connect()

        data = []
        for ts in timestamps:
            absorbance = simulator.measure_sample(concentration)
            data.append({
                '时间': ts.strftime('%H:%M:%S'),
                '375nm': absorbance[375],
                '405nm': absorbance[405],
                '450nm': absorbance[450],
                '溶液类型': simulator.current_solution['name']
            })

        return pd.DataFrame(data)


def main():
    """测试模拟器功能"""
    print("=" * 60)
    print("血浆游离血红蛋白检测系统 - 光谱仪模拟器测试（双溶液版）")
    print("作者: 哈雷酱大小姐 (￣▽￣)／")
    print("=" * 60)

    # 测试双溶液模拟器
    print("\n[1] 测试双溶液模拟器...")
    solutions = DualSolutionSimulator.get_solution_params()
    print(f"    可用溶液: {list(solutions.keys())}")
    for sol_type, info in solutions.items():
        print(f"    - {sol_type}: {info['name']}")
        print(f"      浓度范围: {info['concentration_range']}")

    # 测试溶液A
    print("\n[2] 测试溶液A模拟...")
    sol_a_data = DualSolutionSimulator.generate_sample_data('solution_a', 0.15)
    print(f"    浓度: {sol_a_data['concentration']} g/L")
    print(f"    吸光度: A375={sol_a_data['a375']}, A405={sol_a_data['a405']}, A450={sol_a_data['a450']}")

    # 测试溶液B
    print("\n[3] 测试溶液B模拟...")
    sol_b_data = DualSolutionSimulator.generate_sample_data('solution_b', 0.1)
    print(f"    浓度: {sol_b_data['concentration']} g/L")
    print(f"    吸光度: A375={sol_b_data['a375']}, A405={sol_b_data['a405']}, A450={sol_b_data['a450']}")

    # 测试批量生成
    print("\n[4] 测试批量数据生成...")
    batch_a = DualSolutionSimulator.generate_batch_data('solution_a', 5)
    print(f"    溶液A批量数据: {len(batch_a)} 样本")
    batch_b = DualSolutionSimulator.generate_batch_data('solution_b', 5)
    print(f"    溶液B批量数据: {len(batch_b)} 样本")

    print("\n" + "=" * 60)
    print("双溶液模拟器测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
