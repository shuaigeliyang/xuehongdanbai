"""
血浆游离血红蛋白检测系统 - 双溶液类型数据预处理模块
作者: 哈雷酱大小姐 (￣▽￣)／
功能: 分别处理两种不同溶液的实验数据
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
import sys
import io
import pickle
import json
from pathlib import Path
from datetime import datetime

warnings.filterwarnings('ignore')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class DualSolutionDataProcessor:
    """双溶液数据处理器 - 分别处理两种不同溶液"""

    def __init__(self):
        self.solution_configs = {
            'solution_a': {
                'name': '溶液A',
                'file': '实验记录-20250731.xlsx',
                'description': '2025年7月31日测量的标准溶液',
                'concentration_col': '溶液浓度g/L'
            },
            'solution_b': {
                'name': '溶液B',
                'file': '实验记录-20250812.xlsx',
                'description': '2025年8月12日测量的实验溶液',
                'concentration_col': '实验浓度g/L'
            }
        }
        self.processors = {}
        self.summaries = {}

    def process_single_solution(self, solution_key: str):
        """处理单个溶液的数据"""
        config = self.solution_configs[solution_key]
        print(f"\n{'='*70}")
        print(f"处理 {config['name']} 数据")
        print(f"{'='*70}")
        print(f"文件: {config['file']}")
        print(f"描述: {config['description']}")

        # 读取数据
        df = pd.read_excel(config['file'])

        # 标准化列名
        df.columns = ['编号', '浓度g/L', '375nm', '405nm', '450nm']

        # 提取浓度值
        df['浓度值'] = pd.to_numeric(df['浓度g/L'], errors='coerce')
        df['浓度值'] = df['浓度值'].ffill()

        # 移除无效行
        df = df.dropna(subset=['375nm', '405nm', '450nm', '浓度值'])
        df_valid = df[['浓度值', '375nm', '405nm', '450nm']].copy()

        print(f"\n[1] 数据加载:")
        print(f"    有效样本数: {len(df_valid)}")

        # 异常值处理
        print(f"\n[2] 异常值检测:")
        for col in ['375nm', '405nm', '450nm']:
            Q1 = df_valid[col].quantile(0.25)
            Q3 = df_valid[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            outliers = ((df_valid[col] < lower) | (df_valid[col] > upper)).sum()
            print(f"    {col}: {outliers} 个异常值")
            df_valid = df_valid[(df_valid[col] >= lower) & (df_valid[col] <= upper)]

        # 浓度范围过滤
        df_valid = df_valid[(df_valid['浓度值'] >= 0) & (df_valid['浓度值'] <= 6)]

        print(f"\n[3] 清洗后样本数: {len(df_valid)}")

        # 特征工程
        df_valid['A405_A375'] = df_valid['405nm'] / (df_valid['375nm'] + 0.001)
        df_valid['A450_A405'] = df_valid['450nm'] / (df_valid['405nm'] + 0.001)
        df_valid['A450_A375'] = df_valid['450nm'] / (df_valid['375nm'] + 0.001)
        df_valid['A405_minus_A375'] = df_valid['405nm'] - df_valid['375nm']
        df_valid['A450_minus_A405'] = df_valid['450nm'] - df_valid['405nm']
        df_valid['A_sum'] = df_valid['375nm'] + df_valid['405nm'] + df_valid['450nm']

        feature_cols = ['375nm', '405nm', '450nm',
                       'A405_A375', 'A450_A405', 'A450_A375',
                       'A405_minus_A375', 'A450_minus_A405', 'A_sum']

        X = df_valid[feature_cols].values
        y = df_valid['浓度值'].values

        # 划分训练测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # 标准化
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # 保存数据
        self.processors[solution_key] = {
            'data': df_valid,
            'X_train': X_train_scaled,
            'X_test': X_test_scaled,
            'y_train': y_train,
            'y_test': y_test,
            'scaler': scaler,
            'feature_cols': feature_cols
        }

        # 统计摘要
        summary = {
            'name': config['name'],
            'description': config['description'],
            'total_samples': len(df_valid),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'concentration_range': (float(y.min()), float(y.max())),
            'concentration_mean': float(y.mean()),
            'wavelengths': {
                '375nm': {
                    'mean': float(df_valid['375nm'].mean()),
                    'std': float(df_valid['375nm'].std())
                },
                '405nm': {
                    'mean': float(df_valid['405nm'].mean()),
                    'std': float(df_valid['405nm'].std())
                },
                '450nm': {
                    'mean': float(df_valid['450nm'].mean()),
                    'std': float(df_valid['450nm'].std())
                }
            }
        }

        self.summaries[solution_key] = summary

        print(f"\n[4] 数据统计:")
        print(f"    浓度范围: {summary['concentration_range'][0]:.4f} - {summary['concentration_range'][1]:.4f} g/L")
        print(f"    浓度均值: {summary['concentration_mean']:.4f} g/L")
        print(f"    训练集: {len(X_train)} 样本")
        print(f"    测试集: {len(X_test)} 样本")

        print(f"\n[OK] {config['name']} 数据处理完成！")

        return summary

    def process_all_solutions(self):
        """处理所有溶液数据"""
        print("\n" + "="*70)
        print("   双溶液数据预处理系统")
        print("   作者: 哈雷酱大小姐 (￣▽￣)／")
        print("="*70)

        for solution_key in self.solution_configs.keys():
            self.process_single_solution(solution_key)

        # 对比分析
        self.compare_solutions()

        # 保存处理结果
        self.save_processed_data()

        # 生成对比报告
        self.generate_comparison_report()

        print(f"\n{'='*70}")
        print("[OK] 所有溶液数据处理完成！")
        print(f"{'='*70}")

        return self.summaries

    def compare_solutions(self):
        """对比分析两种溶液"""
        print(f"\n{'='*70}")
        print("溶液对比分析")
        print(f"{'='*70}")

        sum_a = self.summaries['solution_a']
        sum_b = self.summaries['solution_b']

        print(f"\n{'指标':<20} {'溶液A':<20} {'溶液B':<20}")
        print("-"*60)
        print(f"{'样本数':<20} {sum_a['total_samples']:<20} {sum_b['total_samples']:<20}")
        print(f"{'浓度范围':<20} {str(sum_a['concentration_range']):<20} {str(sum_b['concentration_range']):<20}")
        print(f"{'浓度均值':<20} {sum_a['concentration_mean']:.4f} {'':>12} {sum_b['concentration_mean']:.4f}")

        print(f"\n吸光度对比:")
        for wl in ['375nm', '405nm', '450nm']:
            mean_a = sum_a['wavelengths'][wl]['mean']
            mean_b = sum_b['wavelengths'][wl]['mean']
            print(f"  {wl}: 溶液A={mean_a:.4f}, 溶液B={mean_b:.4f}, 差异={abs(mean_a-mean_b):.4f}")

    def save_processed_data(self):
        """保存处理后的数据"""
        output_dir = Path('processed_data')
        output_dir.mkdir(exist_ok=True)

        for solution_key, processor in self.processors.items():
            config = self.solution_configs[solution_key]

            # 保存数据集
            data_file = output_dir / f"{solution_key}_processed.csv"
            processor['data'].to_csv(data_file, index=False, encoding='utf-8-sig')
            print(f"\n[OK] 数据已保存: {data_file}")

            # 保存标准化器
            scaler_file = output_dir / f"{solution_key}_scaler.pkl"
            with open(scaler_file, 'wb') as f:
                pickle.dump(processor['scaler'], f)
            print(f"[OK] 标准化器已保存: {scaler_file}")

    def generate_comparison_report(self):
        """生成对比报告"""
        report = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'solutions': self.summaries
        }

        report_file = Path('processed_data') / 'comparison_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] 对比报告已保存: {report_file}")

    def get_training_data(self, solution_key: str):
        """获取指定溶液的训练数据"""
        if solution_key not in self.processors:
            raise ValueError(f"未知的溶液类型: {solution_key}")

        processor = self.processors[solution_key]
        return (
            processor['X_train'],
            processor['X_test'],
            processor['y_train'],
            processor['y_test'],
            processor['scaler'],
            processor['feature_cols']
        )


def main():
    """主函数"""
    processor = DualSolutionDataProcessor()
    summaries = processor.process_all_solutions()

    print("\n" + "="*70)
    print("数据预处理完成！")
    print("="*70)
    print("\n下一步: 运行模型训练脚本")
    print("  python 双溶液模型训练脚本.py")

    return processor


if __name__ == "__main__":
    processor = main()
