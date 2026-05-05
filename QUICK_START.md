# 快速开始指南

## 🚀 迁移后首次启动

### 步骤 1: 安装新依赖
```bash
pip install openai
# 或重新安装所有依赖
pip install -r requirements.txt
```

### 步骤 2: 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用你喜欢的编辑器
```

在 `.env` 文件中填入：
```
SILICONFLOW_API_KEY=sk-your-actual-api-key-here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
FLASK_SECRET_KEY=your-random-secret-key
DATABASE_PATH=data/mistakes.db
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=5242880
```

### 步骤 3: 运行测试
```bash
python test_setup.py
```

预期输出：
```
✓ Python版本: 3.x.x
✓ .env 文件存在
✓ API密钥已配置
✓ openai 已安装
✓ AIService 导入成功
✓ 所有测试通过！
```

### 步骤 4: 启动应用
```bash
python app.py
```

访问: http://localhost:5000

## 📋 功能测试清单

### 基础测试
- [ ] 上传一张数学题图片
- [ ] 查看 OCR 识别结果
- [ ] 生成 AI 解析
- [ ] 推荐类似题目

### 完整测试
- [ ] 测试初一/初二/初三各年级
- [ ] 测试不同知识点分类
- [ ] 积累 10+ 道错题
- [ ] 生成薄弱点分析报告

## ⚠️ 常见问题

### 问题 1: ModuleNotFoundError: No module named 'openai'
**解决**: `pip install openai`

### 问题 2: ValueError: 请在.env文件中设置SILICONFLOW_API_KEY
**解决**: 检查 `.env` 文件是否存在且配置正确

### 问题 3: API 调用失败
**检查**:
- API 密钥是否正确
- 网络连接是否正常
- 硅基流动服务是否可用

### 问题 4: 图片识别失败
**可能原因**:
- 图片不清晰
- 图片格式不支持
- API 配额不足

**降级方案**: 系统会提示手动输入题目

## 🔄 回滚到旧版本

如果需要回滚到 Anthropic Claude:

```bash
# 1. 恢复依赖
pip uninstall openai
pip install anthropic==0.18.0

# 2. 恢复配置
# 编辑 config.py，将 SILICONFLOW_* 改回 ANTHROPIC_*

# 3. 恢复服务
# 在路由文件中将 AIService 改回 ClaudeService

# 4. 恢复环境变量
# 在 .env 中将 SILICONFLOW_API_KEY 改回 ANTHROPIC_API_KEY
```

## 📚 更多文档

- 详细迁移指南: `MIGRATION_GUIDE.md`
- 迁移总结: `MIGRATION_SUMMARY.md`
- 测试脚本: `test_setup.py`

## 🎯 关键变更速查

| 项目 | 旧值 (Anthropic) | 新值 (硅基流动) |
|------|------------------|-----------------|
| 依赖包 | anthropic | openai |
| API 密钥 | ANTHROPIC_API_KEY | SILICONFLOW_API_KEY |
| Base URL | (无) | https://api.siliconflow.cn/v1 |
| 模型 | claude-3-5-sonnet-20241022 | moonshotai/Kimi-K2-Thinking |
| 服务类 | ClaudeService | AIService |
| 服务文件 | claude_service.py | ai_service.py |

## ✅ 验证迁移成功

运行以下命令确认迁移成功：

```bash
# 检查依赖
python -c "import openai; print('✓ OpenAI SDK 已安装')"

# 检查配置
python -c "from config import Config; print('✓ 配置加载成功')"

# 检查服务
python -c "from services.ai_service import AIService; print('✓ AIService 可用')"

# 完整测试
python test_setup.py
```

全部通过即表示迁移成功！🎉
