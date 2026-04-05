"""
测试MySQL数据库连接
作者: 哈雷酱大小姐 (￣▽￣)／
"""

import asyncio
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from db_config import async_engine, init_db, close_db
from sqlalchemy import text


async def test_mysql_connection():
    """测试MySQL数据库连接"""
    print("""
    ========================================
     测试MySQL数据库连接
     作者: 哈雷酱大小姐 (￣▽￣)／
    ========================================
    """)

    try:
        print("\n[1/4] 测试数据库连接...")
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
            print(f"    [OK] 成功连接到MySQL")
            print(f"    [INFO] MySQL版本: {version}")

        print("\n[2/4] 测试数据库访问...")
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT DATABASE()"))
            current_db = result.scalar()
            print(f"    [OK] 当前数据库: {current_db}")

            result = await conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            print(f"    [INFO] 当前表数量: {len(tables)}")

        print("\n[3/4] 初始化数据库表...")
        await init_db()
        print("    [OK] 数据库表初始化完成")

        print("\n[4/4] 验证表创建...")
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            print(f"    [OK] 创建了 {len(tables)} 个表")
            for table in tables:
                print(f"       - {table[0]}")

        print("\n" + "=" * 60)
        print("MySQL数据库配置成功！(￣▽￣)／")
        print("=" * 60)
        print("\n数据库信息:")
        print(f"  - MySQL版本: {version}")
        print(f"  - 数据库名: {current_db}")
        print(f"  - 表数量: {len(tables)}")
        print(f"  - 表名: {[t[0] for t in tables]}")
        print("\n下一步:")
        print("  启动后端服务: python main_complete.py")

        return True

    except Exception as e:
        print(f"\n[ERROR] 连接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 关闭数据库连接
        await close_db()


if __name__ == "__main__":
    success = asyncio.run(test_mysql_connection())

    if success:
        print("\n[SUCCESS] MySQL数据库配置完成，可以启动后端服务了！")
    else:
        print("\n[FAILED] 请检查错误信息并解决问题")
