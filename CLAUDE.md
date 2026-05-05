## 项目概述

初中数学错题本 — 基于 Flask 的 Web 应用，供学生拍照上传数学错题和经典题，由 AI 自动提取题目、分类知识点并追踪薄弱环节。所有数据本地存储（SQLite），界面和 AI 提示词均为中文。

**核心功能：**
- 错题本：记录做错的题目，用于针对性复习
- 经典题库：收集典型题目，用于系统性学习
- AI 解析：自动生成详细解题步骤和易错点分析
- 标签管理：灵活的标签系统，支持按题型、知识点、错误原因分类
- 薄弱知识分析：基于标签统计，AI 生成个性化学习建议

## 常用命令

```bash
# 环境搭建
python -m venv venv && source venv/bin/activate  # Linux/Mac
# Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # 然后填写 SILICONFLOW_API_KEY

# 启动应用（首次运行自动创建数据库并填充知识点数据）
python app.py  # 访问 http://localhost:5000

# 在虚拟环境启动应用
source venv/bin/activate && python app.py

# 验证环境、依赖、模块导入和数据库
python test_setup.py

# 直接操作数据库（需在虚拟环境中）
source venv/bin/activate && python3 << 'EOF'
from app import app
from models import db, Mistake, KnowledgePoint
with app.app_context():
    # 查询示例
    mistakes = Mistake.query.all()
    # 修改示例
    mistake = db.session.get(Mistake, 1)
    mistake.review_count = 0
    db.session.commit()
EOF
```

## 项目结构

```
mistake-notebook/
├── app.py                 # Flask 主应用
├── config.py              # 配置管理
├── requirements.txt       # Python 依赖
├── .env                   # 环境变量（需自行创建）
├── models/                # 数据模型
│   ├── database.py        # 数据库初始化 + 知识点自动填充
│   └── schemas.py         # SQLAlchemy 模型定义
├── services/              # 业务逻辑
│   ├── ai_service.py      # 硅基流动 API 集成（OpenAI 兼容客户端）
│   ├── claude_service.py  # Claude API 集成（备用）
│   ├── image_service.py   # 图片处理（保存/缩略图/压缩）
│   ├── analysis_service.py # 数据分析（统计查询）
│   └── knowledge_points.py # 知识点静态数据（北师大版初一）
├── routes/                # 路由 Blueprint
│   ├── upload.py          # /upload/ — 错题上传及 AI 处理
│   ├── mistakes.py        # /mistakes/ — 错题增删改查
│   ├── classics.py        # /classics/ — 经典题增删改查及上传
│   ├── analysis.py        # /analysis/ — 统计与报告
│   └── tags.py            # /tags/ — 标签管理
├── static/
│   ├── css/style.css      # 全局样式（微软 Fluent 配色）
│   ├── js/main.js         # 通用工具函数（Toast、防抖、标签选择器）
│   └── uploads/           # 上传图片（按 YYYY/MM/ 组织）
├── templates/
│   ├── base.html          # 基础模板（导航栏/页脚）
│   ├── index.html         # 首页（概览，ECharts 可视化）
│   ├── upload.html        # 错题上传页
│   ├── mistake_list.html  # 错题列表（支持按标签筛选）
│   ├── mistake_detail.html # 错题详情
│   ├── classic_upload.html # 经典题上传页
│   ├── classic_list.html  # 经典题列表
│   ├── classic_detail.html # 经典题详情
│   ├── tags.html          # 标签管理页
│   └── analysis.html      # 分析报告（marked.js 渲染）
├── data/                  # SQLite 数据库文件
└── test_math_question.jpg # 测试用图片
```

## 架构

### 请求流程

`app.py`（Flask 入口）→ 注册五个 Blueprint（`routes/`）→ 各路由调用 `services/` 中的服务 → 通过 `models/` 中的 SQLAlchemy 模型持久化数据。

### AI 集成（`services/ai_service.py`）

