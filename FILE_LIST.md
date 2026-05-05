# 项目文件清单

## 核心文件

### 应用入口
- `app.py` - Flask应用主入口，路由注册
- `config.py` - 配置管理，环境变量加载

### 数据模型 (models/)
- `__init__.py` - 模型包初始化
- `database.py` - 数据库初始化和连接
- `schemas.py` - SQLAlchemy数据模型定义
  - Mistake - 错题表
  - KnowledgePoint - 知识点表
  - AnalysisReport - 分析报告表
  - Tag - 标签表
  - MistakeTag - 错题标签关联表

### 业务逻辑 (services/)
- `__init__.py` - 服务包初始化
- `claude_service.py` - Claude API集成（核心AI功能）
  - extract_question_from_image() - 图片OCR识别
  - classify_knowledge_point() - 知识点自动分类
  - generate_explanation() - 生成详细解析
  - recommend_similar_questions() - 推荐类似题目
  - analyze_weak_points() - 薄弱环节分析
- `image_service.py` - 图片处理服务
  - save_uploaded_image() - 保存上传图片
  - _create_thumbnail() - 生成缩略图
  - compress_image() - 图片压缩
- `analysis_service.py` - 数据分析统计
  - get_mistakes_statistics() - 错题统计
  - get_knowledge_point_statistics() - 知识点统计
  - get_weak_points_data() - 薄弱知识点数据
  - get_time_series_data() - 时间序列数据
  - get_difficulty_distribution() - 难度分布
- `knowledge_points.py` - 知识点分类体系
  - KNOWLEDGE_POINTS_DATA - 完整知识点数据
  - get_knowledge_points_by_grade() - 按年级获取
  - get_all_knowledge_points() - 获取所有知识点

### 路由处理 (routes/)
- `__init__.py` - 路由包初始化
- `upload.py` - 图片上传路由
  - GET /upload - 上传页面
  - POST /upload/image - 单张上传
  - POST /upload/batch - 批量上传
- `mistakes.py` - 错题管理路由
  - GET /mistakes - 错题列表
  - GET /mistakes/<id> - 错题详情
  - PUT /mistakes/<id> - 更新错题
  - DELETE /mistakes/<id> - 删除错题
  - POST /mistakes/<id>/explanation - 生成解析
  - GET /mistakes/<id>/similar - 获取类似题目
  - POST /mistakes/<id>/review - 记录复习
  - POST /mistakes/batch-delete - 批量删除
  - POST /mistakes/batch-master - 批量标记已掌握
- `analysis.py` - 分析报告路由
  - GET /analysis - 分析报告页面
  - GET /analysis/current - 当前分析
  - POST /analysis/generate - 生成报告
  - GET /analysis/<id> - 查看历史报告
  - GET /analysis/statistics - 统计数据

### 前端模板 (templates/)
- `base.html` - 基础布局模板
- `index.html` - 首页
- `upload.html` - 上传页面
- `mistake_list.html` - 错题列表
- `mistake_detail.html` - 错题详情
- `analysis.html` - 分析报告

### 静态资源 (static/)
- `css/style.css` - 全局样式表
- `js/main.js` - 通用JavaScript工具函数
- `uploads/` - 上传图片存储目录

### 数据存储 (data/)
- `mistakes.db` - SQLite数据库文件（运行时自动创建）

## 配置文件

- `.env.example` - 环境变量模板
- `.env` - 环境变量配置（需用户创建）
- `.gitignore` - Git忽略规则
- `requirements.txt` - Python依赖清单

## 文档

- `README.md` - 项目说明文档
- `QUICKSTART.md` - 快速启动指南
- `FILE_LIST.md` - 本文件，项目文件清单

## 工具脚本

- `test_setup.py` - 环境测试脚本
- `install.sh` - Linux/Mac自动安装脚本
- `install.bat` - Windows自动安装脚本

## 文件统计

- Python文件: 13个
- HTML模板: 6个
- CSS文件: 1个
- JavaScript文件: 1个
- 配置文件: 4个
- 文档文件: 3个
- 脚本文件: 3个

总计: 31个核心文件

## 代码行数估算

- Python代码: ~2000行
- HTML模板: ~800行
- CSS样式: ~600行
- JavaScript: ~200行

总计: ~3600行代码
