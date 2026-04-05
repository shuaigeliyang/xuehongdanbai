"""
血浆游离血红蛋白检测系统 - 光谱仪模拟器
作者: 哈雷酱大小姐 (￣▽￣)／
功能: 模拟三波长光谱检测仪，生成测试数据
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import json
from datetime import datetime


class SpectrometerSimulator:
    """光谱仪模拟器 - 基于朗伯-比尔定律"""

    def __init__(self, noise_level: float = 0.01):
        """
        初始化模拟器

        Args:
            noise_level: 测量噪声水平（标准差）
        """
        self.noise_level = noise_level

        # 三波长摩尔吸光系数（基于FHb特性）
        self.wavelengths = [375, 405, 450]
        self.epsilon = {
            375: 0.85,  # 紫外区
            405: 1.25,  # Soret带（特征峰）
            450: 0.65   # 可见区
        }

        # 仪器参数
        self.path_length = 1.0  # 光程（cm）
        self.is_connected = False
        self.last_calibration_date = None

    def connect(self) -> Dict[str, str]:
        """模拟连接设备"""
        self.is_connected = True
        return {
            "status": "success",
            "message": "光谱仪模拟器已启动",
            "device_info": {
                "model": "Simulated Spectrometer V1.0",
                "wavelengths": self.wavelengths,
                "manufacturer": "哈雷酱科技 (￣▽￣)／",
                "serial_number": f"SIMP-{datetime.now().strftime('%Y%m%d')}"
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

    def measure_sample(self, concentration: float) -> Dict[str, float]:
        """
        测量单个样本

        Args:
            concentration: FHb浓度 (g/L)

        Returns:
            三个波长的吸光度值
        """
        if not self.is_connected:
            raise ValueError("设备未连接，请先调用 connect()")

        if concentration < 0 or concentration > 6:
            raise ValueError("浓度超出测量范围 (0-6 g/L)")

        absorbance = {}

        for wavelength in self.wavelengths:
            # 朗伯-比尔定律: A = ε × c × l
            theoretical_A = self.epsilon[wavelength] * concentration * self.path_length

            # 添加高斯噪声（模拟测量误差）
            noise = np.random.normal(0, self.noise_level)
            measured_A = max(0, theoretical_A + noise)

            absorbance[wavelength] = round(measured_A, 4)

        return absorbance

    def batch_measure(self, concentrations: List[float]) -> pd.DataFrame:
        """
        批量测量样本

        Args:
            concentrations: 浓度列表

        Returns:
            测量结果DataFrame
        """
        results = []

        for i, conc in enumerate(concentrations):
            try:
                absorbance = self.measure_sample(conc)
                results.append({
                    '样本编号': i + 1,
                    '浓度(g/L)': conc,
                    '375nm': absorbance[375],
                    '405nm': absorbance[405],
                    '450nm': absorbance[450],
                    '测量时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            except ValueError as e:
                print(f"样本 {i+1} 测量失败: {e}")

        return pd.DataFrame(results)

    def generate_calibration_data(self,
                                  n_points: int = 10,
                                  concentration_range: Tuple[float, float] = (0, 0.5)) -> pd.DataFrame:
        """
        生成校准数据

        Args:
            n_points: 校准点数
            concentration_range: 浓度范围

        Returns:
            校准数据
        """
        concentrations = np.linspace(concentration_range[0], concentration_range[1], n_points)
        return self.batch_measure(concentrations.tolist())

    def generate_test_dataset(self,
                             n_samples: int = 50,
                             concentration_range: Tuple[float, float] = (0, 0.3),
                             save_path: str = None) -> pd.DataFrame:
        """
        生成完整测试数据集

        Args:
            n_samples: 样本数量
            concentration_range: 浓度范围
            save_path: 保存路径（可选）

        Returns:
            测试数据集
        """
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
            lambda x: '质控样本' if x in [0.1, 0.2] else '待测样本'
        )

        # 保存
        if save_path:
            df.to_excel(save_path, index=False, encoding='utf-8-sig')
            print(f"测试数据集已保存: {save_path}")

        return df


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
                            interval_seconds: int = 30) -> pd.DataFrame:
        """
        生成时间序列数据（模拟稳定性测试）

        Args:
            concentration: 浓度
            duration_minutes: 测量时长
            interval_seconds: 测量间隔

        Returns:
            时间序列数据
        """
        n_points = int(duration_minutes * 60 / interval_seconds)
        timestamps = pd.date_range(
            start=datetime.now(),
            periods=n_points,
            freq=f'{interval_seconds}S'
        )

        simulator = SpectrometerSimulator(noise_level=0.008)
        simulator.connect()

        data = []
        for ts in timestamps:
            absorbance = simulator.measure_sample(concentration)
            data.append({
                '时间': ts.strftime('%H:%M:%S'),
                '375nm': absorbance[375],
                '405nm': absorbance[405],
                '450nm': absorbance[450]
            })

        return pd.DataFrame(data)


def main():
    """测试模拟器功能"""
    print("=" * 60)
    print("血浆游离血红蛋白检测系统 - 光谱仪模拟器测试")
    print("作者: 哈雷酱大小姐 (￣▽￣)／")
    print("=" * 60)

    # 创建模拟器
    sim = SpectrometerSimulator(noise_level=0.01)

    # 连接设备
    print("\n[1] 连接设备...")
    result = sim.connect()
    print(f"    {result['message']}")
    print(f"    设备信息: {result['device_info']}")

    # 自动调零
    print("\n[2] 自动调零...")
    result = sim.auto_zero()
    print(f"    {result['message']}")

    # 单次测量
    print("\n[3] 单次测量测试...")
    concentration = 0.15
    absorbance = sim.measure_sample(concentration)
    print(f"    浓度: {concentration} g/L")
    print(f"    吸光度: {absorbance}")

    # 批量测量
    print("\n[4] 批量测量测试...")
    concentrations = [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
    batch_df = sim.batch_measure(concentrations)
    print(f"    测量样本数: {len(batch_df)}")
    print("\n    测量结果:")
    print(batch_df.to_string(index=False))

    # 生成测试数据集
    print("\n[5] 生成完整测试数据集...")
    test_df = sim.generate_test_dataset(
        n_samples=30,
        concentration_range=(0, 0.3),
        save_path='data/测试数据集_模拟.xlsx'
    )
    print(f"    生成样本数: {len(test_df)}")
    print(f"    浓度范围: {test_df['浓度(g/L)'].min():.3f} - {test_df['浓度(g/L)'].max():.3f} g/L")

    # 生成光谱数据
    print("\n[6] 生成连续光谱数据...")
    spectrum_df = SpectralDataGenerator.generate_spectrum(0.15)
    spectrum_df.to_csv('data/光谱数据_示例.csv', index=False, encoding='utf-8-sig')
    print(f"    光谱数据点数: {len(spectrum_df)}")
    print(f"    最大吸光度: {spectrum_df['吸光度'].max():.4f} (波长: {spectrum_df.loc[spectrum_df['吸光度'].idxmax(), '波长(nm)']} nm)")

    print("\n" + "=" * 60)
    print("模拟器测试完成！所有数据已保存到 data/ 目录")
    print("=" * 60)


if __name__ == "__main__":
    main()
