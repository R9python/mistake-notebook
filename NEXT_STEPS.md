# 下一步操作指南

恭喜！初中数学错题本应用已经完成开发。以下是你需要做的下一步操作。

## 🎯 立即开始使用

### 步骤 1：安装依赖

```bash
cd /home/zhy/mycode/mistake-notebook

# 方式 1：使用自动安装脚本（推荐）
./install.sh

# 方式 2：手动安装
pip install -r requirements.txt
```

### 步骤 2：配置 API 密钥

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册/登录账号
3. 创建 API 密钥
4. 配置环境变量：

```bash
cp .env.example .env
nano .env  # 或使用其他编辑器
```

在 `.env` 文件中填入：

```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx  # 你的真实密钥
FLASK_SECRET_KEY=your-random-secret-key
DATABASE_PATH=data/mistakes.db
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=5242880
```

### 步骤 3：测试环境

```bash
python3 test_setup.py
```

确保所有测试通过。

### 步骤 4：启动应用

```bash
python3 app.py
```

访问 `http://localhost:5000`

## 📖 学习文档

建议按以下顺序阅读文档：

1. **README.md** - 了解项目概述和功能特性
2. **QUICKSTART.md** - 快速启动指南
3. **EXAMPLES.md** - 详细使用示例
4. **PROJECT_SUMMARY.md** - 技术架构和扩展建议

## 🎓 第一次使用

### 上传第一道错题

1. 准备一张数学错题图片（清晰、文字可读）
2. 点击"上传错题"
3. 选择年级（初一/初二/初三）
4. 拖拽图片到上传区域
5. 点击"开始上传并识别"
6. 查看 AI 识别结果

### 生成第一份分析报告

1. 至少上传 10-20 道错题
2. 点击"分析报告"
3. 点击"生成分析报告"
4. 查看薄弱知识点和学习建议

## 🔧 故障排��

### 问题 1：依赖安装失败

```bash
# 升级 pip
pip install --upgrade pip

# 重新安装
pip install -r requirements.txt
```

### 问题 2：API 调用失败

- 检查 `.env` 文件中的 API 密钥是否正确
- 确认网络连接正常
- 访问 [Anthropic Status](https://status.anthropic.com/) 查看服务状态

### 问题 3：数据库错误

```bash
# 删除数据库重新初始化
rm data/mistakes.db
python3 app.py
```

## 💡 使用建议

### 每日使用流程

- **放学后**：上传当天的错题（5-10 分钟）
- **晚自习**：查看 AI 解析（15-20 分钟）
- **周末**：生成分析报告，针对性复习（30-60 分钟）

### 复习策略

- 第 1 天：上传错题，查看解析
- 第 3 天：第一次复习
- 第 7 天：第二次复习
- 第 15 天：第三次复习
- 第 30 天：最后复习，标记已掌握

## 🚀 扩展功能

如果你想添加新功能，可以参考：

- **PROJECT_SUMMARY.md** - 扩展建议章节
- **FILE_LIST.md** - 了解代码结构
- 代码注释 - 每个文件都有详细注释

## 📊 监控使用情况

### 查看 API 使用量

访问 [Anthropic Console](https://console.anthropic.com/) 查看：
- API 调用次数
- Token 使用量
- 费用统计

### 数据备份

定期备份数据：

```bash
# 备份数据库
cp data/mistakes.db data/mistakes_backup_$(date +%Y%m%d).db

# 备份图片
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz static/uploads/
```

## 🎯 学习目标

建议设定以下目标：

- **短期**（1周）：熟悉应用功能，上传 20+ 道错题
- **中期**（1月）：掌握 80% 的错题，生成 4 份分析报告
- **长期**（1学期）：清空所有未掌握错题，数学成绩提升

## 📞 获取帮助

如果遇到问题：

1. 查看文档（README.md、QUICKSTART.md、EXAMPLES.md）
2. 运行测试脚本（test_setup.py）
3. 查看应用日志（终端输出）
4. 检查 API 密钥和网络连接

## ✅ 检查清单

在开始使用前，确保：

- [ ] 已安装所有依赖
- [ ] 已配置 API 密钥
- [ ] 测试脚本全部通过
- [ ] 应用可以正常启动
- [ ] 可以访问 http://localhost:5000
- [ ] 已阅读 README.md 和 QUICKSTART.md

## 🎉 开始使用

一切准备就绪！现在可以开始使用初中数学错题本应用了。

**祝学习进步！** 📚🎓

---

*如有问题，请参考文档或重新运行 test_setup.py 检查环境。*
