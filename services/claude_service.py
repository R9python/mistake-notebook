"""Claude API服务 - 核心AI功能"""
import anthropic
import base64
import json
from config import Config
from services.knowledge_points import get_knowledge_points_by_grade, get_all_knowledge_points


class ClaudeService:
    """Claude API集成服务"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.model = Config.CLAUDE_MODEL

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
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{
                    'role': 'user',
                    'content': [
                        {
                            'type': 'image',
                            'source': {
                                'type': 'base64',
                                'media_type': media_type,
                                'data': image_data
                            }
                        },
                        {'type': 'text', 'text': prompt}
                    ]
                }]
            )

            # 提取文本响应
            result_text = next(block.text for block in response.content if block.type == 'text')

            # 解析JSON
            result = json.loads(result_text)
            return result

        except Exception as e:
            print(f"图片识别失败: {e}")
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
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{'role': 'user', 'content': prompt}]
            )

            result_text = next(block.text for block in response.content if block.type == 'text')
            result = json.loads(result_text)
            return result

        except Exception as e:
            print(f"知识点分类失败: {e}")
            # 降级方案：返回默认值
            return {
                'primary_point': knowledge_points[0]['name'] if knowledge_points else '未分类',
                'secondary_points': [],
                'difficulty': 'medium',
                'reasoning': f'自动分类失败: {str(e)}',
                'error': str(e)
            }

    def generate_explanation(self, question_text: str, student_answer: str = None) -> str:
        """
        生成详细解析

        Args:
            question_text: 题目文字
            student_answer: 学生的错误解答（可选）

        Returns:
            markdown格式的详细解析
        """
        prompt = f"""请为以下数学题目提供详细解析：

题目：
{question_text}
"""

        if student_answer:
            prompt += f"""
学生的解答：
{student_answer}
"""

        prompt += """
请提供：
1. 题目分析（考查的知识点和解题思路）
2. 详细解题步骤（每一步都要清晰说明）
3. 正确答案
4. 常见错误分析（如果有学生解答，请指出错误所在）
5. 解题技巧和注意事项

请用markdown格式输出，使用适当的标题、列表和数学公式。"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                thinking={'type': 'adaptive'},
                messages=[{'role': 'user', 'content': prompt}]
            )

            explanation = next(block.text for block in response.content if block.type == 'text')
            return explanation

        except Exception as e:
            print(f"生成解析失败: {e}")
            return f"解析生成失败: {str(e)}"

    def recommend_similar_questions(self, question_text: str, knowledge_point: str) -> list:
        """
        推荐类似题目

        Args:
            question_text: 原题目文字
            knowledge_point: 知识点名称

        Returns:
            [
                {
                    'question': str,  # 题目
                    'answer': str,    # 答案
                    'hint': str       # 简要提示
                },
                ...
            ]
        """
        prompt = f"""基于以下原题和知识点，生成3道类似的练习题：

原题：
{question_text}

知识点：{knowledge_point}

要求：
- 难度相近
- 考查相同知识点
- 题型略有变化（不要完全一样）
- 每道题都要有答案和简要解题提示

请以JSON格式返回：
[
    {{
        "question": "题目文字",
        "answer": "答案",
        "hint": "解题提示"
    }},
    ...
]"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3072,
                messages=[{'role': 'user', 'content': prompt}]
            )

            result_text = next(block.text for block in response.content if block.type == 'text')
            similar_questions = json.loads(result_text)
            return similar_questions

        except Exception as e:
            print(f"推荐题目失败: {e}")
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
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3072,
                thinking={'type': 'adaptive'},
                messages=[{'role': 'user', 'content': prompt}]
            )

            result_text = next(block.text for block in response.content if block.type == 'text')
            analysis = json.loads(result_text)
            return analysis

        except Exception as e:
            print(f"分析失败: {e}")
            return {
                'weak_points_ranking': [],
                'analysis': f'分析失败: {str(e)}',
                'suggestions': []
            }
