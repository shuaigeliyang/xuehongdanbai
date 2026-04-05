"""
简化的后端服务 - 用于初始化数据库和测试
作者: 哈雷酱大小姐 (￣▽￣)／
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path
import json
from datetime import datetime
import random

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 使用简化的数据库配置
from db_config_simple import engine, get_db, init_db
from database import Base, PredictionRecord
from sqlalchemy.orm import Session

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 初始化数据库
print("""
========================================
  血浆游离血红蛋白检测系统
  数据库初始化和测试工具
  作者: 哈雷酱大小姐 (￣▽￣)／
========================================
""")

print("[1/4] 初始化数据库...")
try:
    init_db()
    print("    [OK] 数据库表创建成功")
except Exception as e:
    print(f"    [ERROR] 数据库初始化失败: {e}")
    sys.exit(1)

print("\n[2/4] 测试数据库连接...")
try:
    with engine.connect() as conn:
        result = conn.execute("SELECT VERSION()")
        version = result.scalar()
        print(f"    [OK] MySQL版本: {version}")
except Exception as e:
    print(f"    [ERROR] 连接失败: {e}")
    sys.exit(1)

print("\n[3/4] 插入测试数据...")
try:
    with get_db() as db:
        # 检查是否已有数据
        count = db.query(PredictionRecord).count()
        print(f"    当前记录数: {count}")

        # 插入5条测试数据
        test_data = [
            {
                "a375": 0.1275,
                "a405": 0.1875,
                "a450": 0.0975,
                "concentration": 0.1523,
                "model_type": "rf"
            },
            {
                "a375": 0.2341,
                "a405": 0.3124,
                "a450": 0.1456,
                "concentration": 0.2876,
                "model_type": "rf"
            },
            {
                "a375": 0.0987,
                "a405": 0.1432,
                "a450": 0.0765,
                "concentration": 0.1098,
                "model_type": "svr"
            },
            {
                "a375": 0.3456,
                "a405": 0.4567,
                "a450": 0.2345,
                "concentration": 0.4321,
                "model_type": "rf"
            },
            {
                "a375": 0.1876,
                "a405": 0.2543,
                "a450": 0.1234,
                "concentration": 0.2198,
                "model_type": "svr"
            }
        ]

        for i, data in enumerate(test_data, 1):
            record = PredictionRecord(
                user_id=None,
                sample_id=f"TEST-{i:03d}",
                sample_type="测试样本",
                notes=f"自动生成的测试数据 {i}",
                a375=data["a375"],
                a405=data["a405"],
                a450=data["a450"],
                predicted_concentration=data["concentration"],
                confidence=round(random.uniform(0.90, 0.99), 4),
                model_type=data["model_type"],
                input_features={
                    "ratio_405_375": round(data["a405"] / data["a375"], 4),
                    "ratio_450_405": round(data["a450"] / data["a405"], 4)
                }
            )
            db.add(record)

        db.commit()
        new_count = db.query(PredictionRecord).count()
        print(f"    [OK] 插入了 {len(test_data)} 条测试数据")
        print(f"    总记录数: {new_count}")

except Exception as e:
    print(f"    [ERROR] 插入数据失败: {e}")
    import traceback
    traceback.print_exc()

print("\n[4/4] 验证数据...")
try:
    with get_db() as db:
        records = db.query(PredictionRecord).order_by(PredictionRecord.created_at.desc()).limit(5).all()
        print(f"    [OK] 查询到 {len(records)} 条记录:")

        for record in records:
            print(f"       - ID: {record.id}, 样本: {record.sample_id}, "
                  f"浓度: {record.predicted_concentration:.4f} g/L, "
                  f"模型: {record.model_type}, "
                  f"时间: {record.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

except Exception as e:
    print(f"    [ERROR] 查询失败: {e}")

print("\n" + "=" * 60)
print("数据库初始化和测试完成！(￣▽￣)／")
print("=" * 60)

# Flask API路由
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT VERSION()")
            version = result.scalar()
        return jsonify({
            "status": "healthy",
            "mysql_version": version,
            "database": "fhb_detection",
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

        with get_db() as db:
            # 获取总数
            total = db.query(PredictionRecord).count()

            # 获取记录
            records = db.query(PredictionRecord).order_by(
                PredictionRecord.created_at.desc()
            ).offset(offset).limit(limit).all()

            # 格式化数据
            formatted_records = []
            for record in records:
                formatted_records.append({
                    "id": str(record.id),
                    "sample_info": {
                        "sample_id": record.sample_id,
                        "sample_type": record.sample_type,
                        "notes": record.notes
                    },
                    "absorbance": {
                        "a375": record.a375,
                        "a405": record.a405,
                        "a450": record.a450
                    },
                    "prediction": {
                        "concentration": record.predicted_concentration,
                        "confidence": record.confidence,
                        "model_type": record.model_type,
                        "timestamp": record.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "created_at": record.created_at.isoformat()
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
        with get_db() as db:
            record = PredictionRecord(
                user_id=None,
                sample_id=data.get('sample_info', {}).get('sample_id'),
                sample_type=data.get('sample_info', {}).get('sample_type', '待测样本'),
                notes=data.get('sample_info', {}).get('notes'),
                a375=absorbance.get('a375', 0),
                a405=absorbance.get('a405', 0),
                a450=absorbance.get('a450', 0),
                predicted_concentration=concentration,
                confidence=0.95,
                model_type=model_type,
                input_features={}
            )
            db.add(record)
            db.commit()

            # 返回结果
            return jsonify({
                "sample_info": data.get('sample_info'),
                "prediction": {
                    "concentration": round(concentration, 4),
                    "confidence": 0.95,
                    "model_type": model_type,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "input_features": {},
                "model_info": {}
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n现在你可以:")
    print("1. 查看MySQL中的数据:")
    print("   mysql -uroot -proot -e \"USE fhb_detection; SELECT * FROM predictions ORDER BY created_at DESC LIMIT 10;\"")
    print("2. 访问API测试:")
    print("   http://localhost:5000/health")
    print("   http://localhost:5000/api/history")
    print("3. 启动完整后端:")
    print("   python main_complete.py")
    print("\n按Ctrl+C停止服务")

    # 启动Flask服务
    app.run(host='0.0.0.0', port=5000, debug=False)