- 使用**硅基流动 API**（OpenAI 兼容客户端）
- 在 `config.py` 中配置两个模型，均可通过 `.env` 覆盖：
  - **视觉模型**（`AI_VISION_MODEL`，默认 `Qwen/Qwen2.5-VL-32B-Instruct`）— 图片 OCR 提取题目
  - **文本模型**（`AI_TEXT_MODEL`，当前实际使用 `deepseek-ai/DeepSeek-V3`，代码默认值为 `Qwen/Qwen2.5-72B-Instruct`）— 知识点分类、解析生成、类似题推荐、基于标签的薄弱知识分析
- 所有 AI 响应预期为 JSON 格式（有时包裹在 markdown 代码块中）。`AIService._extract_json()` 会去除 `<think>` 标签和代码围栏后再解析，并对裸反斜杠（LaTeX 命令）进行多轮容错修复。
- 几何题检测（`_is_geometry_question()`）：解析时自动在顶部插入原题图片供学生对照。
- 每个 AI 方法都有优雅降级路径，失败时返回默认/空结果。
- **标签分析**：`analyze_weak_tags()` 方法使用专门的教学专家提示词，分析学生的薄弱标签并给出短期/长期学习建议

### 核心模块

| 层级 | 模块 | 职责 |
|------|------|------|
| 数据模型 | `models/schemas.py` | SQLAlchemy 模型：`Mistake`、`ClassicQuestion`、`KnowledgePoint`（支持层级自引用）、`AnalysisReport`、`Tag`、`MistakeTag`、`ClassicQuestionTag` |
| 数据模型 | `models/database.py` | 数据库初始化 + 表为空时自动从 `services/knowledge_points.py` 填充知识点 |
| 服务 | `services/ai_service.py` | `AIService` 类 — 所有 AI API 调用（OCR、分类、解析、推荐、标签分析） |
| 服务 | `services/image_service.py` | `ImageService` — 保存上传文件、生成 200×200 缩略图、压缩超大图片 |
| 服务 | `services/analysis_service.py` | `AnalysisService` — 统计查询（时间序列、难度分布、基于标签的薄弱知识统计） |
| 服务 | `services/knowledge_points.py` | 静态知识点数据，当前仅含初一（7年级）北师大版课程 |
| 路由 | `routes/upload.py` | `/upload/` — 错题单张和批量图片上传及 AI 处理，传入 `kp_data` 供级联选择，支持标签关联 |
| 路由 | `routes/mistakes.py` | `/mistakes/` — 错题列表（支持按标签筛选）、详情、AI 解析、类似题、复习记录、批量操作 |
| 路由 | `routes/classics.py` | `/classics/` — 经典题上传、列表、详情、AI 解析、复习记录、批量操作（无类似题推荐） |
| 路由 | `routes/analysis.py` | `/analysis/` — 统计数据接口、基于标签的 AI 分析报告生成 |
| 路由 | `routes/tags.py` | `/tags/` — 标签的增删改查接口和管理页面 |

### 数据模型要点

- `grade_level` 以整数存储：7、8、9（对应初一/初二/初三）
- `Mistake` 和 `ClassicQuestion` 模型结构相似，但用途不同：
  - `Mistake`：记录做错的题目，包含类似题推荐功能
  - `ClassicQuestion`：收集典型题目，无类似题推荐
- `Mistake.source`：字符串，记录错题来源（已废弃，改用标签系统）
- `Mistake.tags` 和 `ClassicQuestion.tags`：多对多关系，分别通过 `MistakeTag` 和 `ClassicQuestionTag` 关联表连接到 `Tag` 表
- `Tag` 表：存储标签（id, name, color），支持自定义颜色，错题和经典题共享标签系统
- `Mistake.similar_questions` 和 `AnalysisReport.weak_points`/`statistics` 均为 JSON 字符串，存储在 Text 列中
- 上传图片按 `static/uploads/YYYY/MM/` 组织，缩略图以 `_thumb` 为后缀

### 配置

所有配置在 `config.py` 中，通过 `python-dotenv` 从 `.env` 加载。启动时调用 `Config.validate()`，若缺少 `SILICONFLOW_API_KEY` 将 `exit(1)` 终止。

## 前端开发要点

### 模板系统（Jinja2）

