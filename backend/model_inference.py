"""
血浆游离血红蛋白检测系统 - 模型推理引擎
作者: 哈雷酱大小姐 (￣▽￣)／
功能: 加载ML模型，执行预测推理
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelInferenceEngine:
    """模型推理引擎"""

    def __init__(self, model_dir: str = "."):
        """
        初始化推理引擎

        Args:
            model_dir: 模型文件目录
        """
        self.model_dir = Path(model_dir)
        self.rf_model = None
        self.svr_model = None
        self.scaler = None
        self.feature_names = [
            '375nm', '405nm', '450nm',
            'A405_A375', 'A450_A405', 'A450_A375',
            'A405_minus_A375', 'A450_minus_A405', 'A_sum'
        ]

        # 模型性能指标（从训练结果读取）
        self.model_metrics = {
            'rf': {
                'test_r2': 0.9980,
                'test_mae': 0.0033,
                'test_mse': 0.000013,
                'cv_r2': 0.9910
            },
            'svr': {
                'test_r2': 0.9921,
                'test_mae': 0.0061,
                'test_mse': 0.000052,
                'cv_r2': 0.9919
            }
        }

        # 特征重要性（RandomForest）
        self.feature_importance = {
            'A405_A375': 82.63,
            'A450_A405': 7.21,
            'A450_minus_A405': 4.41,
            'A_sum': 1.60,
            '375nm': 1.08,
            'A450_A375': 1.01,
            '405nm': 0.98,
            '450nm': 0.70,
            'A405_minus_A375': 0.37
        }

    def load_models(self) -> bool:
        """
        加载训练好的模型

        Returns:
            是否加载成功
        """
        try:
            # 加载随机森林模型
            rf_path = self.model_dir / "随机森林模型.pkl"
            if rf_path.exists():
                with open(rf_path, 'rb') as f:
                    self.rf_model = pickle.load(f)
                logger.info("随机森林模型加载成功")
            else:
                logger.warning(f"随机森林模型未找到: {rf_path}")

            # 加载SVM回归模型
            svr_path = self.model_dir / "SVM回归模型.pkl"
            if svr_path.exists():
                with open(svr_path, 'rb') as f:
                    self.svr_model = pickle.load(f)
                logger.info("SVM回归模型加载成功")
            else:
                logger.warning(f"SVM回归模型未找到: {svr_path}")

            # 加载特征标准化器
            scaler_path = self.model_dir / "特征标准化器.pkl"
            if scaler_path.exists():
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                logger.info("特征标准化器加载成功")
            else:
                logger.warning(f"特征标准化器未找到: {scaler_path}")

            # 检查至少有一个模型加载成功
            if self.rf_model is None and self.svr_model is None:
                logger.error("没有可用的模型！")
                return False

            if self.scaler is None:
                logger.warning("标准化器未加载，将不进行特征标准化")

            return True

        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False

    def extract_features(self, a375: float, a405: float, a450: float) -> np.ndarray:
        """
        特征工程：从原始吸光度提取特征

        Args:
            a375: 375nm吸光度
            a405: 405nm吸光度
            a450: 450nm吸光度

        Returns:
            特征向量 (1, 9)
        """
        # 避免除零
        eps = 0.001

        features = np.array([[
            # 原始特征
            a375, a405, a450,

            # 比值特征
            a405 / (a375 + eps),  # A405/A375
            a450 / (a405 + eps),  # A450/A405
            a450 / (a375 + eps),  # A450/A375

            # 差值特征
            a405 - a375,          # A405-A375
            a450 - a405,          # A450-A405

            # 总和特征
            a375 + a405 + a450    # A_sum
        ]])

        return features

    def predict(self,
                a375: float,
                a405: float,
                a450: float,
                model_type: str = 'rf') -> Tuple[float, Dict]:
        """
        预测血浆游离血红蛋白浓度

        Args:
            a375: 375nm吸光度
            a405: 405nm吸光度
            a450: 450nm吸光度
            model_type: 模型类型 ('rf' 或 'svr')

        Returns:
            (预测浓度, 详细信息)
        """
        # 检查模型是否加载
        if model_type == 'rf':
            model = self.rf_model
        elif model_type == 'svr':
            model = self.svr_model
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")

        if model is None:
            raise ValueError(f"{model_type} 模型未加载")

        # 特征提取
        features = self.extract_features(a375, a405, a450)

        # 特征标准化（如果标准化器可用）
        if self.scaler is not None:
            features_scaled = self.scaler.transform(features)
        else:
            features_scaled = features

        # 预测
        concentration = model.predict(features_scaled)[0]

        # 计算置信度（基于模型R²）
        metrics = self.model_metrics[model_type]
        confidence = metrics['test_r2']

        # 构建详细信息
        details = {
            'model_type': model_type,
            'confidence': confidence,
            'input_features': dict(zip(self.feature_names, features[0])),
            'model_metrics': metrics
        }

        return concentration, details

    def batch_predict(self,
                      samples: list,
                      model_type: str = 'rf') -> list:
        """
        批量预测

        Args:
            samples: 样本列表，每个样本是 (a375, a405, a450) 元组
            model_type: 模型类型

        Returns:
            预测结果列表
        """
        results = []

        for i, (a375, a405, a450) in enumerate(samples):
            try:
                concentration, details = self.predict(a375, a405, a450, model_type)
                results.append({
                    'index': i,
                    'concentration': concentration,
                    'success': True,
                    'details': details
                })
            except Exception as e:
                logger.error(f"样本 {i} 预测失败: {e}")
                results.append({
                    'index': i,
                    'concentration': None,
                    'success': False,
                    'error': str(e)
                })

        return results

    def get_model_info(self, model_type: str = 'rf') -> Dict:
        """
        获取模型信息

        Args:
            model_type: 模型类型

        Returns:
            模型信息字典
        """
        if model_type not in ['rf', 'svr']:
            raise ValueError(f"不支持的模型类型: {model_type}")

        metrics = self.model_metrics[model_type]

        info = {
            'model_type': 'Random Forest' if model_type == 'rf' else 'SVM Regression',
            'version': '1.0.0',
            'performance_metrics': metrics,
            'feature_names': self.feature_names,
            'last_trained': '2026-03-16'
        }

        # 添加特征重要性（仅RandomForest）
        if model_type == 'rf':
            info['feature_importance'] = self.feature_importance

        return info

    def validate_input(self, a375: float, a405: float, a450: float) -> Tuple[bool, Optional[str]]:
        """
        验证输入数据

        Args:
            a375, a405, a450: 吸光度值

        Returns:
            (是否有效, 错误信息)
        """
        # 检查范围
        for name, value in [('375nm', a375), ('405nm', a405), ('450nm', a450)]:
            if value < 0:
                return False, f"{name}吸光度不能为负数"
            if value > 3:
                return False, f"{name}吸光度值异常 (可能超过测量范围)"

        # 检查数据合理性（405nm应该是最高，但允许测量噪声）
        if a405 < max(a375, a450) * 0.3:
            return False, "吸光度数据异常 (405nm应该是最高的，当前值过低)"

        return True, None


# 全局推理引擎实例
_inference_engine = None


def get_inference_engine(model_dir: str = ".") -> ModelInferenceEngine:
    """
    获取推理引擎单例

    Args:
        model_dir: 模型目录

    Returns:
        推理引擎实例
    """
    global _inference_engine

    if _inference_engine is None:
        _inference_engine = ModelInferenceEngine(model_dir)
        _inference_engine.load_models()

    return _inference_engine


def main():
    """测试推理引擎"""
    print("=" * 60)
    print("模型推理引擎测试")
    print("=" * 60)

    # 创建推理引擎
    engine = ModelInferenceEngine(".")
    engine.load_models()

    # 测试预测
    print("\n[1] 单次预测测试:")
    a375, a405, a450 = 0.1275, 0.1875, 0.0975
    print(f"    输入: A375={a375}, A405={a405}, A450={a450}")

    try:
        concentration_rf, details_rf = engine.predict(a375, a405, a450, 'rf')
        print(f"    RF预测: {concentration_rf:.4f} g/L")
        print(f"    置信度: {details_rf['confidence']:.4f}")

        concentration_svr, details_svr = engine.predict(a375, a405, a450, 'svr')
        print(f"    SVR预测: {concentration_svr:.4f} g/L")
        print(f"    置信度: {details_svr['confidence']:.4f}")

    except Exception as e:
        print(f"    预测失败: {e}")

    # 批量预测
    print("\n[2] 批量预测测试:")
    samples = [
        (0.0850, 0.1250, 0.0650),
        (0.1700, 0.2500, 0.1300),
        (0.2550, 0.3750, 0.1950)
    ]

    results = engine.batch_predict(samples, 'rf')
    for result in results:
        if result['success']:
            print(f"    样本 {result['index']}: {result['concentration']:.4f} g/L")

    # 模型信息
    print("\n[3] 模型信息:")
    info = engine.get_model_info('rf')
    print(f"    模型类型: {info['model_type']}")
    print(f"    R²: {info['performance_metrics']['test_r2']:.4f}")
    print(f"    MAE: {info['performance_metrics']['test_mae']:.4f} g/L")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
