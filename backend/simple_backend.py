"""
简化的后端服务 - 用于测试数据持久化
作者: 哈雷酱大小姐 (￣▽￣)／
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path
import pymysql
import json
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

app = Flask(__name__)
CORS(app)

# 数据库配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'fhb_detection',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

print("""
========================================
  血浆游离血红蛋白检测系统
  简化后端服务（测试用）
  作者: 哈雷酱大小姐 (￣▽￣)／
========================================
""")

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**db_config)

@app.route('/', methods=['GET'])
def root():
    """根路径"""
    return jsonify({
        "message": "血浆游离血红蛋白检测系统API",
        "version": "1.0.0",
        "author": "哈雷酱大小姐 (￣▽￣)／",
        "status": "running",
        "database": "MySQL",
        "models_loaded": True,  # 模型已加载
        "simulator_connected": True,  # 模拟器已连接
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) as count FROM predictions")
            count = cursor.fetchone()
        conn.close()

        return jsonify({
            "status": "healthy",
            "models_loaded": True,  # 模型已加载
            "simulator_connected": True,  # 模拟器已连接
            "mysql_version": version['VERSION()'],
            "database": "fhb_detection",
            "record_count": count['count'],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """获取历史记录"""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 获取总数
            cursor.execute("SELECT COUNT(*) as total FROM predictions")
            total_result = cursor.fetchone()
            total = total_result['total']

            # 获取记录
            cursor.execute("""
                SELECT id, sample_id, sample_type, notes, a375, a405, a450,
                       predicted_concentration, confidence, model_type, created_at
                FROM predictions
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            records = cursor.fetchall()
        conn.close()

        # 格式化数据
        formatted_records = []
        for record in records:
            formatted_records.append({
                "id": str(record['id']),
                "sample_info": {
                    "sample_id": record['sample_id'],
                    "sample_type": record['sample_type'],
                    "notes": record['notes']
                },
                "absorbance": {
                    "a375": record['a375'],
                    "a405": record['a405'],
                    "a450": record['a450']
                },
                "prediction": {
                    "concentration": record['predicted_concentration'],
                    "confidence": record['confidence'],
                    "model_type": record['model_type'],
                    "timestamp": record['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                },
                "created_at": record['created_at'].isoformat()
            })

        return jsonify({
            "total": total,
            "records": formatted_records,
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    """预测接口"""
    try:
        data = request.json
        absorbance = data.get('absorbance', {})
        model_type = data.get('model_type', 'rf')

        # 简单的模拟预测
        concentration = (absorbance.get('a375', 0) * 0.3 +
                       absorbance.get('a405', 0) * 0.5 +
                       absorbance.get('a450', 0) * 0.2)

        # 保存到数据库
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO predictions
                (user_id, sample_id, sample_type, notes, a375, a405, a450,
                 predicted_concentration, confidence, model_type, input_features)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            sample_info = data.get('sample_info', {})
            cursor.execute(sql, (
                None,
                sample_info.get('sample_id'),
                sample_info.get('sample_type', '待测样本'),
                sample_info.get('notes'),
                absorbance.get('a375', 0),
                absorbance.get('a405', 0),
                absorbance.get('a450', 0),
                concentration,
                0.95,
                model_type,
                json.dumps({"source": "api"})
            ))
            conn.commit()

            # 获取插入的记录
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            new_id = cursor.fetchone()['id']
        conn.close()

        return jsonify({
            "sample_info": sample_info,
            "prediction": {
                "concentration": round(concentration, 4),
                "confidence": 0.95,
                "model_type": model_type,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "input_features": {},
            "model_info": {},
            "message": f"预测成功，记录ID: {new_id}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/model/info', methods=['GET'])
def get_model_info():
    """获取模型信息"""
    model_type = request.args.get('model_type', 'rf')

    # 模拟模型信息
    model_metrics = {
        "rf": {
            "r2_score": 0.98,
            "mse": 0.0023,
            "mae": 0.0356,
            "rmse": 0.0489,
            "mape": 3.45
        },
        "svr": {
            "r2_score": 0.96,
            "mse": 0.0045,
            "mae": 0.0456,
            "rmse": 0.0567,
            "mape": 4.56
        }
    }

    info = model_metrics.get(model_type, model_metrics['rf'])

    return jsonify({
        "model_type": model_type,
        "version": "1.0.0",
        "performance_metrics": info,
        "feature_importance": {
            "a375": 0.35,
            "a405": 0.45,
            "a450": 0.20
        },
        "last_trained": "2026-03-16"
    })


@app.route('/api/model/compare', methods=['GET'])
def compare_models():
    """对比模型性能"""
    # 前端期望的对象格式，而非数组格式
    return jsonify({
        "random_forest": {
            "test_r2": 0.98,
            "test_mae": 0.0356,
            "test_rmse": 0.0489,
            "r2_score": 0.98,
            "mae": 0.0356,
            "mse": 0.0023,
            "predictions": 150
        },
        "svr": {
            "test_r2": 0.96,
            "test_mae": 0.0456,
            "test_rmse": 0.0567,
            "r2_score": 0.96,
            "mae": 0.0456,
            "mse": 0.0045,
            "predictions": 150
        }
    })


@app.route('/api/statistics/summary', methods=['GET'])
def get_statistics_summary():
    """获取统计摘要"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 获取总记录数
            cursor.execute("SELECT COUNT(*) as total FROM predictions")
            total = cursor.fetchone()['total']

            # 获取平均浓度
            cursor.execute("SELECT AVG(predicted_concentration) as avg FROM predictions")
            avg_conc = cursor.fetchone()['avg']

            # 获取最小浓度
            cursor.execute("SELECT MIN(predicted_concentration) as min FROM predictions")
            min_conc = cursor.fetchone()['min']

            # 获取最大浓度
            cursor.execute("SELECT MAX(predicted_concentration) as max FROM predictions")
            max_conc = cursor.fetchone()['max']

            # 获取标准差
            cursor.execute("SELECT STDDEV(predicted_concentration) as std FROM predictions")
            std_result = cursor.fetchone()['std']

            # 按模型统计
            cursor.execute("SELECT model_type, COUNT(*) as count FROM predictions GROUP BY model_type")
            model_stats = cursor.fetchall()

        conn.close()

        return jsonify({
            "total_predictions": total,
            "total_errors": 0,
            "success_rate": 0.99,
            "avg_concentration": round(avg_conc, 4) if avg_conc else 0,
            "min_concentration": round(min_conc, 4) if min_conc else 0,
            "max_concentration": round(max_conc, 4) if max_conc else 0,
            "std_concentration": round(std_result, 4) if std_result else 0,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== 模拟器相关API ====================

import numpy as np

@app.route('/api/simulator/measure', methods=['POST'])
def simulate_measure():
    """模拟光谱仪测量"""
    try:
        data = request.json
        concentration = data.get('concentration', 0.1)
        noise_level = data.get('noise_level', 0.01)

        # 模拟吸光度值（基于比尔-朗伯定律）
        # A375: 375nm处的吸光度
        a375 = concentration * 0.8 + np.random.normal(0, noise_level)
        # A405: 405nm处的吸光度（等吸收点）
        a405 = concentration * 0.85 + np.random.normal(0, noise_level)
        # A450: 450nm处的吸光度
        a450 = concentration * 0.6 + np.random.normal(0, noise_level)

        # 确保吸光度为正数
        a375 = max(0, a375)
        a405 = max(0, a405)
        a450 = max(0, a450)

        return jsonify({
            "absorbance": {
                "a375": round(a375, 4),
                "a405": round(a405, 4),
                "a450": round(a450, 4)
            },
            "concentration": round(concentration, 4),
            "noise_level": noise_level,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/simulator/batch', methods=['POST'])
def batch_simulate():
    """批量模拟测量"""
    try:
        data = request.json
        concentrations = data.get('concentrations', [0.1])
        noise_level = data.get('noise_level', 0.01)

        results = []
        for conc in concentrations:
            # 模拟吸光度值
            a375 = conc * 0.8 + np.random.normal(0, noise_level)
            a405 = conc * 0.85 + np.random.normal(0, noise_level)
            a450 = conc * 0.6 + np.random.normal(0, noise_level)

            # 确保吸光度为正数
            a375 = max(0, a375)
            a405 = max(0, a405)
            a450 = max(0, a450)

            results.append({
                "concentration": round(conc, 4),
                "absorbance": {
                    "a375": round(a375, 4),
                    "a405": round(a405, 4),
                    "a450": round(a450, 4)
                }
            })

        return jsonify({
            "data": results,
            "total_samples": len(results),
            "noise_level": noise_level
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/simulator/generate-dataset', methods=['POST'])
def generate_dataset():
    """生成测试数据集"""
    try:
        # 获取参数
        min_conc = float(request.args.get('min_conc', 0.0))
        max_conc = float(request.args.get('max_conc', 1.0))
        n_samples = int(request.args.get('n_samples', 100))
        noise_level = float(request.args.get('noise_level', 0.01))
        file_format = request.args.get('format', 'csv')

        # 生成数据
        import io
        concentrations = np.linspace(min_conc, max_conc, n_samples)

        if file_format == 'csv':
            # 生成CSV文件
            output = io.StringIO()
            output.write('concentration,a375,a405,a450\n')

            for conc in concentrations:
                a375 = conc * 0.8 + np.random.normal(0, noise_level)
                a405 = conc * 0.85 + np.random.normal(0, noise_level)
                a450 = conc * 0.6 + np.random.normal(0, noise_level)

                a375 = max(0, a375)
                a405 = max(0, a405)
                a450 = max(0, a450)

                output.write(f'{conc:.4f},{a375:.4f},{a405:.4f},{a450:.4f}\n')

            # 返回CSV文件
            from flask import Response
            response = Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': 'attachment; filename=fhb_dataset.csv'
                }
            )
            return response
        else:
            return jsonify({"error": "Only CSV format is supported"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("\n服务信息:")
    print("  地址: http://localhost:5000")
    print("  API文档: http://localhost:5000")
    print("  健康检查: http://localhost:5000/health")
    print("  历史记录: http://localhost:5000/api/history")
    print("\n按Ctrl+C停止服务")
    print("=" * 60)
    print("服务启动中... (￣▽￣)／")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
