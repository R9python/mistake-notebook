"""AI API服务 - 核心AI功能 (硅基流动 Kimi)"""
from openai import OpenAI
import base64
import json
import re
import logging
from config import Config
from services.knowledge_points import get_knowledge_points_by_grade, get_all_knowledge_points

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIService:
    """AI API集成服务 (使用硅基流动 Kimi 模型)"""

    @staticmethod
    def _extract_json(text: str):
        """从AI响应中提取JSON，处理markdown代码块包裹的情况"""
        if not text:
            return None
        # 去除可能的思维链内容（<think>...</think>标签）
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        # 尝试提取 ```json ... ``` 或 ``` ... ``` 中的内容
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()
        # 预处理：将 JSON 合法转义但实为 LaTeX 命令的字符还原
        # \f(\x0c) → \\frac, \b(\x08) → \\beta 等情况：先在原始文本层面修复
        text = text.replace('\\f', '\\\\f').replace('\\b', '\\\\b').replace('\\t', '\\\\t').replace('\\n', '\\n')
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 修复1：裸反斜杠（LaTeX \frac 等未转义）
            fixed = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', text)
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                # 修复2：冒号后缺少左引号，如 "key": value" → "key": "value"
                fixed2 = re.sub(r':\s*([^"\s\[\]{},][^,\n\]]*?")', r': "\1', fixed)
                try:
                    return json.loads(fixed2)
                except json.JSONDecodeError:
                    return None

    def __init__(self):
        self.client = OpenAI(
            api_key=Config.SILICONFLOW_API_KEY,
            base_url=Config.SILICONFLOW_BASE_URL
        )
        self.vision_model = Config.AI_VISION_MODEL  # 图片识别用
        self.text_model = Config.AI_TEXT_MODEL      # 文本分析用

    def extract_question_from_image(self, image_path: str, grade_level: int) -> dict:
        """
        从图片中提取题目文字

        Args:
            image_path: 图片路径
            grade_level: 年级 (7/8/9)

        Returns:
            {
                'question_text': str,  # 题目文字
                'student_answer': str  # 学生的错误解答（如果有）
            }
        """
        # 读取图片并转为base64
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        # 根据图片类型确定media_type
        if image_path.lower().endswith('.png'):
            media_type = 'image/png'
        elif image_path.lower().endswith(('.jpg', '.jpeg')):
            media_type = 'image/jpeg'
        elif image_path.lower().endswith('.webp'):
            media_type = 'image/webp'
        else:
            media_type = 'image/jpeg'

        prompt = f"""请仔细分析这张初{grade_level - 6}数学错题图片，提取以下信息：

1. 完整的题目文字（包括题干、问题、选项等）
2. 学生的解答过程（如果图片中有手写或打印的解答）

请以JSON格式返回：
{{
    "question_text": "完整题目文字",
    "student_answer": "学生的解答过程（如果没有则为空字符串）"
}}

注意：
- 准确识别数学符号、公式、图形描述
- 保持题目的原始格式和结构
- 如果有多个小题，请全部提取"""

        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,  # 使用 Vision 模型
                max_tokens=2048,
                messages=[{
                    'role': 'user',
                    'content': [
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:{media_type};base64,{image_data}'
                            }
                        },
                        {'type': 'text', 'text': prompt}
                    ]
                }]
            )

            # 提取文本响应
            result_text = response.choices[0].message.content

            # 解析JSON（处理可能的markdown包裹）
            result = self._extract_json(result_text)
            return result

        except Exception as e:
            logger.error(f"图片识别失败: {type(e).__name__}: {e}", exc_info=True)
            # 降级方案：返回空结果，允许用户手动输入
            return {
                'question_text': '',
                'student_answer': '',
                'error': str(e)
            }

    def classify_knowledge_point(self, question_text: str, grade_level: int) -> dict:
        """
        自动分类知识点

        Args:
            question_text: 题目文字
            grade_level: 年级 (7/8/9)

        Returns:
            {
                'primary_point': str,      # 主要知识点名称
                'secondary_points': list,  # 次要知识点列表
                'difficulty': str,         # 难度 (easy/medium/hard)
                'reasoning': str           # 判断理由
            }
        """
        # 获取该年级的知识点列表
        knowledge_points = get_knowledge_points_by_grade(grade_level)

        # 构建知识点列表文本
        kp_text = "\n".join([
            f"- {kp['name']} ({kp['category']}): {kp['description']}"
            for kp in knowledge_points
        ])

        prompt = f"""请分析以下初{grade_level - 6}数学题目，识别其考查的知识点：

题目：
{question_text}

可选知识点列表：
{kp_text}

请以JSON格式返回：
{{
    "primary_point": "主要知识点名称",
    "secondary_points": ["次要知识点1", "次要知识点2"],
    "difficulty": "easy/medium/hard",
    "reasoning": "判断理由（简要说明为什么选择这些知识点）"
}}

注意：
- primary_point必须从上述列表中选择一个最相关的
- secondary_points可以为空数组，或包含1-2个相关知识点
- difficulty根据题目复杂度判断：easy（基础概念）、medium（综合应用）、hard（难题、竞赛题）"""

        try:
            response = self.client.chat.completions.create(
                model=self.text_model,  # 使用文本模型
                max_tokens=1024,
                messages=[{'role': 'user', 'content': prompt}]
            )

            result_text = response.choices[0].message.content
            result = self._extract_json(result_text)
            return result

        except Exception as e:
            logger.error(f"知识点分类失败: {type(e).__name__}: {e}")
            # 降级方案：返回默认值
            return {
                'primary_point': knowledge_points[0]['name'] if knowledge_points else '未分类',
                'secondary_points': [],
                'difficulty': 'medium',
                'reasoning': f'自动分类失败: {str(e)}',
                'error': str(e)
            }

    @staticmethod
    def _is_geometry_question(question_text: str) -> bool:
        """判断是否为几何题"""
        keywords = ['如图', '∠', '△', '平行', '垂直', '证明', '线段',
                    '射线', '直线', '三角形', '四边形', '∥', '⊥', '角平分线',
                    '对顶角', '同位角', '内错角', '同旁内角']
        return any(k in question_text for k in keywords)

    @staticmethod
    def _get_image_base64(image_path: str):
        """读取图片并返回 (base64字符串, media_type)"""
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')
        if image_path.lower().endswith('.png'):
            media_type = 'image/png'
        elif image_path.lower().endswith('.webp'):
            media_type = 'image/webp'
        else:
            media_type = 'image/jpeg'
        return image_data, media_type

    def generate_explanation(self, question_text: str,
                             student_answer: str = None,
                             image_path: str = None,
                             knowledge_info: dict = None) -> str:
        """
        生成详细解析

        Args:
            question_text: 题目文字
            student_answer: 学生的错误解答（可选）
            image_path: 原题图片路径（可选，几何题时传入以看图解题）
            knowledge_info: 题目基本信息字典，包含 grade_label/semester_label/chapter/category/description

        Returns:
            markdown格式的详细解析
        """
        is_geometry = self._is_geometry_question(question_text)

        # 构建题目基本信息段落（告知AI年级范围，避免超纲）
        if knowledge_info:
            grade_label = knowledge_info.get('grade_label', '')
            semester_label = knowledge_info.get('semester_label', '')
            chapter = knowledge_info.get('chapter', '')
            category = knowledge_info.get('category', '')
            description = knowledge_info.get('description', '')
            info_parts = []
            if grade_label:
                info_parts.append(f"年级：{grade_label}")
            if semester_label:
                info_parts.append(f"学期：{semester_label}")
            if chapter:
                info_parts.append(f"章节：{chapter}")
            if category:
                info_parts.append(f"课本目录：{category}")
            if description:
                info_parts.append(f"知识内容：{description}")
            knowledge_block = "\n".join(info_parts)
            knowledge_section = f"""
【题目基本信息】
{knowledge_block}

【重要约束】解题时只能使用该年级该学期已学过的知识点，绝对不能使用超出此范围的数学方法或概念。
"""
        else:
            knowledge_section = ""

        # 角色设定（system message）- 针对 DeepSeek-V3 优化
        system_role = (
            "你是一位经验丰富的初中数学特级教师，擅长用简单易懂的语言讲解数学题目。"
            "你的教学风格：\n"
            "1. 循序渐进，从已知到未知，逐步引导学生思考\n"
            "2. 语言简洁清晰，避免使用过于复杂的术语\n"
            "3. 善于抓住题目的关键点和易错点\n"
            "4. 注重解题方法的总结和归纳\n"
            "5. 严格遵守年级知识范围，不使用超纲知识"
        )

        # ── 几何题 + 有图片 → Vision模型看图解题 ──────────────────────────
        if is_geometry and image_path:
            try:
                image_data, media_type = self._get_image_base64(image_path)
            except Exception as e:
                logger.warning(f"读取图片失败，退回纯文字解析: {e}")
                is_geometry = False

        if is_geometry and image_path:
            student_part = f"\n学生的解答：\n{student_answer}\n" if student_answer else ""
            geometry_prompt = f"""请仔细观察图片中的几何图形，然后为以下题目提供详细解析。
{knowledge_section}
题目：
{question_text}
{student_part}
【解题要求】
1. 必须严格依据图片中实际看到的几何图形来解题
2. 不得凭空假设任何点、线、角的位置关系
3. 每一步推理都要注明依据（定义、定理、公理）
4. 使用初中生能理解的语言

请按以下结构输出（使用markdown格式）：

## 📋 题目分析
- 考查的核心知识点
- 图形中的关键信息（已知条件）
- 解题的突破口

## 📝 详细解题步骤
（分步骤编号，每步说明：做什么 → 为什么 → 得到什么）

## ✅ 正确答案

## ⚠️ 易错点提醒
（用【易错】标记，说明为什么容易错）

## 🔍 常见错误分析
{('（分析学生解答中的错误，指出错在哪里、为什么错）' if student_answer else '（列举本题的典型错误做法）')}

## 💡 解题技巧
（总结本题的解题方法和思路）

数学公式用LaTeX：行内 $...$，独立公式 $$...$$
"""
            try:
                response = self.client.chat.completions.create(
                    model=self.vision_model,  # 用视觉模型看图解题
                    max_tokens=4096,
                    messages=[
                        {'role': 'system', 'content': system_role},
                        {
                            'role': 'user',
                            'content': [
                                {
                                    'type': 'image_url',
                                    'image_url': {
                                        'url': f'data:{media_type};base64,{image_data}'
                                    }
                                },
                                {'type': 'text', 'text': geometry_prompt}
                            ]
                        }
                    ]
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"几何题看图解析失败: {type(e).__name__}: {e}")
                return f"解析生成失败: {str(e)}"

        # ── 代数题 或 无图片 → 原有纯文本模型流程 ─────────────────────────
        prompt = f"""请为以下初中数学题目提供详细解析。
{knowledge_section}
题目：
{question_text}
"""

        if student_answer:
            prompt += f"""
学生的解答：
{student_answer}
"""

        prompt += """
【解题要求】
1. 使用初中生能理解的语言，避免过于抽象的表述
2. 每个步骤都要说明"为什么这样做"
3. 重点标注易错点和关键步骤
4. 如果有多种解法，优先介绍最简单的方法

请按以下结构输出（使用markdown格式）：

## 📋 题目分析
- 题目类型和考查的知识点
- 已知条件和求解目标
- 解题思路概述

## 📝 详细解题步骤
（分步骤编号，格式：**步骤N：** 做什么 → 为什么 → 结果）

## ✅ 正确答案

## ⚠️ 易错点提醒
（用【易错】标记，说明容易在哪里出错、为什么容易错）

## 🔍 常见错误分析
{('（分析学生解答中的错误：错在哪里、为什么错、正确做法是什么）' if student_answer else '（列举本题的典型错误做法和原因）')}

## 💡 解题技巧
（总结本题的解题方法、思路和注意事项）

数学公式请使用LaTeX格式，行内公式用 $...$ 包裹，独立公式用 $$...$$ 包裹。
例如：行内公式 $x^2 + 1$，独立公式：
$$
x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}
$$
"""

        try:
            # Kimi-K2-Thinking 模型自带思维链能力，无需特殊参数
            response = self.client.chat.completions.create(
                model=self.text_model,  # 使用文本模型
                max_tokens=4096,
                messages=[
                    {'role': 'system', 'content': system_role},
                    {'role': 'user', 'content': prompt}
                ]
            )

            explanation = response.choices[0].message.content
            return explanation

        except Exception as e:
            logger.error(f"生成解析失败: {type(e).__name__}: {e}")
            return f"解析生成失败: {str(e)}"

    def recommend_similar_questions(self, question_text: str, knowledge_point: str, tags: list = None) -> list:
        """
        推荐类似题目

        Args:
            question_text: 原题目文字
            knowledge_point: 知识点名称
            tags: 题目标签列表（可选）

        Returns:
            [
                {
                    'question': str,  # 题目
                    'answer': str,    # 答案
                    'hint': str       # 分步解题思路
                },
                ...
            ]
        """
        tags_line = f"题目标签：{', '.join(tags)}" if tags else ""
        prompt = f"""根据下面这道初中数学题，生成3道类似的练习题，用于帮助学生巩固同一知识点。

原题：
{question_text}

知识点：{knowledge_point}
{tags_line}

出题要求：
- 难度与原题相近
- 考查完全相同的知识点和解题方法
- 标签反映了该题的题型和易错点，出题时需体现这些特征
- 三道题各自采用不同的变化方式，例如：改变数值、改变已知/求解方向、改变题目情境
- 不要与原题过于相似，避免学生只靠套路解题
- 数学符号和公式使用 LaTeX 格式（行内用 $...$，块级用 $$...$$）
- 出题前必须自行验算，确保题目有唯一正确答案且答案与解题过程完全一致，不得出现无解或条件矛盾的题目

请以 JSON 格式返回，不要包含其他文字：
[
    {{
        "question": "题目文字",
        "answer": "最终答案",
        "hint": "分步解题思路，帮助学生理解方法"
    }},
    ...
]"""

        try:
            response = self.client.chat.completions.create(
                model=self.text_model,
                max_tokens=3072,
                messages=[
                    {
                        'role': 'system',
                        'content': '你是一位经验丰富的初中数学教师，擅长出题和分析题目考查点。'
                    },
                    {'role': 'user', 'content': prompt}
                ]
            )

            result_text = response.choices[0].message.content
            similar_questions = self._extract_json(result_text)
            return similar_questions

        except Exception as e:
            logger.error(f"推荐题目失败: {type(e).__name__}: {e}")
            return []

    def analyze_weak_points(self, mistakes_data: list) -> dict:
        """
        分析薄弱环节

        Args:
            mistakes_data: 错题统计数据
                [
                    {
                        'knowledge_point': str,
                        'count': int,
                        'mastered_count': int,
                        'examples': [str]  # 示例题目
                    },
                    ...
                ]

        Returns:
            {
                'weak_points_ranking': list,  # 薄弱知识点排名
                'analysis': str,              # 详细分析
                'suggestions': list           # 学习建议
            }
        """
        # 构建统计数据文本
        stats_text = "\n".join([
            f"- {item['knowledge_point']}: 错误{item['count']}次，已掌握{item['mastered_count']}次"
            for item in mistakes_data
        ])

        prompt = f"""请分析以下错题统计数据，识别薄弱知识点并给出学习建议：

错题统计：
{stats_text}

请以JSON格式返回：
{{
    "weak_points_ranking": [
        {{
            "knowledge_point": "知识点名称",
            "error_rate": 0.75,
            "priority": "high/medium/low",
            "specific_issues": "具体问题描述"
        }},
        ...
    ],
    "analysis": "整体分析（markdown格式，分析学习状况和主要问题）",
    "suggestions": [
        "建议1：针对性学习建议",
        "建议2：复习顺序建议",
        "建议3：学习方法建议"
    ]
}}

注意：
- 按错误率从高到低排序
- priority根据错误率和重要性判断
- 给出具体可行的学习建议"""

        try:
            # Kimi-K2-Thinking ���型自带思维链能力，无需特殊参数
            response = self.client.chat.completions.create(
                model=self.text_model,  # 使用文本模型
                max_tokens=3072,
                messages=[{'role': 'user', 'content': prompt}]
            )

            result_text = response.choices[0].message.content
            analysis = self._extract_json(result_text)
            return analysis

        except Exception as e:
            logger.error(f"分析失败: {type(e).__name__}: {e}")
            return {
                'weak_points_ranking': [],
                'analysis': f'分析失败: {str(e)}',
                'suggestions': []
            }

    def analyze_weak_tags(self, tags_data: list) -> dict:
        """
        分析薄弱标签

        Args:
            tags_data: 标签统计数据
                [
                    {
                        'tag': str,
                        'count': int,
                        'mastered_count': int,
                        'examples': [str]  # 示例题目
                    },
                    ...
                ]

        Returns:
            {
                'weak_tags_ranking': list,  # 薄弱标签排名
                'analysis': str,            # 详细分析
                'suggestions': list         # 学习建议
            }
        """
        # 构建统计数据文本
        stats_text = "\n".join([
            f"- {item['tag']}: 错误{item['count']}次，已掌握{item['mastered_count']}次"
            for item in tags_data
        ])

        # 添加示例题目（帮助AI理解标签含义）
        examples_text = ""
        for item in tags_data[:5]:  # 只展示前5个标签的示例
            if item.get('examples'):
                examples_text += f"\n【{item['tag']}】示例题目：\n"
                for i, ex in enumerate(item['examples'][:2], 1):
                    examples_text += f"  {i}. {ex}\n"

        system_role = """你是一位经验丰富的初中数学教学专家，擅长分析学生的学习问题并给出针对性建议。

你的分析特点：
1. 能够识别标签背后的深层问题（知识点薄弱、题型不熟、思维方式、学习习惯等）
2. 善于发现标签之间的关联性（如"计算错误"可能源于"有理数运算"基础不牢）
3. 给出的建议具体可行，分短期和长期目标
4. 语言亲切，鼓励学生，避免打击自信心"""

        prompt = f"""请分析以下初中数学错题的标签统计数据，识别学生的薄弱环节并给出学习建议。

## 错题标签统计
{stats_text}

## 标签示例题目
{examples_text}

## 分析要求

1. **标签分类**：将标签分为以下类型
   - 知识点类（如"三角形全等"、"一元一次方程"）
   - 题型类（如"找规律"、"动点问题"、"应用题"）
   - 错误原因类（如"计算错误"、"审题不清"、"粗心"）

2. **深度分析**：
   - 识别最核心的问题（不只是列举标签）
   - 分析标签之间的关联性
   - 判断是知识漏洞、方法不当还是习惯问题

3. **优先级判断**：
   - high：基础知识点薄弱，影响后续学习
   - medium：特定题型不熟练，需要专项训练
   - low：偶发性错误，加强练习即可

4. **建议要求**：
   - 短期目标（1-2周内可完成）
   - 长期规划（1-2个月的提升路径）
   - 具体的学习方法和资源

## 返回格式

请以JSON格式返回：
{{
    "weak_tags_ranking": [
        {{
            "tag": "标签名称",
            "tag_type": "knowledge/question_type/error_cause",
            "error_rate": 0.75,
            "priority": "high/medium/low",
            "root_cause": "深层原因分析（为什么会在这个标签上频繁出错）",
            "impact": "影响范围（这个问题会影响哪些其他知识点或题型）"
        }},
        ...
    ],
    "analysis": "## 整体分析\\n\\n### 核心问题\\n...\\n\\n### 问题关联\\n...\\n\\n### 学习状态评估\\n...",
    "suggestions": [
        {{
            "type": "short_term",
            "title": "短期目标（1-2周）",
            "actions": [
                "具体行动1",
                "具体行动2"
            ]
        }},
        {{
            "type": "long_term",
            "title": "长期规划（1-2月）",
            "actions": [
                "具体行动1",
                "具体行动2"
            ]
        }},
        {{
            "type": "method",
            "title": "学习方法建议",
            "actions": [
                "方法1",
                "方法2"
            ]
        }}
    ]
}}

注意：
- 分析要深入，不要只是重复标签名称
- 建议要具体可行，避免空泛的"多练习"、"认真审题"
- 语气要鼓励性，帮助学生建立信心"""

        try:
            response = self.client.chat.completions.create(
                model=self.text_model,  # DeepSeek-V3
                max_tokens=4096,
                messages=[
                    {'role': 'system', 'content': system_role},
                    {'role': 'user', 'content': prompt}
                ]
            )

            result_text = response.choices[0].message.content
            analysis = self._extract_json(result_text)
            return analysis

        except Exception as e:
            logger.error(f"分析失败: {type(e).__name__}: {e}")
            return {
                'weak_tags_ranking': [],
                'analysis': f'分析失败: {str(e)}',
                'suggestions': []
            }