- 所有模板在 `templates/` 目录，继承自 `base.html`
- 使用 `{% extends "base.html" %}` 和 `{% block %}` 结构
- 前端数据通过 `{{ variable | tojson }}` 传递给 JavaScript
- 导航栏高亮：`base.html` 中用 `request.path.startswith(...)` 判断当前页，给对应 `<a>` 加 `active` 类

### 样式规范（`static/css/style.css`）

- 配色系统：微软 Fluent UI 风格，变量定义在 `:root` 中（`--ms-blue`、`--ms-green`、`--ms-red` 等）
- 按钮类：`.btn-primary`（蓝）、`.btn-secondary`（灰）、`.btn-danger`（红）、`.btn-review`（浅绿）
- 标签类：`.knowledge-tag`（知识点，蓝底白字）、`.difficulty-tag`（难度，颜色按难度变化）、`.tag-item`（错题标签，彩色圆角）
- 标签选择器：`.tag-selector`（容器）、`.tag-selected-item`（已选标签）、`.tag-dropdown-item`（下拉选项）
- 标签筛选栏：`.tag-filter-bar`（快速筛选容器）、`.tag-filter-item`（标签按钮）
- 导航高亮：`.nav-menu a.active`（白色半透明背景 + 底部白线 + 加粗）
- Toast 通知：`.toast`、`.toast-success`、`.toast-error`、`.toast-info`（右下角弹出，2.8s 后消失）
- 响应式：使用 flexbox 和 grid，`@media (max-width: 768px)` 处理移动端

### JavaScript 约定

- 使用原生 JavaScript（无框架）
- 通用工具在 `static/js/main.js`：`showToast(message, type)`、`debounce()`、`throttle()`、`TagSelector` 类
- **Toast 通知系统**：所有用户反馈使用 `showToast()` 而非阻塞式 `alert()`，提供更好的用户体验
- `TagSelector` 类：标签选择组件，支持多选、搜索、新建标签，使用方法见上传页和详情页
- **ECharts 5.4.3**：用于首页薄弱知识分布的饼图可视化
- **marked.js**：用于分析报告页面的 markdown 渲染，支持富文本格式
- **MathJax 3.x**：用于数学公式渲染（LaTeX 语法），在错题和经典题详情页加载
- 公式包裹规则：`$...$` 行内公式，`$$...$$` 块级公式
- `prepareForMathJax(text)`：自动检测 LaTeX 命令并按行补上 `$` 包裹；将中文填空下划线转为 `\underline{\qquad}`

### 标签选择实现

上传页和详情页使用 `TagSelector` 类实现标签多选：
- 初始化：`new TagSelector('containerId', {placeholder, maxTags, allowCreate})`
- 获取选中标签：`tagSelector.getSelectedTags()` 返回标签 ID 数组
- 设置标签：`tagSelector.setSelectedTags([id1, id2, ...])`
- 支持搜索、新建标签（输入后按回车）、删除已选标签

### 错题列表筛选逻辑（`routes/mistakes.py`）

```python
# 支持按年级、学期、知识点、标签、掌握状态筛选
query = Mistake.query
if tag_id:
    query = query.join(Mistake.tags).filter(Tag.id == tag_id)
mistakes = query.order_by(Mistake.created_at.desc()).all()
```

- 列表页不再按来源分组，改为按创建时间倒序显示
- 支持标签快速筛选栏（彩色标签按钮）
- 同一路由同时构建 `kp_data`（知识点级联数据）和 `tags`（所有标签）传给模板

## 数据库操作注意事项

### 知识点数据

- 当前仅保留 7 年级（初一）知识点，8/9 年级已删除
- 知识点结构：`grade_level`（7）、`semester`（1=上学期，2=下学期）、`chapter`（第一章、第二章...）
- 北师大版教材体系，数据源在 `services/knowledge_points.py`

### 常见查询模式

