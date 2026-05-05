# 快速启动指南

## 第一次使用

### 1. 安装依赖

```bash
cd /home/zhy/mycode/mistake-notebook
pip install -r requirements.txt
```

### 2. 配置 API 密钥

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 Anthropic API 密钥：

```
ANTHROPIC_API_KEY=sk-ant-xxxxx  # 替换为你的真实密钥
FLASK_SECRET_KEY=your-random-secret-key-here
DATABASE_PATH=data/mistakes.db
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=5242880
```

### 3. 启动应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

## 获取 API 密钥

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册/登录账号
3. 进入 API Keys 页面
4. 创建新的 API 密钥
5. 复制密钥到 `.env` 文件

## 使用流程

### 上传第一道错题

1. 打开浏览器访问 `http://localhost:5000`
2. 点击"上传错题"
3. 选择年级（初一/初二/初三）
4. 拖拽或选择错题图片
5. 点击"开始上传并识别"
6. 等待 AI 识别完成

### 查看错题详情

1. 在首页或错题列表中点击错题卡片
2. 查看 AI 识别的题目文字（可手动修正）
3. 点击"生成解析"获取详细解题步骤
4. 点击"加载推荐"获取类似题目
5. 标记"已掌握"或记录复习

### 生成分析报告

1. 至少上传 5-10 道错题后
2. 点击"分析报告"
3. 选择年级（可选）
4. 点击"生成分析报告"
5. 查看薄弱知识点和学习建议

## 注意事项

- 首次运行会自动创建数据库和知识点数据
- 图片建议清晰、文字可读，大小 < 5MB
- API 调用需要网络连接
- 所有数据存储在本地，不会上传云端

## 故障排除

### 问题：API 调用失败

**解决方案**：
- 检查 `.env` 中的 API 密钥是否正确
- 确认网络连接正常
- 查看终端错误信息

### 问题：图片识别不准确

**解决方案**：
- 确保图片清晰
- 在错题详情页手动修正题目文字
- 重新选择知识点分类

### 问题：数据库错误

**解决方案**：
```bash
rm data/mistakes.db
python app.py  # 重新初始化
```

## 目录说明

```
mistake-notebook/
├── app.py              # 启动文件
├── config.py           # 配置
├── .env                # 环境变量（需创建）
├── models/             # 数据模型
├── services/           # 业务逻辑（AI服务）
├── routes/             # 路由处理
├── templates/          # HTML模板
├── static/             # 静态资源
│   ├── css/
│   ├── js/
│   └── uploads/        # 上传的图片
└── data/               # 数据库文件
```

## 下一步

- 上传更多错题建立题库
- 定期查看分析报告
- 针对薄弱知识点重点复习
- 使用类似题目功能举一反三

祝学习进步！📚
