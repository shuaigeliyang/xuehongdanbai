"""
血浆游离血红蛋白检测系统 - 双溶液模型训练脚本
作者: 哈雷酱大小姐 (￣▽￣)／
功能: 为两种不同溶液分别训练独立的ML模型
"""

import numpy as np
import pandas as pd
import pickle
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings

warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class DualSolutionModelTrainer:
    """双溶液模型训练器 - 为每种溶液训练独立模型"""

    def __init__(self, data_processor):
        """
        初始化训练器

        Args:
            data_processor: DualSolutionDataProcessor实例
        """
        self.processor = data_processor
        self.models = {}
        self.results = {}

    def train_solution_models(self, solution_key: str):
        """为指定溶液训练模型"""
        from 双溶液数据预处理脚本 import DualSolutionDataProcessor

        config = self.processor.solution_configs[solution_key]
        print(f"\n{'='*70}")
        print(f"训练 {config['name']} 的模型")
        print(f"{'='*70}")

        # 获取训练数据
        X_train, X_test, y_train, y_test, scaler, feature_cols = \
            self.processor.get_training_data(solution_key)

        print(f"\n[1] 数据准备:")
        print(f"    训练集: {X_train.shape}")
        print(f"    测试集: {X_test.shape}")
        print(f"    特征数: {len(feature_cols)}")

        # 训练随机森林
        print(f"\n[2] 训练随机森林模型...")
        rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train, y_train)

        # 评估随机森林
        y_pred_rf = rf_model.predict(X_test)
        rf_metrics = self.calculate_metrics(y_test, y_pred_rf, X_train, y_train, rf_model)

        print(f"    训练集 R²: {rf_metrics['train_r2']:.4f}")
        print(f"    测试集 R²: {rf_metrics['test_r2']:.4f}")
        print(f"    测试集 MAE: {rf_metrics['test_mae']:.4f} g/L")

        # 训练SVR
        print(f"\n[3] 训练SVR模型...")
        svr_model = SVR(
            kernel='rbf',
            C=100,
            gamma='scale',
            epsilon=0.001
        )
        svr_model.fit(X_train, y_train)

        # 评估SVR
        y_pred_svr = svr_model.predict(X_test)
        svr_metrics = self.calculate_metrics(y_test, y_pred_svr, X_train, y_train, svr_model)

        print(f"    训练集 R²: {svr_metrics['train_r2']:.4f}")
        print(f"    测试集 R²: {svr_metrics['test_r2']:.4f}")
        print(f"    测试集 MAE: {svr_metrics['test_mae']:.4f} g/L")

        # 交叉验证
        print(f"\n[4] 5折交叉验证...")
        rf_cv_scores = cross_val_score(rf_model, X_train, y_train, cv=5, scoring='r2')
        svr_cv_scores = cross_val_score(svr_model, X_train, y_train, cv=5, scoring='r2')

        print(f"    RandomForest CV-R²: {rf_cv_scores.mean():.4f} (±{rf_cv_scores.std():.4f})")
        print(f"    SVR CV-R²: {svr_cv_scores.mean():.4f} (±{svr_cv_scores.std():.4f})")

        # 选择最佳模型
        best_model_type = 'rf' if rf_metrics['test_r2'] > svr_metrics['test_r2'] else 'svr'
        best_model = rf_model if best_model_type == 'rf' else svr_model
        best_metrics = rf_metrics if best_model_type == 'rf' else svr_metrics

        print(f"\n[5] 最佳模型: {best_model_type.upper()}")

        # 保存结果
        self.models[solution_key] = {
            'rf_model': rf_model,
            'svr_model': svr_model,
            'best_model_type': best_model_type,
            'best_model': best_model,
            'scaler': scaler,
            'feature_cols': feature_cols,
            'solution_name': config['name']
        }

        self.results[solution_key] = {
            'solution_name': config['name'],
            'rf_metrics': rf_metrics,
            'svr_metrics': svr_metrics,
            'rf_cv': {
                'mean': float(rf_cv_scores.mean()),
                'std': float(rf_cv_scores.std())
            },
            'svr_cv': {
                'mean': float(svr_cv_scores.mean()),
                'std': float(svr_cv_scores.std())
            },
            'best_model_type': best_model_type,
            'best_metrics': best_metrics
        }

        # 生成可视化
        self.generate_solution_plots(solution_key, y_test, y_pred_rf, y_pred_svr)

        print(f"\n[OK] {config['name']} 模型训练完成！")

        return self.results[solution_key]

    def calculate_metrics(self, y_true, y_pred, X_train, y_train, model):
        """计算模型性能指标"""
        train_pred = model.predict(X_train)

        return {
            'train_r2': r2_score(y_train, train_pred),
            'test_r2': r2_score(y_true, y_pred),
            'test_mae': mean_absolute_error(y_true, y_pred),
            'test_mse': mean_squared_error(y_true, y_pred),
            'test_rmse': np.sqrt(mean_squared_error(y_true, y_pred))
        }

    def generate_solution_plots(self, solution_key, y_true, y_pred_rf, y_pred_svr):
        """为单个溶液生成可视化"""
        output_dir = Path('model_results')
        output_dir.mkdir(exist_ok=True)

        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        solution_name = self.processor.solution_configs[solution_key]['name']

        fig.suptitle(f'{solution_name} - 模型性能对比', fontsize=16, fontweight='bold')

        # RandomForest 预测 vs 实际
        axes[0].scatter(y_true, y_pred_rf, alpha=0.6, color='#4ECDC4')
        axes[0].plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
        axes[0].set_xlabel('实际浓度 (g/L)')
        axes[0].set_ylabel('预测浓度 (g/L)')
        axes[0].set_title('Random Forest', fontweight='bold')
        axes[0].grid(True, alpha=0.3)

        # SVR 预测 vs 实际
        axes[1].scatter(y_true, y_pred_svr, alpha=0.6, color='#FF6B6B')
        axes[1].plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
        axes[1].set_xlabel('实际浓度 (g/L)')
        axes[1].set_ylabel('预测浓度 (g/L)')
        axes[1].set_title('SVR', fontweight='bold')
        axes[1].grid(True, alpha=0.3)

        # 残差对比
        residuals_rf = y_pred_rf - y_true
        residuals_svr = y_pred_svr - y_true
        axes[2].hist(residuals_rf, bins=10, alpha=0.5, label='RandomForest', color='#4ECDC4')
        axes[2].hist(residuals_svr, bins=10, alpha=0.5, label='SVR', color='#FF6B6B')
        axes[2].set_xlabel('残差')
        axes[2].set_ylabel('频数')
        axes[2].set_title('残差分布', fontweight='bold')
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)

        plt.tight_layout()
        plot_file = output_dir / f"{solution_key}_performance.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[OK] 可视化已保存: {plot_file}")

    def train_all_solutions(self):
        """训练所有溶液的模型"""
        print("\n" + "="*70)
        print("   双溶液模型训练系统")
        print("   作者: 哈雷酱大小姐 (￣▽￣)／")
        print("="*70)

        for solution_key in self.processor.solution_configs.keys():
            self.train_solution_models(solution_key)

        # 生成对比报告
        self.generate_comparison_report()

        # 保存所有模型
        self.save_all_models()

        print(f"\n{'='*70}")
        print("[OK] 所有模型训练完成！")
        print(f"{'='*70}")

        return self.results

    def generate_comparison_report(self):
        """生成模型对比报告"""
        print(f"\n{'='*70}")
        print("模型性能对比")
        print(f"{'='*70}")

        print(f"\n{'溶液':<15} {'模型':<15} {'测试R²':<12} {'MAE':<12} {'CV-R²':<12}")
        print("-"*70)

        for sol_key, result in self.results.items():
            name = result['solution_name']

            # RandomForest
            rf = result['rf_metrics']
            print(f"{name:<15} {'RF':<15} {rf['test_r2']:<12.4f} {rf['test_mae']:<12.4f} {result['rf_cv']['mean']:<12.4f}")

            # SVR
            svr = result['svr_metrics']
            print(f"{'':<15} {'SVR':<15} {svr['test_r2']:<12.4f} {svr['test_mae']:<12.4f} {result['svr_cv']['mean']:<12.4f}")

            # 最佳
            best = result['best_metrics']
            best_type = 'RF' if result['best_model_type'] == 'rf' else 'SVR'
            print(f"{'':<15} {'最佳('+best_type+')':<15} {best['test_r2']:<12.4f} {best['test_mae']:<12.4f}")
            print()

    def save_all_models(self):
        """保存所有训练好的模型"""
        models_dir = Path('models')
        models_dir.mkdir(exist_ok=True)

        for solution_key, model_data in self.models.items():
            solution_name = model_data['solution_name']

            # 保存RF模型
            rf_file = models_dir / f"{solution_key}_random_forest.pkl"
            with open(rf_file, 'wb') as f:
                pickle.dump(model_data['rf_model'], f)
            print(f"[OK] RF模型已保存: {rf_file}")

            # 保存SVR模型
            svr_file = models_dir / f"{solution_key}_svr.pkl"
            with open(svr_file, 'wb') as f:
                pickle.dump(model_data['svr_model'], f)
            print(f"[OK] SVR模型已保存: {svr_file}")

            # 保存元数据
            metadata = {
                'solution_key': solution_key,
                'solution_name': solution_name,
                'best_model_type': model_data['best_model_type'],
                'feature_cols': model_data['feature_cols'],
                'trained_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            meta_file = models_dir / f"{solution_key}_metadata.json"
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # 保存标准化器
            scaler_file = models_dir / f"{solution_key}_scaler.pkl"
            with open(scaler_file, 'wb') as f:
                pickle.dump(model_data['scaler'], f)


def main():
    """主函数"""
    # 导入数据处理器
    from 双溶液数据预处理脚本 import DualSolutionDataProcessor

    print("\n" + "="*70)
    print("   双溶液模型训练流程")
    print("="*70)

    # 数据预处理
    print("\n[步骤1] 数据预处理...")
    data_processor = DualSolutionDataProcessor()
    data_processor.process_all_solutions()

    # 模型训练
    print("\n[步骤2] 模型训练...")
    trainer = DualSolutionModelTrainer(data_processor)
    results = trainer.train_all_solutions()

    # 保存训练结果摘要
    summary_file = Path('model_results') / 'training_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 训练摘要已保存: {summary_file}")

    print("\n" + "="*70)
    print("训练完成！")
    print("="*70)
    print("\n下一步: 运行后端集成")
    print("  python backend/dual_solution_server.py")

    return data_processor, trainer


if __name__ == "__main__":
    data_processor, trainer = main()
