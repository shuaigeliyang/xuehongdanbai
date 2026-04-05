"""快速验证MySQL记录数"""
import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='fhb_detection',
    cursorclass=pymysql.cursors.DictCursor
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) as total FROM predictions")
result = cursor.fetchone()

print(f"总记录数: {result['total']}")

cursor.execute("SELECT id, sample_id, predicted_concentration, created_at FROM predictions ORDER BY created_at DESC LIMIT 6")
records = cursor.fetchall()

print("\n最新的6条记录:")
for record in records:
    print(f"ID: {record['id']}, 样本: {record['sample_id']}, 浓度: {record['predicted_concentration']:.4f} g/L, 时间: {record['created_at']}")

conn.close()
