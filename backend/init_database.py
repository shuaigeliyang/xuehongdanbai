"""
数据库初始化脚本
作者: 哈雷酱大小姐 (￣▽￣)／
用于创建数据库表和初始数据
"""

import asyncio
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from db_config import init_db, close_db
from database import User, PredictionRecord
from auth import AuthService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


async def create_admin_user():
    """创建默认管理员用户"""
    from db_config import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        # 检查是否已存在admin用户
        result = await session.execute(select(User).where(User.username == "admin"))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("✓ 管理员用户已存在，跳过创建")
            return

        # 创建管理员用户
        hashed_password = AuthService.get_password_hash("admin123")
        admin_user = User(
            username="admin",
            email="admin@hairechan.tech",
            hashed_password=hashed_password,
            full_name="系统管理员",
            role="admin",
            is_active=True
        )

        session.add(admin_user)
        await session.commit()

        print("✓ 管理员用户创建成功")
        print("  用户名: admin")
        print("  密码: admin123")
        print("  请在生产环境中修改默认密码！")


async def main():
    """主函数"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║        血浆游离血红蛋白检测系统 - 数据库初始化                ║
    ║                                                                ║
    ║        作者: 哈雷酱大小姐 (￣▽￣)／                           ║
    ║                                                                ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    try:
        # 初始化数据库表
        print("\n[1/2] 初始化数据库表...")
        await init_db()
        print("    ✓ 数据库表创建成功")

        # 创建默认管理员用户
        print("\n[2/2] 创建默认管理员用户...")
        await create_admin_user()

        print("\n" + "=" * 60)
        print("数据库初始化完成！(￣▽￣)／")
        print("=" * 60)

        # 显示数据库文件位置
        db_file = Path(__file__).parent / "fhb_detection.db"
        if db_file.exists():
            print(f"\n数据库文件位置: {db_file}")
            print(f"数据库文件大小: {db_file.stat().st_size} 字节")

        print("\n下一步：")
        print("1. 启动后端服务: python main_complete.py")
        print("2. 访问API文档: http://localhost:8000/docs")
        print("3. 使用管理员账号登录 (admin/admin123)")
        print("\n注意：请记得在生产环境中修改默认密码！")

    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 关闭数据库连接
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
