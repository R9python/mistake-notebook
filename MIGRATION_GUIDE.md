# API 迁移指南：Anthropic Claude → 硅基流动 Kimi

## 迁移完成状态 ✅

本项目已成功从 Anthropic Claude API 迁移到硅基流动 Kimi 模型。

## 已完成的修改

### 1. 依赖包更新
- ✅ `requirements.txt`: `anthropic==0.18.0` → `openai>=1.0.0`

### 2. 配置文件更新
- ✅ `config.py`:
  - API 配置从 `ANTHROPIC_API_KEY` 改为 `SILICONFLOW_API_KEY`
  - 添加 `SILICONFLOW_BASE_URL`
  - 模型从 `claude-3-5-sonnet-20241022` 改为 `moonshotai/Kimi-K2-Thinking`
  - 配置验证方法已更新

- ✅ `.env.example`: 环境变量模板已更新

### 3. AI 服务重构
- ✅ 创建新文件 `services/ai_service.py` (替代 `claude_service.py`)
- ✅ 类名: `ClaudeService` → `AIService`
- ✅ API 调用格式: Anthropic SDK → OpenAI 兼容格式
- ✅ 图片格式: `image` source → `image_url`
- ✅ 响应解析: `content` blocks → `choices[0].message.content`
- ✅ 移除 `thinking={'type': 'adaptive'}` 参数（Kimi-K2-Thinking 自带推理能力）

### 4. 路由文件更新
- ✅ `routes/upload.py`: 导入和实例化已更新
- ✅ `routes/mistakes.py`: 导入和实例化已更新
- ✅ `routes/analysis.py`: 导入和实例化已更新

## 下一步操作

### 1. 安装新依赖
```bash
pip install openai
pip uninstall anthropic
```

或者重新安装所有依赖：
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
复制 `.env.example` 到 `.env` 并填入你的硅基流动 API 密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```
SILICONFLOW_API_KEY=your_actual_api_key_here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
FLASK_SECRET_KEY=your_secret_key_here
DATABASE_PATH=data/mistakes.db
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=5242880
```

### 3. 测试应用
```bash
python app.py
```

### 4. 功能测试清单

#### 测试 1: 图片 OCR
- [ ] 上传清晰的数学题图片
- [ ] 验证题目文字提取准确性
- [ ] 检查数学符号识别

#### 测试 2: 知识点分类
- [ ] 测试初一、初二、初三各年级题目
- [ ] 验证知识点分类准确性
- [ ] 检查难度评估合理性

#### 测试 3: AI 解析
- [ ] 生成详细解析
- [ ] 验证解题步骤完整性
- [ ] 检查 markdown 格式正确性

#### 测试 4: 推荐题目
- [ ] 生成 3 道类似题目
- [ ] 验证题目相关性
- [ ] 检查答案和提示质量

#### 测试 5: 薄弱点分析
- [ ] 积累 10-20 道错题
- [ ] 生成分析报告
- [ ] 验证薄弱点识别准确性

#### 测试 6: 错误处理
- [ ] 测试 API 密钥错误
- [ ] 测试网络超时
- [ ] 测试图片格式错误

## 技术变更详情

### API 调用格式对比

**旧格式 (Anthropic):**
```python
import anthropic
client = anthropic.Anthropic(api_key=api_key)
response = client.messages.create(
    model='claude-3-5-sonnet-20241022',
    max_tokens=2048,
    thinking={'type': 'adaptive'},
    messages=[...]
)
result = next(block.text for block in response.content if block.type == 'text')
```

**新格式 (硅基流动 Kimi):**
```python
from openai import OpenAI
client = OpenAI(api_key=api_key, base_url='https://api.siliconflow.cn/v1')
response = client.chat.completions.create(
    model='moonshotai/Kimi-K2-Thinking',
    max_tokens=2048,
    messages=[...]
)
result = response.choices[0].message.content
```

### 图片格式变更

**旧格式:**
```python
{
    'type': 'image',
    'source': {
        'type': 'base64',
        'media_type': 'image/jpeg',
        'data': base64_string
    }
}
```

**新格式:**
```python
{
    'type': 'image_url',
    'image_url': {
        'url': f'data:image/jpeg;base64,{base64_string}'
    }
}
```

## Kimi-K2-Thinking 模型优势

- ✅ 支持思维链推理（类似 Claude 的 Adaptive Thinking）
- ✅ 适合复杂数学题解析和分析任务
- ✅ 128K 上下文窗口（当前代码最大使用 4096 tokens，完全兼容）
- ✅ 支持 Vision API（图片识别）

## 回滚方案

如果需要回滚到 Anthropic Claude：

1. 恢复 `requirements.txt`: `pip install anthropic==0.18.0`
2. 恢复 `config.py` 中的 API 配置
3. 删除 `services/ai_service.py`
4. 恢复使用 `services/claude_service.py`
5. 恢复路由文件中的导入语句
6. 恢复 `.env` 文件中的 API 密钥

建议在测试前创建 git 备份：
```bash
git add .
git commit -m "Migrated from Anthropic Claude to SiliconFlow Kimi"
```

## 注意事项

1. **旧服务文件**: `services/claude_service.py` 仍然存在，可以在确认迁移成功后删除
2. **API 成本**: 硅基流动的定价可能与 Anthropic 不同，建议先小规模测试
3. **响应质量**: 建议对比测试 Kimi 和 Claude 的输出质量
4. **错误处理**: 所有方法都保留了降级方案，API 失败时会返回友好的错误信息

## 支持

如有问题，请检查：
- API 密钥是否正确配置
- 网络连接是否正常
- 硅基流动服务状态: https://siliconflow.cn
