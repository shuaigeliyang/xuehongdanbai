"""
创建MySQL数据库脚本
作者: 哈雷酱大小姐 (￣▽￣)／
"""

import mysql.connector
from mysql.connector import Error

def create_mysql_database():
    """创建MySQL数据库"""
    print("""
    ========================================
     血浆游离血红蛋白检测系统 - 创建MySQL数据库
     作者: 哈雷酱大小姐 (￣▽￣)／
    ========================================
    """)

    # MySQL连接配置
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root',
        'port': 3306,
        'charset': 'utf8mb4'
    }

    try:
        print("\n[1/3] 连接到MySQL服务器...")
        connection = mysql.connector.connect(**config)

        if connection.is_connected():
            db_info = connection.server_info
            print(f"    [OK] 成功连接到MySQL服务器")
            print(f"    [INFO] MySQL版本: {db_info}")

            cursor = connection.cursor()

            # 检查数据库是否已存在
            print("\n[2/3] 检查数据库是否存在...")
            cursor.execute("SHOW DATABASES LIKE 'fhb_detection'")
            result = cursor.fetchone()

            if result:
                print("    [WARNING] 数据库 'fhb_detection' 已存在")
                try:
                    choice = input("    是否删除并重新创建? (y/N): ").strip().lower()

                    if choice == 'y':
                        print("    [INFO] 删除旧数据库...")
                        cursor.execute("DROP DATABASE fhb_detection")
                        print("    [OK] 旧数据库已删除")
                    else:
                        print("    [OK] 使用现有数据库")
                        cursor.close()
                        connection.close()
                        return True
                except:
                    # 在非交互环境中，默认使用现有数据库
                    print("    [OK] 使用现有数据库")
                    cursor.close()
                    connection.close()
                    return True

            # 创建数据库
            print("\n[3/3] 创建数据库...")
            cursor.execute(
                "CREATE DATABASE fhb_detection "
                "CHARACTER SET utf8mb4 "
                "COLLATE utf8mb4_unicode_ci"
            )
            print("    [OK] 数据库 'fhb_detection' 创建成功")

            # 设置默认字符集
            cursor.execute(
                "ALTER DATABASE fhb_detection "
                "CHARACTER SET utf8mb4 "
                "COLLATE utf8mb4_unicode_ci"
            )

            # 显示数据库信息
            cursor.execute("SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = 'fhb_detection'")
            charset_info = cursor.fetchone()
            print(f"    [INFO] 字符集: {charset_info[0]}")
            print(f"    [INFO] 排序规则: {charset_info[1]}")

            cursor.close()
            connection.close()

            print("\n" + "=" * 60)
            print("数据库创建完成！(￣▽￣)／")
            print("=" * 60)
            print("\n数据库信息:")
            print("  数据库名: fhb_detection")
            print("  字符集: utf8mb4")
            print("  排序规则: utf8mb4_unicode_ci")
            print("  主机: localhost")
            print("  端口: 3306")
            print("\n下一步:")
            print("1. 等待配置文件自动更新")
            print("2. 启动后端服务: python main_complete.py")
            print("3. 数据库表会自动创建")

            return True

    except Error as e:
        print(f"\n[ERROR] MySQL错误: {e}")
        print("\n请检查:")
        print("1. MySQL服务是否正在运行")
        print("2. 用户名和密码是否正确 (root/root)")
        print("3. MySQL是否允许本地连接")
        return False

    except Exception as e:
        print(f"\n[ERROR] 未知错误: {e}")
        return False

if __name__ == "__main__":
    success = create_mysql_database()

    if success:
        print("\n[SUCCESS] 可以继续下一步了！")
    else:
        print("\n[FAILED] 数据库创建失败，请解决问题后重试")
