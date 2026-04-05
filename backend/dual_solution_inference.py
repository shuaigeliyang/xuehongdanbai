"""
血浆游离血红蛋白检测系统 - 双溶液模型推理引擎
作者: 哈雷酱大小姐 (￣▽￣)／
功能: 根据溶液类型加载对应的ML模型进行预测
"""

import pickle
import numpy as np
import json
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DualSolutionInferenceEngine:
    """双溶液推理引擎 - 支持两种不同溶液的预测"""

    def __init__(self, model_dir: str = "../models"):
        """
        初始化双溶液推理引擎

        Args:
            model_dir: 模型文件目录
        """
        self.model_dir = Path(model_dir)

        # 溶液配置
        self.solution_configs = {
            'solution_a': {
                'name': '溶液A',
                'description': '2025年7月31日测量的标准溶液',
                'file': '实验记录-20250731.xlsx'
            },
            'solution_b': {
                'name': '溶液B',
                'description': '2025年8月12日测量的实验溶液',
                'file': '实验记录-20250812.xlsx'
            }
        }

        # 模型存储
        self.models = {}
        self.scalers = {}
        self.metadatas = {}

        # 特征名称
        self.feature_names = [
            '375nm', '405nm', '450nm',
            'A405_A375', 'A450_A405', 'A450_A375',
            'A405_minus_A375', 'A450_minus_A405', 'A_sum'
        ]

    def load_solution_models(self, solution_key: str) -> bool:
        """
        加载指定溶液的模型

        Args:
            solution_key: 溶液类型 ('solution_a' 或 'solution_b')

        Returns:
            是否加载成功
        """
        if solution_key not in self.solution_configs:
            logger.error(f"未知的溶液类型: {solution_key}")
            return False

        try:
            # 加载RF模型
            rf_path = self.model_dir / f"{solution_key}_random_forest.pkl"
            if rf_path.exists():
                with open(rf_path, 'rb') as f:
                    rf_model = pickle.load(f)
                logger.info(f"{solution_key} RandomForest模型加载成功")
            else:
                logger.warning(f"RF模型未找到: {rf_path}")
                rf_model = None

            # 加载SVR模型
            svr_path = self.model_dir / f"{solution_key}_svr.pkl"
            if svr_path.exists():
                with open(svr_path, 'rb') as f:
                    svr_model = pickle.load(f)
                logger.info(f"{solution_key} SVR模型加载成功")
            else:
                logger.warning(f"SVR模型未找到: {svr_path}")
                svr_model = None

            # 加载标准化器
            scaler_path = self.model_dir / f"{solution_key}_scaler.pkl"
            if scaler_path.exists():
                with open(scaler_path, 'rb') as f:
                    scaler = pickle.load(f)
                logger.info(f"{solution_key} 标准化器加载成功")
            else:
                logger.warning(f"标准化器未找到: {scaler_path}")
                scaler = None

            # 加载元数据
            meta_path = self.model_dir / f"{solution_key}_metadata.json"
            if meta_path.exists():
                with open(meta_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                logger.info(f"{solution_key} 元数据加载成功")
            else:
                logger.warning(f"元数据未找到: {meta_path}")
                metadata = {}

            # 检查至少有一个模型
            if rf_model is None and svr_model is None:
                logger.error(f"{solution_key} 没有可用的模型！")
                return False

            # 存储模型
            self.models[solution_key] = {
                'rf': rf_model,
                'svr': svr_model,
                'best': metadata.get('best_model_type', 'svr')
            }

            self.scalers[solution_key] = scaler
            self.metadatas[solution_key] = metadata

            return True

        except Exception as e:
            logger.error(f"{solution_key} 模型加载失败: {e}")
            return False

    def load_all_models(self) -> bool:
        """
        加载所有溶液的模型

        Returns:
            是否全部加载成功
        """
        logger.info("="*60)
        logger.info("加载双溶液模型...")
        logger.info("="*60)

        all_success = True
        for solution_key in self.solution_configs.keys():
            success = self.load_solution_models(solution_key)
            if not success:
                all_success = False

        if all_success:
            logger.info("="*60)
            logger.info("所有溶液模型加载完成！")
            logger.info("="*60)

        return all_success

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
        eps = 0.001

        features = np.array([[
            a375, a405, a450,
            a405 / (a375 + eps),
            a450 / (a405 + eps),
            a450 / (a375 + eps),
            a405 - a375,
            a450 - a405,
            a375 + a405 + a450
        ]])

        return features

    def predict(self,
                a375: float,
                a405: float,
                a450: float,
                solution_type: str = 'solution_a',
                model_type: str = 'best') -> Tuple[float, Dict]:
        """
        预测血浆游离血红蛋白浓度

        Args:
            a375: 375nm吸光度
            a405: 405nm吸光度
            a450: 450nm吸光度
            solution_type: 溶液类型 ('solution_a' 或 'solution_b')
            model_type: 模型类型 ('rf', 'svr', 或 'best'使用最佳模型)

        Returns:
            (预测浓度, 详细信息)
        """
        # 检查溶液类型
        if solution_type not in self.solution_configs:
            raise ValueError(f"未知的溶液类型: {solution_type}")

        # 检查模型是否加载
        if solution_type not in self.models:
            raise ValueError(f"{solution_type} 的模型未加载")

        # 确定使用的模型
        if model_type == 'best':
            model_type = self.models[solution_type]['best']

        model = self.models[solution_type][model_type]
        if model is None:
            raise ValueError(f"{solution_type} 的 {model_type} 模型未加载")

        # 特征提取
        features = self.extract_features(a375, a405, a450)

        # 特征标准化
        scaler = self.scalers.get(solution_type)
        if scaler is not None:
            features_scaled = scaler.transform(features)
        else:
            features_scaled = features

        # 预测
        concentration = model.predict(features_scaled)[0]

        # 构建详细信息
        details = {
            'solution_type': solution_type,
            'solution_name': self.solution_configs[solution_type]['name'],
            'model_type': model_type,
            'input_features': dict(zip(self.feature_names, features[0])),
            'input_absorbance': {
                '375nm': a375,
                '405nm': a405,
                '450nm': a450
            }
        }

        return concentration, details

    def validate_input(self, a375: float, a405: float, a450: float) -> Tuple[bool, Optional[str]]:
        """
        验证输入数据

        Args:
            a375, a405, a450: 吸光度值

        Returns:
            (是否有效, 错误信息)
        """
        for name, value in [('375nm', a375), ('405nm', a405), ('450nm', a450)]:
            if value < 0:
                return False, f"{name}吸光度不能为负数"
            if value > 10:
                return False, f"{name}吸光度值异常 (>10)"

        return True, None

    def get_solution_info(self, solution_type: str) -> Dict:
        """
        获取溶液信息

        Args:
            solution_type: 溶液类型

        Returns:
            溶液信息字典
        """
        if solution_type not in self.solution_configs:
            raise ValueError(f"未知的溶液类型: {solution_type}")

        config = self.solution_configs[solution_type]
        metadata = self.metadatas.get(solution_type, {})

        return {
            'solution_type': solution_type,
            'solution_name': config['name'],
            'description': config['description'],
            'data_file': config['file'],
            'best_model_type': metadata.get('best_model_type', 'unknown'),
            'trained_at': metadata.get('trained_at', 'unknown'),
            'feature_cols': metadata.get('feature_cols', self.feature_names)
        }

    def get_all_solutions_info(self) -> Dict:
        """获取所有溶液的信息"""
        return {
            sol_key: self.get_solution_info(sol_key)
            for sol_key in self.solution_configs.keys()
        }


# 全局推理引擎实例
_inference_engine = None


def get_dual_solution_engine(model_dir: str = "../models") -> DualSolutionInferenceEngine:
    """
    获取双溶液推理引擎单例

    Args:
        model_dir: 模型目录

    Returns:
        推理引擎实例
    """
    global _inference_engine

    if _inference_engine is None:
        _inference_engine = DualSolutionInferenceEngine(model_dir)
        _inference_engine.load_all_models()

    return _inference_engine


def main():
    """测试推理引擎"""
    print("="*60)
    print("双溶液推理引擎测试")
    print("="*60)

    # 创建引擎
    engine = DualSolutionInferenceEngine("../models")
    engine.load_all_models()

    # 测试预测
    print("\n[1] 溶液A预测测试:")
    a375, a405, a450 = 1.9702, 0.6393, 1.0960
    conc, details = engine.predict(a375, a405, a450, 'solution_a', 'best')
    print(f"    输入: A375={a375}, A405={a405}, A450={a450}")
    print(f"    预测浓度: {conc:.4f} g/L")
    print(f"    使用模型: {details['model_type']}")

    print("\n[2] 溶液B预测测试:")
    a375, a405, a450 = 0.0875, 0.0146, 0.0535
    conc, details = engine.predict(a375, a405, a450, 'solution_b', 'best')
    print(f"    输入: A375={a375}, A405={a405}, A450={a450}")
    print(f"    预测浓度: {conc:.4f} g/L")
    print(f"    使用模型: {details['model_type']}")

    # 溶液信息
    print("\n[3] 溶液信息:")
    all_info = engine.get_all_solutions_info()
    for sol_key, info in all_info.items():
        print(f"\n{info['solution_name']}:")
        print(f"  描述: {info['description']}")
        print(f"  最佳模型: {info['best_model_type']}")

    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == "__main__":
    main()