```python
# 按年级和学期查询知识点
kps = KnowledgePoint.query.filter_by(grade_level=7, semester=1).all()

# 查询错题及关联知识点
mistake = db.session.get(Mistake, mistake_id)
kp_name = mistake.knowledge_point.name if mistake.knowledge_point else '未分类'

# 查询错题的标签
tags = mistake.tags  # 返回 Tag 对象列表
tag_names = [tag.name for tag in mistake.tags]

# 更新错题字段
mistake.knowledge_point_id = new_kp_id
db.session.commit()

# 更新错题标签（替换所有标签）
mistake.tags = Tag.query.filter(Tag.id.in_([1, 2, 3])).all()
db.session.commit()

# 按标签筛选错题
mistakes = Mistake.query.join(Mistake.tags).filter(Tag.id == tag_id).all()
```

### AI 分类结果处理

AI 返回的知识点名称可能带括号描述（如 "有理数 (数与代数)"），需要用 `split('(')[0].strip()` 提取纯名称再匹配数据库。

### AI 解析存储格式

`Mistake.ai_explanation` 存储的是**HTML**（由 markdown 转换而来），渲染时直接 `{{ mistake.ai_explanation | safe }}`。历史数据若存的是原始 markdown，路由会在详情页加载时自动转换并回写数据库。

## 用户界面术语

- "年级" 显示为：初一/初二/初三
- "学期" 显示为：上学期/下学期
- "课本目录" 对应数据库的 `category` 字段
- "知识内容" 对应数据库的 `description` 字段
- "点妹的笔记" 是笔记区域的标题（用户自定义，对应 `Mistake.notes` 和 `ClassicQuestion.notes`）
- "错题标签" / "经典题标签" 对应 `tags` 关系，支持多个标签（如：找规律、三角形全等、动点问题）
- "概览" 是首页标题，展示错题总数、经典题总数、掌握率和薄弱知识分布
- "薄弱知识分布" 基于标签统计未掌握的错题，使用 ECharts 饼图展示

## 标签系统

### 数据迁移

首次启用标签系统时，运行 `python migrate_source_to_tags.py` 将现有的 `Mistake.source` 数据迁移到标签系统：
- 提取所有唯一的 source 值
- 为每个 source 创建对应的 Tag
- 建立 Mistake 和 Tag 的多对多关联
- 保留原 source 字段作为备份

### 标签管理

- 访问 `/tags` 进入标签管理页面
- 支持新建、编辑、删除标签
- 每个标签可设置自定义颜色
- 删除标签前会检查是否有错题使用，有使用的标签无法删除
- 标签管理页显示每个标签的使用次数

### 标签使用

- 上传错题或经典题时可选择多个标签（最多 5 个）
- 错题/经典题详情页可编辑标签
- 错题/经典题列表页支持按标签筛选
- 标签快速筛选栏提供一键筛选功能
- 首页"薄弱知识分布"展示未掌握错题的标签统计（前 10 个）
- 分析报告基于标签生成个性化学习建议

## 首页数据可视化

### 概览统计

首页展示四个核心指标：
- **错题总数**：`Mistake.query.count()`
- **经典题总数**：`ClassicQuestion.query.count()`
- **掌握率**：已掌握错题数 / 总错题数
- **待复习**：未掌握的错题数

### 薄弱知识分布（ECharts 饼图）

使用 ECharts 5.4.3 展示未掌握错题的标签分布：

```python
# 查询逻辑（app.py）
tag_stats = db.session.query(
    Tag.id, Tag.name, Tag.color,
    func.count(MistakeTag.mistake_id).label('count')
).join(MistakeTag).join(Mistake).filter(
    Mistake.is_mastered == False
).group_by(Tag.id).order_by(
    func.count(MistakeTag.mistake_id).desc()
).limit(10).all()
```

**图表配置：**
- 类型：环形饼图（`radius: ['40%', '70%']`）
- 标签：外部显示，带引导线（`labelLine`）
- 颜色：使用标签自定义颜色
- 交互：点击标签跳转到对应的错题筛选页

## 分析报告系统

### 数据统计（`services/analysis_service.py`）

`get_weak_tags_data()` 方法查询薄弱标签：

