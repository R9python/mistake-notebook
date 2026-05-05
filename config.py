import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """应用配置类"""

    # Flask配置
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

    # 数据库配置
    _BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(_BASE_DIR, os.getenv('DATABASE_PATH', 'data/mistakes.db'))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 文件上传配置
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 5242880))  # 5MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

    # AI API配置 (硅基流动)
    SILICONFLOW_API_KEY = os.getenv('SILICONFLOW_API_KEY')
    SILICONFLOW_BASE_URL = os.getenv('SILICONFLOW_BASE_URL', 'https://api.siliconflow.cn/v1')

    # Vision 模型（用于图片OCR）- 使用 Qwen2.5-VL
    AI_VISION_MODEL = os.getenv('AI_VISION_MODEL', 'Qwen/Qwen3-VL-32B-Instruct')

    # 文本模型（用于分析、推理）- 使用 DeepSeek-V3（数学推理能力强）
    AI_TEXT_MODEL = os.getenv('AI_TEXT_MODEL', 'deepseek-ai/DeepSeek-V3')

    AI_MAX_TOKENS = 4096
    AI_TIMEOUT = 30

    @staticmethod
    def validate():
        """验证必需的配置项"""
        if not Config.SILICONFLOW_API_KEY or Config.SILICONFLOW_API_KEY == 'your_siliconflow_api_key_here':
            raise ValueError("请在.env文件中设置SILICONFLOW_API_KEY")

        # 确保必要的目录存在
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
