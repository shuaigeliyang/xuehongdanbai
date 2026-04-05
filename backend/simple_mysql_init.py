"""
最简化的MySQL操作脚本
作者: 哈雷酱大小姐 (￣▽￣)／
直接使用pymysql，不需要SQLAlchemy
"""

import pymysql
import json
from datetime import datetime
import random
import sys

print("""
========================================
  血浆游离血红蛋白检测系统
  MySQL数据库初始化工具（最简版）
  作者: 哈雷酱大小姐 (￣▽￣)／
========================================
""")

# 数据库配置
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'fhb_detection',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

try:
    # 连接数据库
    print("[1/5] 连接MySQL数据库...")
    connection = pymysql.connect(**config)
    print("    [OK] 成功连接到数据库")

    # 创建表
    print("\n[2/5] 创建预测记录表...")
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NULL,
                sample_id VARCHAR(100),
                sample_type VARCHAR(50) DEFAULT '待测样本',
                notes TEXT,
                a375 FLOAT NOT NULL,
                a405 FLOAT NOT NULL,
                a450 FLOAT NOT NULL,
                predicted_concentration FLOAT NOT NULL,
                confidence FLOAT,
                model_type VARCHAR(20) DEFAULT 'rf',
                input_features JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_created_at (created_at),
                INDEX idx_model_type (model_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        connection.commit()
        print("    [OK] 表创建成功")

    # 检查现有数据
    print("\n[3/5] 检查现有数据...")
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM predictions")
        result = cursor.fetchone()
        print(f"    当前记录数: {result['count']}")

    # 插入测试数据
    print("\n[4/5] 插入测试数据...")
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

    with connection.cursor() as cursor:
        for i, data in enumerate(test_data, 1):
            input_features = {
                "ratio_405_375": round(data["a405"] / data["a375"], 4),
                "ratio_450_405": round(data["a450"] / data["a405"], 4)
            }

            sql = """
                INSERT INTO predictions
                (user_id, sample_id, sample_type, notes, a375, a405, a450,
                 predicted_concentration, confidence, model_type, input_features)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(sql, (
                None,
                f"TEST-{i:03d}",
                "测试样本",
                f"自动生成的测试数据 {i}",
                data["a375"],
                data["a405"],
                data["a450"],
                data["concentration"],
                round(random.uniform(0.90, 0.99), 4),
                data["model_type"],
                json.dumps(input_features)
            ))

        connection.commit()
        print(f"    [OK] 插入了 {len(test_data)} 条测试数据")

    # 查询验证
    print("\n[5/5] 查询验证数据...")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, sample_id, predicted_concentration, model_type, created_at
            FROM predictions
            ORDER BY created_at DESC
            LIMIT 10
        """)
        results = cursor.fetchall()

        print(f"    [OK] 查询到 {len(results)} 条记录:")
        for row in results:
            print(f"       - ID: {row['id']}, 样本: {row['sample_id']}, "
                  f"浓度: {row['predicted_concentration']:.4f} g/L, "
                  f"模型: {row['model_type']}, "
                  f"时间: {row['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")

    # 获取统计信息
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as total FROM predictions")
        total = cursor.fetchone()['total']

        cursor.execute("SELECT model_type, COUNT(*) as count FROM predictions GROUP BY model_type")
        model_stats = cursor.fetchall()

        print(f"\n统计信息:")
        print(f"    总记录数: {total}")
        for stat in model_stats:
            print(f"    {stat['model_type']}模型: {stat['count']} 条")

    print("\n" + "=" * 60)
    print("数据库初始化和测试完成！(￣▽￣)／")
    print("=" * 60)

    print("\n下一步:")
    print("1. 启动后端服务会使用相同的数据库")
    print("2. 前端访问 http://localhost:3000")
    print("3. 数据会永久保存在MySQL中")

except Exception as e:
    print(f"\n[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    if 'connection' in locals():
        connection.close()
        print("\n数据库连接已关闭")
