"""
血浆游离血红蛋白检测系统 - 数据预处理与分析模块
作者: 哈雷酱大小姐
功能: 数据清洗、探索性分析和特征工程
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import warnings
import sys
import io
warnings.filterwarnings('ignore')

# 设置输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class FHbDataProcessor:
    """血浆游离血红蛋白数据处理器"""

    def __init__(self):
        self.raw_data = None
        self.cleaned_data = None
        self.features = None
        self.targets = None
        self.scaler = StandardScaler()

    def load_data(self, file_paths):
        """加载多个Excel数据集"""
        print("=" * 60)
        print("[数据加载阶段]")
        print("=" * 60)

        all_data = []

        for i, file_path in enumerate(file_paths, 1):
            print(f"\n[{i}] 正在读取: {file_path}")
            df = pd.read_excel(file_path)

            # 标准化列名
            df.columns = ['编号', '浓度g/L', '375nm', '405nm', '450nm']

            # 提取浓度值(处理"空白"、"对照"等文本)
            df['浓度值'] = pd.to_numeric(df['浓度g/L'], errors='coerce')

            # 前向填充浓度值(同一组重复测量使用相同浓度)
            df['浓度值'] = df['浓度值'].fillna(method='ffill')

            # 移除完全无效的行
            df = df.dropna(subset=['375nm', '405nm', '450nm', '浓度值'])

            # 保留有效列
            df_valid = df[['浓度值', '375nm', '405nm', '450nm']].copy()
            df_valid = df_valid.dropna()

            print(f"    [OK] 有效样本数: {len(df_valid)}")
            print(f"    [OK] 浓度范围: {df_valid['浓度值'].min():.4f} - {df_valid['浓度值'].max():.4f} g/L")

            all_data.append(df_valid)

        # 合并所有数据
        self.raw_data = pd.concat(all_data, ignore_index=True)
        print(f"\n{'='*60}")
        print(f"[OK] 数据加载完成！总计 {len(self.raw_data)} 个样本")
        print(f"{'='*60}")

        return self.raw_data

    def clean_data(self):
        """数据清洗"""
        print("\n" + "=" * 60)
        print("[数据清洗阶段]")
        print("=" * 60)

        df = self.raw_data.copy()

        # 移除异常值(使用IQR方法)
        print("\n[1] 异常值检测与处理:")
        for col in ['375nm', '405nm', '450nm']:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR

            outliers = ((df[col] < lower) | (df[col] > upper)).sum()
            print(f"    {col}: 发现 {outliers} 个异常值")

            # 移除异常值
            df = df[(df[col] >= lower) & (df[col] <= upper)]

        # 移除浓度异常值
        df = df[(df['浓度值'] >= 0) & (df['浓度值'] <= 6)]

        print(f"\n[OK] 清洗后样本数: {len(df)}")

        # 检查缺失值
        missing = df.isnull().sum()
        if missing.sum() > 0:
            print(f"\n[2] 缺失值处理:")
            for col, count in missing.items():
                if count > 0:
                    print(f"    {col}: {count} 个缺失值")
                    # 使用均值填充
                    df[col].fillna(df[col].mean(), inplace=True)
        else:
            print("\n[2] 无缺失值 [OK]")

        self.cleaned_data = df
        print(f"\n{'='*60}")
        print("[OK] 数据清洗完成！")
        print(f"{'='*60}")

        return self.cleaned_data

    def feature_engineering(self):
        """特征工程"""
        print("\n" + "=" * 60)
        print("[特征工程阶段]")
        print("=" * 60)

        df = self.cleaned_data.copy()

        # 基础特征:三个波长吸光度
        X = df[['375nm', '405nm', '450nm']].values
        y = df['浓度值'].values

        print("\n[1] 基础特征:")
        print("    [OK] 375nm吸光度")
        print("    [OK] 405nm吸光度")
        print("    [OK] 450nm吸光度")

        # 创建组合特征
        print("\n[2] 创建组合特征:")

        # 吸光度比值(基于朗伯-比尔定律)
        df['A405_A375'] = df['405nm'] / (df['375nm'] + 0.001)  # 避免除零
        df['A450_A405'] = df['450nm'] / (df['405nm'] + 0.001)
        df['A450_A375'] = df['450nm'] / (df['375nm'] + 0.001)
        print("    [OK] 吸光度比值特征 (A405/A375, A450/A405, A450/A375)")

        # 吸光度差值
        df['A405_minus_A375'] = df['405nm'] - df['375nm']
        df['A450_minus_A405'] = df['450nm'] - df['405nm']
        print("    [OK] 吸光度差值特征 (ΔA405-375, ΔA450-405)")

        # 吸光度总和
        df['A_sum'] = df['375nm'] + df['405nm'] + df['450nm']
        print("    [OK] 吸光度总和特征")

        # 扩展特征矩阵
        feature_cols = ['375nm', '405nm', '450nm',
                       'A405_A375', 'A450_A405', 'A450_A375',
                       'A405_minus_A375', 'A450_minus_A405', 'A_sum']

        X_extended = df[feature_cols].values

        print(f"\n[3] 特征统计:")
        print(f"    原始特征数: 3")
        print(f"    扩展特征数: {len(feature_cols)}")
        print(f"    样本数: {len(df)}")

        self.features = X_extended
        self.targets = y
        self.feature_names = feature_cols
        self.feature_data = df

        print(f"\n{'='*60}")
        print("[OK] 特征工程完成！")
        print(f"{'='*60}")

        return X_extended, y, feature_cols

    def exploratory_analysis(self):
        """探索性数据分析"""
        print("\n" + "=" * 60)
        print("[探索性数据分析]")
        print("=" * 60)

        df = self.feature_data

        # 创建可视化
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('血浆游离血红蛋白数据分析', fontsize=16, fontweight='bold')

        # 1. 浓度分布
        axes[0, 0].hist(df['浓度值'], bins=20, color='skyblue', edgecolor='black')
        axes[0, 0].set_title('浓度分布', fontweight='bold')
        axes[0, 0].set_xlabel('浓度 (g/L)')
        axes[0, 0].set_ylabel('频数')
        axes[0, 0].grid(True, alpha=0.3)

        # 2. 波长与浓度的关系
        wavelengths = ['375nm', '405nm', '450nm']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        for idx, (wl, color) in enumerate(zip(wavelengths, colors)):
            axes[0, 1].scatter(df[wl], df['浓度值'], alpha=0.6, color=color, label=wl)
        axes[0, 1].set_title('吸光度 vs 浓度', fontweight='bold')
        axes[0, 1].set_xlabel('吸光度')
        axes[0, 1].set_ylabel('浓度 (g/L)')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # 3. 波长相关性热图
        corr_matrix = df[wavelengths].corr()
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                    ax=axes[0, 2], cbar_kws={'label': '相关系数'})
        axes[0, 2].set_title('波长相关性矩阵', fontweight='bold')

        # 4-6. 各波长与浓度的散点图
        for idx, (wl, color) in enumerate(zip(wavelengths, colors)):
            axes[1, idx].scatter(df[wl], df['浓度值'], alpha=0.6, color=color)
            axes[1, idx].set_title(f'{wl} vs 浓度', fontweight='bold')
            axes[1, idx].set_xlabel(f'{wl} 吸光度')
            axes[1, idx].set_ylabel('浓度 (g/L)')

            # 添加趋势线
            z = np.polyfit(df[wl], df['浓度值'], 2)
            p = np.poly1d(z)
            x_line = np.linspace(df[wl].min(), df[wl].max(), 100)
            axes[1, idx].plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2)
            axes[1, idx].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('01_数据分析报告.png', dpi=300, bbox_inches='tight')
        print("\n[OK] 可视化报告已保存: 01_数据分析报告.png")

        # 打印统计信息
        print(f"\n{'='*60}")
        print("[数据统计摘要]")
        print(f"{'='*60}")
        print(f"\n[浓度统计]")
        print(f"  均值: {df['浓度值'].mean():.4f} g/L")
        print(f"  标准差: {df['浓度值'].std():.4f} g/L")
        print(f"  最小值: {df['浓度值'].min():.4f} g/L")
        print(f"  最大值: {df['浓度值'].max():.4f} g/L")

        print(f"\n[吸光度统计]")
        for wl in wavelengths:
            print(f"  {wl}: 均值={df[wl].mean():.4f}, 标准差={df[wl].std():.4f}")

        print(f"\n{'='*60}")
        print("[OK] 探索性分析完成！")
        print(f"{'='*60}")

        return fig

    def save_processed_data(self, output_file='processed_data.csv'):
        """保存处理后的数据"""
        if self.feature_data is not None:
            self.feature_data.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\n[OK] 处理后的数据已保存: {output_file}")
        else:
            print("\n[WARNING] 没有可保存的数据")

    def get_train_test_data(self, test_size=0.2, random_state=42):
        """获取训练和测试数据"""
        from sklearn.model_selection import train_test_split

        if self.features is None or self.targets is None:
            raise ValueError("请先运行 feature_engineering() 方法")

        X_train, X_test, y_train, y_test = train_test_split(
            self.features, self.targets,
            test_size=test_size,
            random_state=random_state
        )

        print(f"\n{'='*60}")
        print("[数据集划分]")
        print(f"{'='*60}")
        print(f"训练集: {len(X_train)} 样本 ({(1-test_size)*100:.0f}%)")
        print(f"测试集: {len(X_test)} 样本 ({test_size*100:.0f}%)")
        print(f"{'='*60}")

        return X_train, X_test, y_train, y_test


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("   血浆游离血红蛋白检测系统 - 数据预处理模块")
    print("   作者: 哈雷酱大小姐")
    print("=" * 60 + "\n")

    # 初始化数据处理器
    processor = FHbDataProcessor()

    # 加载数据
    file_paths = [
        '实验记录-20250731.xlsx',
        '实验记录-20250812.xlsx'
    ]
    processor.load_data(file_paths)

    # 数据清洗
    processor.clean_data()

    # 特征工程
    processor.feature_engineering()

    # 探索性分析
    processor.exploratory_analysis()

    # 保存处理后的数据
    processor.save_processed_data()

    # 获取训练/测试集
    X_train, X_test, y_train, y_test = processor.get_train_test_data()

    print("\n" + "=" * 60)
    print("   数据预处理阶段完成！准备进入模型训练...")
    print("=" * 60 + "\n")

    return processor, X_train, X_test, y_train, y_test


if __name__ == "__main__":
    processor, X_train, X_test, y_train, y_test = main()
