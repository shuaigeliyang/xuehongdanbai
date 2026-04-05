"""
验证MySQL数据
作者: 哈雷酱大小姐 (￣▽￣)／
"""

import pymysql
import json
from datetime import datetime

# 数据库配置
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'fhb_detection',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

print("""
========================================
  MySQL数据验证工具
  作者: 哈雷酱大小姐 (￣▽￣)／
========================================
""")

try:
    connection = pymysql.connect(**config)
    print("[OK] 成功连接到数据库\n")

    with connection.cursor() as cursor:
        # 查看表结构
        print("=" * 60)
        print("数据库表结构:")
        print("=" * 60)
        cursor.execute("DESCRIBE predictions")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col['Field']:20s} {col['Type']:20s} {col['Null']:5s} {col['Key']:5s}")

        # 查看所有数据
        print("\n" + "=" * 60)
        print("预测记录数据:")
        print("=" * 60)
        cursor.execute("""
            SELECT id, sample_id, sample_type, a375, a405, a450,
                   predicted_concentration, confidence, model_type, created_at
            FROM predictions
            ORDER BY created_at DESC
        """)
        results = cursor.fetchall()

        print(f"\n总记录数: {len(results)}\n")
        for row in results:
            print(f"ID: {row['id']}")
            print(f"  样本编号: {row['sample_id']}")
            print(f"  样本类型: {row['sample_type']}")
            print(f"  吸光度: A375={row['a375']:.4f}, A405={row['a405']:.4f}, A450={row['a450']:.4f}")
            print(f"  预测浓度: {row['predicted_concentration']:.4f} g/L")
            print(f"  置信度: {row['confidence']:.2%}")
            print(f"  模型类型: {row['model_type']}")
            print(f"  创建时间: {row['created_at']}")
            print()

        # 统计信息
        print("=" * 60)
        print("统计信息:")
        print("=" * 60)
        cursor.execute("SELECT COUNT(*) as total FROM predictions")
        total = cursor.fetchone()['total']
        print(f"总记录数: {total}")

        cursor.execute("SELECT model_type, COUNT(*) as count FROM predictions GROUP BY model_type")
        model_stats = cursor.fetchall()
        print("\n按模型统计:")
        for stat in model_stats:
            print(f"  {stat['model_type']}: {stat['count']} 条")

        cursor.execute("SELECT AVG(predicted_concentration) as avg_conc FROM predictions")
        avg_conc = cursor.fetchone()['avg_conc']
        print(f"\n平均浓度: {avg_conc:.4f} g/L")

    print("\n" + "=" * 60)
    print("数据验证完成！(￣▽￣)／")
    print("=" * 60)

except Exception as e:
    print(f"[ERROR] {e}")

finally:
    if 'connection' in locals():
        connection.close()
        print("数据库连接已关闭")
