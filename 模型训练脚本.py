"""
血浆游离血红蛋白检测系统 - 机器学习模型训练模块
作者: 哈雷酱大小姐
功能: SVM回归和随机森林模型训练、评估和对比
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
import pickle
import json
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class FHbModelTrainer:
    """血浆游离血红蛋白检测模型训练器"""

    def __init__(self):
        self.svr_model = None
        self.rf_model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.results = {}

    def load_data(self, data_file='processed_data.csv'):
        """加载预处理后的数据"""
        print("=" * 60)
        print("[加载数据]")
        print("=" * 60)

        df = pd.read_csv(data_file)

        # 分离特征和目标
        feature_cols = [col for col in df.columns if col != '浓度值']
        X = df[feature_cols].values
        y = df['浓度值'].values

        self.feature_names = feature_cols

        print(f"[OK] 数据加载完成")
        print(f"    样本数: {len(X)}")
        print(f"    特征数: {len(feature_cols)}")
        print(f"    特征列表: {feature_cols}")
        print(f"=" * 60)

        return X, y

    def split_data(self, X, y, test_size=0.2, random_state=42):
        """划分训练集和测试集"""
        print("\n" + "=" * 60)
        print("[数据集划分]")
        print("=" * 60)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        # 标准化特征
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        print(f"训练集: {len(X_train)} 样本")
        print(f"测试集: {len(X_test)} 样本")
        print(f"=" * 60)

        return X_train_scaled, X_test_scaled, y_train, y_test

    def train_svr(self, X_train, y_train, X_test, y_test):
        """训练支持向量机回归模型"""
        print("\n" + "=" * 60)
        print("[SVM回归模型训练]")
        print("=" * 60)

        # 超参数网格搜索
        print("\n[1] 超参数优化...")
        param_grid = {
            'kernel': ['rbf', 'linear'],
            'C': [0.1, 1, 10, 100],
            'gamma': ['scale', 'auto', 0.01, 0.1, 1],
            'epsilon': [0.01, 0.1, 0.2]
        }

        svr = SVR()
        grid_search = GridSearchCV(
            svr, param_grid, cv=5,
            scoring='neg_mean_squared_error',
            n_jobs=-1, verbose=0
        )

        grid_search.fit(X_train, y_train)

        print(f"[OK] 最佳参数: {grid_search.best_params_}")
        print(f"[OK] 最佳交叉验证得分: {-grid_search.best_score_:.6f}")

        # 使用最佳参数训练模型
        best_svr = grid_search.best_estimator_
        best_svr.fit(X_train, y_train)

        # 预测
        y_train_pred = best_svr.predict(X_train)
        y_test_pred = best_svr.predict(X_test)

        # 评估
        train_mse = mean_squared_error(y_train, y_train_pred)
        test_mse = mean_squared_error(y_test, y_test_pred)
        train_mae = mean_absolute_error(y_train, y_train_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)

        print(f"\n[2] 模型评估:")
        print(f"    训练集 - MSE: {train_mse:.6f}, MAE: {train_mae:.6f}, R2: {train_r2:.6f}")
        print(f"    测试集 - MSE: {test_mse:.6f}, MAE: {test_mae:.6f}, R2: {test_r2:.6f}")

        # 交叉验证
        cv_scores = cross_val_score(best_svr, X_train, y_train, cv=5, scoring='r2')
        print(f"\n[3] 5折交叉验证 R2: {cv_scores.mean():.6f} (+/- {cv_scores.std()*2:.6f})")

        self.svr_model = best_svr
        self.results['SVR'] = {
            'model': 'SVR',
            'best_params': grid_search.best_params_,
            'train_mse': train_mse,
            'test_mse': test_mse,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_r2': train_r2,
            'test_r2': test_r2,
            'cv_r2_mean': cv_scores.mean(),
            'cv_r2_std': cv_scores.std(),
            'y_train_pred': y_train_pred,
            'y_test_pred': y_test_pred
        }

        print(f"=" * 60)
        print("[OK] SVM回归模型训练完成！")
        print(f"=" * 60)

        return best_svr

    def train_random_forest(self, X_train, y_train, X_test, y_test):
        """训练随机森林回归模型"""
        print("\n" + "=" * 60)
        print("[随机森林回归模型训练]")
        print("=" * 60)

        # 超参数网格搜索
        print("\n[1] 超参数优化...")
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [None, 10, 20, 30],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }

        rf = RandomForestRegressor(random_state=42)
        grid_search = GridSearchCV(
            rf, param_grid, cv=5,
            scoring='neg_mean_squared_error',
            n_jobs=-1, verbose=0
        )

        grid_search.fit(X_train, y_train)

        print(f"[OK] 最佳参数: {grid_search.best_params_}")
        print(f"[OK] 最佳交叉验证得分: {-grid_search.best_score_:.6f}")

        # 使用最佳参数训练模型
        best_rf = grid_search.best_estimator_
        best_rf.fit(X_train, y_train)

        # 预测
        y_train_pred = best_rf.predict(X_train)
        y_test_pred = best_rf.predict(X_test)

        # 评估
        train_mse = mean_squared_error(y_train, y_train_pred)
        test_mse = mean_squared_error(y_test, y_test_pred)
        train_mae = mean_absolute_error(y_train, y_train_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)

        print(f"\n[2] 模型评估:")
        print(f"    训练集 - MSE: {train_mse:.6f}, MAE: {train_mae:.6f}, R2: {train_r2:.6f}")
        print(f"    测试集 - MSE: {test_mse:.6f}, MAE: {test_mae:.6f}, R2: {test_r2:.6f}")

        # 交叉验证
        cv_scores = cross_val_score(best_rf, X_train, y_train, cv=5, scoring='r2')
        print(f"\n[3] 5折交叉验证 R2: {cv_scores.mean():.6f} (+/- {cv_scores.std()*2:.6f})")

        # 特征重要性
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': best_rf.feature_importances_
        }).sort_values('importance', ascending=False)

        print(f"\n[4] 特征重要性:")
        for idx, row in feature_importance.iterrows():
            print(f"    {row['feature']}: {row['importance']:.6f}")

        self.rf_model = best_rf
        self.results['RandomForest'] = {
            'model': 'RandomForest',
            'best_params': grid_search.best_params_,
            'train_mse': train_mse,
            'test_mse': test_mse,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_r2': train_r2,
            'test_r2': test_r2,
            'cv_r2_mean': cv_scores.mean(),
            'cv_r2_std': cv_scores.std(),
            'feature_importance': feature_importance,
            'y_train_pred': y_train_pred,
            'y_test_pred': y_test_pred
        }

        print(f"=" * 60)
        print("[OK] 随机森林回归模型训练完成！")
        print(f"=" * 60)

        return best_rf

    def compare_models(self, y_train, y_test):
        """对比两个模型的性能"""
        print("\n" + "=" * 60)
        print("[模型性能对比]")
        print("=" * 60)

        # 创建对比表格
        comparison_data = []
        for model_name, results in self.results.items():
            comparison_data.append({
                '模型': model_name,
                '训练MSE': results['train_mse'],
                '测试MSE': results['test_mse'],
                '训练MAE': results['train_mae'],
                '测试MAE': results['test_mae'],
                '训练R2': results['train_r2'],
                '测试R2': results['test_r2'],
                '交叉验证R2': results['cv_r2_mean']
            })

        df_comparison = pd.DataFrame(comparison_data)
        print("\n" + df_comparison.to_string(index=False))

        # 保存对比结果
        df_comparison.to_csv('模型对比结果.csv', index=False, encoding='utf-8-sig')
        print(f"\n[OK] 对比结果已保存: 模型对比结果.csv")

        return df_comparison

    def visualize_results(self, y_train, y_test):
        """可视化结果"""
        print("\n[生成可视化报告...]")

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('模型性能可视化对比', fontsize=16, fontweight='bold')

        # 1. 测试集预测 vs 实际 - SVR
        axes[0, 0].scatter(y_test, self.results['SVR']['y_test_pred'],
                          alpha=0.6, color='#FF6B6B', label='SVR')
        axes[0, 0].plot([y_test.min(), y_test.max()],
                        [y_test.min(), y_test.max()], 'r--', lw=2)
        axes[0, 0].set_xlabel('实际浓度 (g/L)', fontweight='bold')
        axes[0, 0].set_ylabel('预测浓度 (g/L)', fontweight='bold')
        axes[0, 0].set_title('SVR: 预测 vs 实际', fontweight='bold')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # 2. 测试集预测 vs 实际 - RandomForest
        axes[0, 1].scatter(y_test, self.results['RandomForest']['y_test_pred'],
                          alpha=0.6, color='#4ECDC4', label='RandomForest')
        axes[0, 1].plot([y_test.min(), y_test.max()],
                        [y_test.min(), y_test.max()], 'r--', lw=2)
        axes[0, 1].set_xlabel('实际浓度 (g/L)', fontweight='bold')
        axes[0, 1].set_ylabel('预测浓度 (g/L)', fontweight='bold')
        axes[0, 1].set_title('RandomForest: 预测 vs 实际', fontweight='bold')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # 3. 残差分布对比
        svr_residuals = y_test - self.results['SVR']['y_test_pred']
        rf_residuals = y_test - self.results['RandomForest']['y_test_pred']

        axes[0, 2].hist(svr_residuals, bins=10, alpha=0.5, label='SVR', color='#FF6B6B')
        axes[0, 2].hist(rf_residuals, bins=10, alpha=0.5, label='RF', color='#4ECDC4')
        axes[0, 2].axvline(x=0, color='r', linestyle='--', linewidth=2)
        axes[0, 2].set_xlabel('残差', fontweight='bold')
        axes[0, 2].set_ylabel('频数', fontweight='bold')
        axes[0, 2].set_title('残差分布对比', fontweight='bold')
        axes[0, 2].legend()
        axes[0, 2].grid(True, alpha=0.3)

        # 4. 性能指标对比
        metrics = ['MSE', 'MAE', 'R2']
        svr_metrics = [self.results['SVR']['test_mse'],
                      self.results['SVR']['test_mae'],
                      self.results['SVR']['test_r2']]
        rf_metrics = [self.results['RandomForest']['test_mse'],
                     self.results['RandomForest']['test_mae'],
                     self.results['RandomForest']['test_r2']]

        x = np.arange(len(metrics))
        width = 0.35

        axes[1, 0].bar(x - width/2, svr_metrics, width, label='SVR', color='#FF6B6B')
        axes[1, 0].bar(x + width/2, rf_metrics, width, label='RF', color='#4ECDC4')
        axes[1, 0].set_ylabel('指标值', fontweight='bold')
        axes[1, 0].set_title('性能指标对比', fontweight='bold')
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels(metrics)
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3, axis='y')

        # 5. 特征重要性 (RandomForest)
        feature_imp = self.results['RandomForest']['feature_importance']
        axes[1, 1].barh(feature_imp['feature'], feature_imp['importance'], color='#45B7D1')
        axes[1, 1].set_xlabel('重要性', fontweight='bold')
        axes[1, 1].set_title('特征重要性 (RandomForest)', fontweight='bold')
        axes[1, 1].grid(True, alpha=0.3, axis='x')

        # 6. 误差分布
        axes[1, 2].scatter(range(len(svr_residuals)), svr_residuals,
                          alpha=0.6, label='SVR', color='#FF6B6B')
        axes[1, 2].scatter(range(len(rf_residuals)), rf_residuals,
                          alpha=0.6, label='RF', color='#4ECDC4')
        axes[1, 2].axhline(y=0, color='r', linestyle='--', linewidth=2)
        axes[1, 2].set_xlabel('样本索引', fontweight='bold')
        axes[1, 2].set_ylabel('残差', fontweight='bold')
        axes[1, 2].set_title('测试集残差分布', fontweight='bold')
        axes[1, 2].legend()
        axes[1, 2].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('02_模型性能对比.png', dpi=300, bbox_inches='tight')
        print("[OK] 可视化报告已保存: 02_模型性能对比.png")

        return fig

    def save_models(self):
        """保存训练好的模型"""
        print("\n" + "=" * 60)
        print("[保存模型]")
        print("=" * 60)

        # 保存SVR模型
        with open('svr_model.pkl', 'wb') as f:
            pickle.dump(self.svr_model, f)
        print("[OK] SVR模型已保存: svr_model.pkl")

        # 保存RandomForest模型
        with open('rf_model.pkl', 'wb') as f:
            pickle.dump(self.rf_model, f)
        print("[OK] RandomForest模型已保存: rf_model.pkl")

        # 保存标准化器
        with open('scaler.pkl', 'wb') as f:
            pickle.dump(self.scaler, f)
        print("[OK] 标准化器已保存: scaler.pkl")

        # 保存训练结果
        with open('training_results.json', 'w', encoding='utf-8') as f:
            results_to_save = {}
            for model_name, results in self.results.items():
                results_to_save[model_name] = {
                    k: v for k, v in results.items()
                    if k not in ['y_train_pred', 'y_test_pred', 'feature_importance']
                }
                if 'feature_importance' in results:
                    results_to_save[model_name]['feature_importance'] = \
                        results['feature_importance'].to_dict()

            json.dump(results_to_save, f, ensure_ascii=False, indent=2)
        print("[OK] 训练结果已保存: training_results.json")

        print(f"=" * 60)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("   血浆游离血红蛋白检测系统 - 模型训练模块")
    print("   作者: 哈雷酱大小姐")
    print("=" * 60 + "\n")

    # 初始化训练器
    trainer = FHbModelTrainer()

    # 加载数据
    X, y = trainer.load_data('processed_data.csv')

    # 划分数据集
    X_train, X_test, y_train, y_test = trainer.split_data(X, y)

    # 训练SVM回归模型
    trainer.train_svr(X_train, y_train, X_test, y_test)

    # 训练随机森林回归模型
    trainer.train_random_forest(X_train, y_train, X_test, y_test)

    # 对比模型性能
    trainer.compare_models(y_train, y_test)

    # 可视化结果
    trainer.visualize_results(y_train, y_test)

    # 保存模型
    trainer.save_models()

    print("\n" + "=" * 60)
    print("   模型训练阶段完成！")
    print("=" * 60 + "\n")

    return trainer


if __name__ == "__main__":
    trainer = main()
