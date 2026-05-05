"""测试脚本 - 验证应用基本功能"""
import os
import sys

def check_environment():
    """检查环境配置"""
    print("=" * 50)
    print("环境检查")
    print("=" * 50)

    # 检查Python版本
    print(f"✓ Python版本: {sys.version.split()[0]}")

    # 检查.env文件
    if os.path.exists('.env'):
        print("✓ .env 文件存在")
        with open('.env', 'r') as f:
            content = f.read()
            if 'SILICONFLOW_API_KEY' in content and 'your_siliconflow_api_key_here' not in content:
                print("✓ API密钥已配置")
            else:
                print("✗ 请在.env文件中配置SILICONFLOW_API_KEY")
                return False
    else:
        print("✗ .env 文件不存在，请复制.env.example并配置")
        return False

    # 检查必要目录
    dirs = ['data', 'static/uploads', 'static/css', 'static/js', 'templates']
    for d in dirs:
        if os.path.exists(d):
            print(f"✓ 目录存在: {d}")
        else:
            print(f"✗ 目录缺失: {d}")
            return False

    return True

def check_dependencies():
    """检查依赖包"""
    print("\n" + "=" * 50)
    print("依赖检查")
    print("=" * 50)

    required = ['flask', 'openai', 'pillow', 'sqlalchemy', 'dotenv']
    missing = []

    for package in required:
        try:
            if package == 'pillow':
                __import__('PIL')
            elif package == 'dotenv':
                __import__('dotenv')
            else:
                __import__(package)
            print(f"✓ {package} 已安装")
        except ImportError:
            print(f"✗ {package} 未安装")
            missing.append(package)

    if missing:
        print(f"\n请运行: pip install {' '.join(missing)}")
        return False

    return True

def test_imports():
    """测试模块导入"""
    print("\n" + "=" * 50)
    print("模块导入测试")
    print("=" * 50)

    try:
        from config import Config
        print("✓ config.py 导入成功")

        from models import db, Mistake, KnowledgePoint
        print("✓ models 导入成功")

        from services.knowledge_points import get_all_knowledge_points
        points = get_all_knowledge_points()
        print(f"✓ 知识点数据加载成功 (共{len(points)}个知识点)")

        from services.ai_service import AIService
        print("✓ AIService 导入成功")

        from services.image_service import ImageService
        print("✓ ImageService 导入成功")

        from services.analysis_service import AnalysisService
        print("✓ AnalysisService 导入成功")

        return True

    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_database():
    """测试数据库初始化"""
    print("\n" + "=" * 50)
    print("数据库测试")
    print("=" * 50)

    try:
        from flask import Flask
        from models.database import init_db
        from models import KnowledgePoint

        app = Flask(__name__)
        db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'mistakes.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        init_db(app)

        with app.app_context():
            count = KnowledgePoint.query.count()
            print(f"✓ 数据库初始化成功")
            print(f"✓ 知识点数据已加载 (共{count}条)")

        return True

    except Exception as e:
        print(f"✗ 数据库测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("\n初中数学错题本应用 - 环境测试\n")

    results = []

    # 环境检查
    results.append(("环境配置", check_environment()))

    # 依赖检查
    results.append(("依赖包", check_dependencies()))

    # 模块导入
    results.append(("模块导入", test_imports()))

    # 数据库测试
    results.append(("数据库", test_database()))

    # 总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)

    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("✓ 所有测试通过！可以启动应用了。")
        print("\n运行命令: python app.py")
        print("访问地址: http://localhost:5000")
    else:
        print("✗ 部分测试失败，请检查上述错误信息。")
        print("\n常见问题:")
        print("1. 缺少依赖: pip install -r requirements.txt")
        print("2. 未配置API密钥: 编辑.env文件")
        print("3. 目录权限问题: 检查文件夹权限")
    print("=" * 50)

if __name__ == '__main__':
    main()
