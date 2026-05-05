"""图片处理服务"""
import os
from datetime import datetime
from PIL import Image
from werkzeug.utils import secure_filename
from config import Config


class ImageService:
    """图片处理服务"""

    @staticmethod
    def allowed_file(filename: str) -> bool:
        """检查文件扩展名是否允许"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

    @staticmethod
    def save_uploaded_image(file) -> tuple:
        """
        保存上传的图片并生成缩略图

        Args:
            file: werkzeug FileStorage对象

        Returns:
            (image_path, thumbnail_path) 相对于static目录的路径
        """
        if not file or not ImageService.allowed_file(file.filename):
            raise ValueError("不支持的文件类型")

        # 生成唯一文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_name = secure_filename(file.filename)
        name, ext = os.path.splitext(original_name)
        filename = f"{timestamp}_{name}{ext}"

        # 按年月创建目录
        year_month = datetime.now().strftime('%Y/%m')
        upload_dir = os.path.join(Config.UPLOAD_FOLDER, year_month)
        os.makedirs(upload_dir, exist_ok=True)

        # 保存原图
        image_path = os.path.join(upload_dir, filename)
        file.save(image_path)

        # 生成缩略图
        thumbnail_path = ImageService._create_thumbnail(image_path, upload_dir, filename)

        # 返回相对路径（相对于static目录）
        rel_image_path = os.path.relpath(image_path, 'static')
        rel_thumbnail_path = os.path.relpath(thumbnail_path, 'static')

        return rel_image_path, rel_thumbnail_path

    @staticmethod
    def _create_thumbnail(image_path: str, output_dir: str, filename: str) -> str:
        """
        创建缩略图

        Args:
            image_path: 原图路径
            output_dir: 输出目录
            filename: 文件名

        Returns:
            缩略图路径
        """
        name, ext = os.path.splitext(filename)
        thumbnail_filename = f"{name}_thumb{ext}"
        thumbnail_path = os.path.join(output_dir, thumbnail_filename)

        try:
            with Image.open(image_path) as img:
                # 转换RGBA为RGB（如果需要）
                if img.mode == 'RGBA':
                    img = img.convert('RGB')

                # 生成200x200缩略图（保持宽高比）
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, quality=85, optimize=True)

            return thumbnail_path

        except Exception as e:
            print(f"生成缩略图失败: {e}")
            # 如果失败，返回原图路径
            return image_path

    @staticmethod
    def compress_image(image_path: str, max_size_mb: float = 5.0) -> None:
        """
        压缩图片（如果超过指定大小）

        Args:
            image_path: 图片路径
            max_size_mb: 最大文件大小（MB）
        """
        file_size_mb = os.path.getsize(image_path) / (1024 * 1024)

        if file_size_mb <= max_size_mb:
            return

        try:
            with Image.open(image_path) as img:
                if img.mode == 'RGBA':
                    img = img.convert('RGB')

                # 逐步降低质量直到满足大小要求
                quality = 85
                while quality > 20:
                    img.save(image_path, quality=quality, optimize=True)
                    file_size_mb = os.path.getsize(image_path) / (1024 * 1024)

                    if file_size_mb <= max_size_mb:
                        break

                    quality -= 10

        except Exception as e:
            print(f"压缩图片失败: {e}")
