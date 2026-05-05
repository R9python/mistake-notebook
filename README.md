# 初中数学错题本应用

一个基于 Flask + 硅基流动 API 的私有数学错题本应用，专为初中生设计，支持拍照上传、AI识别、知识点分类和薄弱环节分析。

## 功能特性

- 📷 **拍照上传**：支持拖拽上传和批量上传错题图片
- 🤖 **AI识别**：使用 Claude Vision API 自动提取题目文字（OCR）
- 🏷️ **智能分类**：AI自动识别知识点，覆盖初一到初三数学知识体系
- 📊 **数据分析**：生成薄弱环节分析报告，识别高错误率知识点
- 💡 **AI解析**：提供详细的解题步骤和思路分析
- 🎯 **举一反三**：推荐类似题目进行针对性练习
- 🔒 **隐私保护**：所有数据本地存储，不上传云端

## 技术栈

- **后端**：Python 3.8+ / Flask
- **前端**：HTML + CSS + JavaScript
- **数据库**：SQLite
- **AI服务**：硅基流动 API
- **图片处理**：Pillow

## 安装步骤

### 1. 克隆项目（如果从Git获取）

```bash
cd mistake-notebook
```

### 2. 创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```
ANTHROPIC_API_KEY=your_api_key_here
FLASK_SECRET_KEY=your_secret_key_here
DATABASE_PATH=data/mistakes.db
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=5242880
```

**重要**：请在 [SiliconFlow](https://cloud.siliconflow.cn/me/account/ak) 获取 API 密钥。

### 5. 初始化数据库

首次运行时会自动创建数据库和知识点数据：

```bash
python app.py
```

### 6. 访问应用

打开浏览器访问：`http://localhost:5000`

## 使用指南

### 上传错题

1. 点击"上传错题"
2. 选择年级（初一/初二/初三）
3. 拖拽或选择图片文件
4. 点击"开始上传并识别"
5. AI 自动识别题目并分类

### 查看错题

1. 点击"错题列表"
2. 使用筛选器按年级、知识点、掌握状态筛选
3. 点击错题卡片查看详情

### 错题详情

- 查看原图和题目文字
- 生成 AI 详细解析
- 获取类似题目推荐
- 标记已掌握状态
- 记录复习次数
- 添加个人笔记

### 分析报告

1. 点击"分析报告"
2. 选择年级（可选）
3. 点击"生成分析报告"
4. 查看薄弱知识点排名和学习建议

## 知识点体系

### 初一（七年级）
- 有理数、整式、一元一次方程
- 几何图形初步、相交线与平行线
- 实数、平面直角坐标系
- 二元一次方程组、不等式与不等式组
- 数据的收集与整理

### 初二（八年级）

### 初三（九年级）

## 项目结构

```
mistake-notebook/
├── app.py                 # Flask 主应用
├── config.py              # 配置管理
├── requirements.txt       # Python 依赖
├── .env                   # 环境变量（需自行创建）
├── models/                # 数据模型
│   ├── database.py
│   └── schemas.py
├── services/              # 业务逻辑
│   ├── claude_service.py  # Claude API 集成
│   ├── image_service.py   # 图片处理
│   ├── analysis_service.py # 数据分析
│   └── knowledge_points.py # 知识点体系
├── routes/                # 路由
│   ├── upload.py
│   ├── mistakes.py
│   └── analysis.py
├── static/                # 静态资源
│   ├── css/
│   ├── js/
│   └── uploads/           # 上传图片存储
├── templates/             # HTML 模板
└── data/                  # 数据库文件
```

## API 使用说明

### SiliconFlow API

API 调用示例：
参考网站：https://docs.siliconflow.cn/cn/api-reference/chat-completions/chat-completions

## 数据隐私

- ✅ 所有错题数据存储在本地 SQLite 数据库
- ✅ 图片文件保存在本地 `static/uploads` 目录
- ⚠️ 图片仅在调用 Claude API 时临时发送用于识别
- ⚠️ 不建议上传包含个人敏感信息的图片

## 常见问题

### 1. API 调用失败

- 检查 `.env` 文件中的 `API_KEY` 是否正确
- 确认网络连接正常
- 查看 API 配额是否充足

### 2. 图片识别不准确

- 确保图片清晰，文字可读
- 避免图片过大（建议 < 5MB）
- 可以手动修正识别结果

### 3. 数据库错误

- 删除 `data/mistakes.db` 重新初始化
- 检查文件权限

## 开发计划

- [ ] 复习提醒功能（基于艾宾浩斯遗忘曲线）
- [ ] 导出 PDF 错题集
- [ ] 数据备份功能
- [ ] 多用户支持
- [ ] 移动端优化

## 许可证

本项目仅供个人学习和家庭使用，不得用于商业用途。

## 联系方式

如有问题或建议，请提交 Issue。

---

**注意**