```python
query = db.session.query(
    Tag.id, Tag.name, Tag.color,
    func.count(MistakeTag.mistake_id).label('count'),
    func.sum(func.cast(Mistake.is_mastered, db.Integer)).label('mastered_count')
).select_from(Tag).join(
    MistakeTag, Tag.id == MistakeTag.tag_id
).join(
    Mistake, MistakeTag.mistake_id == Mistake.id
).filter(Mistake.is_mastered == False).group_by(Tag.id)
```

**注意**：使用 `.select_from(Tag)` 明确指定起始表，避免 SQLAlchemy 连接歧义错误。

### AI 分析（`services/ai_service.py`）

`analyze_weak_tags()` 方法使用专门的教学专家提示词：

**系统角色：**
```
你是一位经验丰富的初中数学教学专家，擅长分析学生的学习问题并给出针对性建议。
你的分析特点：
1. 能够识别标签背后的深层问题
2. 善于发现标签之间的关联性
3. 给出的建议具体可行，分短期和长期目标
4. 语言亲切，鼓励学生，避免打击自信心
```

**分析维度：**
1. 标签分类（知识点类、题型类、错误原因类）
2. 深层问题分析（为什么这些标签出现频繁）
3. 优先级判断（哪些标签最需要优先解决）
4. 学习建议（短期目标、长期目标、学习方法）

### 报告渲染（`templates/analysis.html`）

使用 **marked.js** 将 AI 返回的 markdown 转换为富文本 HTML：

```javascript
const analysisHtml = marked.parse(analysisMarkdown);
document.getElementById('analysisText').innerHTML = analysisHtml;
```

**样式增强：**
- 标题层级：`h3`、`h4` 使用不同颜色和字号
- 列表：`ul`、`ol` 带左边框和缩进
- 强调：`strong` 使用主题蓝色
- 代码：`code` 浅灰背景
- 引用：`blockquote` 左侧蓝色边框

## Toast 通知系统

全应用已替换阻塞式 `alert()` 为非阻塞式 `showToast()`：

**使用方法：**
```javascript
showToast('操作成功', 'success');  // 绿色
showToast('操作失败', 'error');    // 红色
showToast('提示信息', 'info');     // 蓝色
```

**特点：**
- 右下角弹出，2.8 秒后自动消失
- 不阻塞用户操作
- 支持多个通知堆叠
- 平滑的淡入淡出动画

**已替换的场景：**
- 表单验证错误
- 上传成功/失败
- 保存操作反馈
- 删除确认后的结果
- 批量操作结果
- 复习记录保存

## 经典题库功能

### 设计理念

经典题库与错题本并行，但用途不同：
- **错题本**：记录做错的题目，用于针对性复习，包含"类似题推荐"功能
- **经典题库**：收集典型题目，用于系统性学习，不需要类似题推荐

### 数据模型

`ClassicQuestion` 模型与 `Mistake` 结构相似：
- 共享字段：`image_path`、`question_text`、`knowledge_point_id`、`grade_level`、`difficulty`、`ai_explanation`、`notes`、`is_mastered`、`review_count`
- 移除字段：`similar_questions`（经典题不需要）
- 独立关联表：`ClassicQuestionTag`（与错题标签系统隔离）

### 路由设计

`routes/classics.py` 包含完整的 CRUD 和上传功能：
- `/classics/upload` - 上传页面和处理
- `/classics/` - 列表页（支持筛选）
- `/classics/<id>` - 详情页
- `/classics/<id>/explanation` - AI 解析
- `/classics/<id>/review` - 复习记录
- `/classics/batch-*` - 批量操作

### 模板文件

- `classic_upload.html` - 基于 `upload.html`，修改标题和路径
- `classic_list.html` - 基于 `mistake_list.html`，修改变量名
- `classic_detail.html` - 基于 `mistake_detail.html`，**移除类似题推荐区块**

### 导航集成

`base.html` 导航栏顺序：
1. 首页
2. 上传错题
3. 错题列表
4. **经典题库**（新增）
5. 分析报告
6. 标签管理

## 测试

- `test_math_question.jpg` 是用来测试上传功能的图片
- `test_setup.py` 验证环境、依赖、模块导入和数据库连接
- `migrate_source_to_tags.py` 数据迁移脚本，将 source 字段迁移到标签系统

## 批量文件操作安全规范

### ⚠️ 重要教训

在 2026-05-06 的开发过程中，发生了一次严重的文件清空事故，导致 4 个模板文件被破坏。以下是经验教训和安全规范。

### 事故回顾

**错误操作：**
使用 sed 批量替换 JavaScript 代码中的 alert 为 showToast：
```bash
sed -i "s/if (ids.length === 0) { alert('请先选择错题'); return; }/.../" mistake_list.html
```

**问题原因：**
1. `{}` 在 shell 中是特殊字符，可能被错误解释
2. JavaScript 代码包含大量特殊字符（括号、分号、引号）
3. sed 正则匹配失败时，`-i` 参数会清空文件
4. 没有备份机制，没有 git 版本控制
5. 没有在单个文件上测试就批量执行

**后果：**
- 清空了 mistake_list.html、classic_list.html、tags.html、mistake_detail.html
- 导致应用无法访问，用户非常着急
- 花费大量时间从记忆中重建文件

### 安全操作规范

#### 方案 A：使用 Edit 工具（最安全，推荐）

```
对于复杂的代码替换，使用 Edit 工具逐个文件精确修改
- 优点：安全可控，可以精确匹配上下文
- 缺点：速度较慢
- 适用：涉及特殊字符、复杂逻辑的替换
```

#### 方案 B：谨慎使用 sed（需要严格测试）

```bash
# 1. 先测试输出（不修改文件）
sed "s/alert/showToast/g" file.html | head -20

# 2. 创建备份后再修改
sed -i.bak "s/alert/showToast/g" file.html

# 3. 验证结果
diff file.html file.html.bak
wc -l file.html file.html.bak

# 4. 确认无误后删除备份
rm file.html.bak

# 5. 避免在 sed 中使用复杂的 JavaScript 代码
#    特别是包含 {} () ; 等特殊字符的代码
```

#### 方案 C：使用 Python 脚本（更可控）

```python
import re

# 读取文件
with open('file.html', 'r') as f:
    content = f.read()

# 替换（可以先打印预览）
new_content = content.replace("alert('", "showToast('")
print(f"将进行 {content.count(\"alert('\")} 处replacements")

# 确认后再写入
with open('file.html', 'w') as f:
    f.write(new_content)
```

#### 方案 D：使用 git 版本控制（强烈推荐）

```bash
# 初始化 git 仓库
git init
git add .
git commit -m "Initial commit"

# 批量操作前先提交
git add -A
git commit -m "Before batch replace"

# 执行批量操作
sed -i "s/alert/showToast/g" *.html

# 检查变更
git diff
git status

# 如果出错，立即回滚
git checkout .
```

### 操作检查清单

在执行批量文件操作前，必须确认：

- [ ] 是否有备份机制（git 或 .bak 文件）？
- [ ] 是否在单个文件上测试过？
- [ ] 是否检查了命令中的特殊字符？
- [ ] 是否可以用更安全的工具（Edit）替代？
- [ ] 操作后是否验证文件完整性（wc -l）？
- [ ] 是否有回滚方案？

### 文件完整性验证

批量操作后立即检查：

```bash
# 检查所有模板文件行数
for file in templates/*.html; do
    lines=$(wc -l < "$file")
    if [ "$lines" -lt 10 ]; then
        echo "⚠️ $(basename $file): $lines 行 - 可能有问题"
    else
        echo "✓ $(basename $file): $lines 行"
    fi
done

# 检查文件是否为空
find templates -name "*.html" -size 0
```

### 核心原则

1. **安全第一**：涉及批量文件操作时，必须有备份机制
2. **测试先行**：在生产数据上操作前，先在测试环境验证
3. **渐进式操作**：先单个文件，再批量；先测试，再执行
4. **工具选择**：复杂替换用专门工具（Edit）比 shell 命令更安全
5. **版本控制**：项目应该使用 git，这样可以随时回滚
6. **立即验证**：操作后立即检查文件完整性
7. **谨慎使用 -i**：sed/awk 的原地修改参数要格外小心

**记住：在处理用户重要数据时，必须极度谨慎，宁可慢一点，也要确保安全。**

