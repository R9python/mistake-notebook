"""错题管理路由"""
from flask import Blueprint, request, jsonify, render_template, current_app, url_for
from datetime import datetime
from models import db, Mistake, KnowledgePoint, Tag
from services.ai_service import AIService
import os
import json
import re
import markdown

bp = Blueprint('mistakes', __name__, url_prefix='/mistakes')


@bp.route('/')
def mistake_list():
    """错题列表页面"""
    # 获取筛选参数
    grade_level = request.args.get('grade', type=int)
    semester = request.args.get('semester', type=int)
    knowledge_point_id = request.args.get('knowledge_point', type=int)
    tag_id = request.args.get('tag', type=int)
    is_mastered = request.args.get('mastered')
    page = request.args.get('page', 1, type=int)

    # 构建查询
    query = Mistake.query

    if grade_level:
        query = query.filter_by(grade_level=grade_level)

    if semester:
        # 通过关联知识点的学期字段筛选
        query = query.join(KnowledgePoint, Mistake.knowledge_point_id == KnowledgePoint.id)\
                     .filter(KnowledgePoint.semester == semester)

    if knowledge_point_id:
        query = query.filter(Mistake.knowledge_point_id == knowledge_point_id)

    if tag_id:
        # 按标签筛选
        query = query.join(Mistake.tags).filter(Tag.id == tag_id)

    if is_mastered is not None and is_mastered != '':
        query = query.filter_by(is_mastered=(is_mastered == 'true'))

    # 获取所有错题（不再按来源分组）
    mistakes = query.order_by(Mistake.created_at.desc()).all()

    # 构建知识点级联数据，供筛选器使用
    kps = KnowledgePoint.query.order_by(
        KnowledgePoint.grade_level,
        KnowledgePoint.semester,
        KnowledgePoint.chapter
    ).all()
    kp_data = {}
    for kp in kps:
        g = kp.grade_level
        s = kp.semester or 0
        if g not in kp_data:
            kp_data[g] = {}
        if s not in kp_data[g]:
            kp_data[g][s] = []
        kp_data[g][s].append({
            'id': kp.id,
            'name': kp.name,
            'chapter': kp.chapter or '',
            'category': kp.category,
            'desc': kp.description or ''
        })

    # 获取所有标签
    tags = Tag.query.order_by(Tag.name).all()

    # 获取所有知识点（扁平列表，供下拉框使用）
    knowledge_points = KnowledgePoint.query.order_by(
        KnowledgePoint.grade_level,
        KnowledgePoint.semester,
        KnowledgePoint.chapter
    ).all()

    return render_template('mistake_list.html',
                           mistakes=mistakes,
                           kp_data=kp_data,
                           knowledge_points=knowledge_points,
                           tags=tags)


@bp.route('/<int:mistake_id>')
def mistake_detail(mistake_id):
    """错题详情页面"""
    mistake = Mistake.query.get_or_404(mistake_id)

    # 兼容历史数据：若 ai_explanation 存的是 markdown 原文或被错误包裹在代码块里，自动转为 HTML
    needs_convert = False
    if mistake.ai_explanation:
        if '<' not in mistake.ai_explanation:
            needs_convert = True  # 纯 markdown 原文
        elif mistake.ai_explanation.strip().startswith('<pre') and 'language-markdown' in mistake.ai_explanation:
            needs_convert = True  # 被 codehilite 错误包裹的 markdown

    if needs_convert:
        raw = mistake.ai_explanation
        # 若是被 <pre><code> 包裹，提取内部文本
        inner = re.sub(r'<[^>]+>', '', raw)
        # 剥除外层代码围栏
        inner = re.sub(r'^```[a-zA-Z]*\s*\n', '', inner.strip())
        inner = re.sub(r'\n```\s*$', '', inner.strip())

        placeholders = {}
        counter = [0]

        def protect_formula(m):
            key = f'\x00MATH{counter[0]}\x00'
            placeholders[key] = m.group(0)
            counter[0] += 1
            return key

        protected = re.sub(r'\$\$[\s\S]*?\$\$', protect_formula, inner)
        protected = re.sub(r'\$[^\$\n]+?\$', protect_formula, protected)
        html = markdown.markdown(protected, extensions=['extra', 'codehilite', 'tables'])
        for key, formula in placeholders.items():
            html = html.replace(key, formula)
        mistake.ai_explanation = html
        db.session.commit()

    # 按 id 升序找紧邻的上一题和下一题
    prev_mistake = Mistake.query.filter(Mistake.id < mistake_id).order_by(Mistake.id.desc()).first()
    next_mistake = Mistake.query.filter(Mistake.id > mistake_id).order_by(Mistake.id.asc()).first()

    return render_template('mistake_detail.html',
                           mistake=mistake,
                           prev_mistake=prev_mistake,
                           next_mistake=next_mistake)


@bp.route('/<int:mistake_id>', methods=['PUT'])
def update_mistake(mistake_id):
    """
    更新错题

    JSON body:
        - question_text: 题目文字（可选）
        - knowledge_point_id: 知识点ID（可选）
        - notes: 笔记（可选）
        - is_mastered: 是否已掌握（可选）
        - tag_ids: 标签ID列表（可选）
    """
    mistake = Mistake.query.get_or_404(mistake_id)
    data = request.get_json()

    if 'question_text' in data:
        mistake.question_text = data['question_text']

    if 'knowledge_point_id' in data:
        mistake.knowledge_point_id = data['knowledge_point_id']

    if 'notes' in data:
        mistake.notes = data['notes']

    if 'tag_ids' in data:
        # 更新标签关联
        tag_ids = data['tag_ids']
        mistake.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()

    if 'is_mastered' in data:
        mistake.is_mastered = data['is_mastered']

    mistake.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': '更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:mistake_id>', methods=['DELETE'])
def delete_mistake(mistake_id):
    """删除错题"""
    mistake = Mistake.query.get_or_404(mistake_id)

    try:
        db.session.delete(mistake)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:mistake_id>/explanation', methods=['POST'])
def generate_explanation(mistake_id):
    """
    生成AI解析

    返回markdown格式的解析
    """
    mistake = Mistake.query.get_or_404(mistake_id)

    # 如果已有解析且未要求重新生成，直接返回
    data = request.get_json(silent=True) or {}
    regenerate = data.get('regenerate', False)
    if mistake.ai_explanation and not regenerate:
        return jsonify({
            'success': True,
            'explanation': mistake.ai_explanation
        })

    try:
        ai_service = AIService()

        # 构建原题图片的完整路径（几何题时传入，让AI看图解题）
        image_full_path = os.path.join(
            current_app.root_path, 'static', mistake.image_path
        )
        image_full_path = image_full_path if os.path.exists(image_full_path) else None

        # 组装题目基本信息，告知AI年级范围避免超纲解题
        grade_map = {7: '初一（7年级）', 8: '初二（8年级）', 9: '初三（9年级）'}
        semester_map = {1: '上学期', 2: '下学期'}
        kp = mistake.knowledge_point
        knowledge_info = {
            'grade_label': grade_map.get(mistake.grade_level, f'{mistake.grade_level}年级'),
            'semester_label': semester_map.get(kp.semester, '') if kp else '',
            'chapter': kp.chapter or '' if kp else '',
            'category': kp.category or '' if kp else '',
            'description': kp.description or '' if kp else '',
        }

        explanation = ai_service.generate_explanation(
            mistake.question_text,
            None,            # 暂不传入学生答案
            image_full_path, # 传入原图，几何题时AI会看图解题
            knowledge_info   # 传入基本信息，约束AI在年级范围内解题
        )

        # Convert markdown to HTML, preserving LaTeX formulas
        # Step 0: 剥除 AI 有时返回的外层代码围栏（```markdown ... ``` 或 ``` ... ```）
        explanation = re.sub(r'^```[a-zA-Z]*\s*\n', '', explanation.strip())
        explanation = re.sub(r'\n```\s*$', '', explanation.strip())

        # Step 1: Extract and protect LaTeX formulas from markdown processing
        placeholders = {}
        counter = [0]

        def protect_formula(match):
            key = f'\x00MATH{counter[0]}\x00'
            placeholders[key] = match.group(0)
            counter[0] += 1
            return key

        # Protect display math ($$...$$) first, then inline math ($...$)
        protected = re.sub(r'\$\$[\s\S]*?\$\$', protect_formula, explanation)
        protected = re.sub(r'\$[^\$\n]+?\$', protect_formula, protected)

        # Step 2: Convert markdown to HTML
        html_explanation = markdown.markdown(
            protected,
            extensions=['extra', 'codehilite', 'tables']
        )

        # Step 3: Restore LaTeX formulas
        for key, formula in placeholders.items():
            html_explanation = html_explanation.replace(key, formula)

        # Step 4: 几何题在解析区顶部插入原题图片，供学生对照解析阅读
        if ai_service._is_geometry_question(mistake.question_text) and image_full_path:
            img_src = url_for('static', filename=mistake.image_path)
            img_html = (
                f'<div class="geometry-original-img">'
                f'<p class="geometry-img-label">📐 题目原图</p>'
                f'<img src="{img_src}" alt="题目原图">'
                f'</div>'
            )
            html_explanation = img_html + html_explanation

        # Save explanation
        mistake.ai_explanation = html_explanation
        db.session.commit()

        return jsonify({
            'success': True,
            'explanation': html_explanation
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:mistake_id>/similar', methods=['GET'])
def get_similar_questions(mistake_id):
    """
    获取类似题目

    返回推荐的类似题目列表
    """
    mistake = Mistake.query.get_or_404(mistake_id)

    # 如果已有推荐，直接返回（除非强制重新生成）
    if mistake.similar_questions and not request.args.get('regenerate'):
        try:
            similar = json.loads(mistake.similar_questions)
            return jsonify({
                'success': True,
                'similar_questions': similar
            })
        except:
            pass

    try:
        ai_service = AIService()
        knowledge_point_name = mistake.knowledge_point.name if mistake.knowledge_point else '未分类'

        similar_questions = ai_service.recommend_similar_questions(
            mistake.question_text,
            knowledge_point_name
        )

        # 保存推荐
        mistake.similar_questions = json.dumps(similar_questions, ensure_ascii=False)
        db.session.commit()

        return jsonify({
            'success': True,
            'similar_questions': similar_questions
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:mistake_id>/review', methods=['POST'])
def record_review(mistake_id):
    """
    记录复习

    更新复习次数和最后复习时间
    """
    mistake = Mistake.query.get_or_404(mistake_id)

    mistake.review_count += 1
    mistake.last_review_at = datetime.utcnow()

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'review_count': mistake.review_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/batch-delete', methods=['POST'])
def batch_delete():
    """
    批量删除错题

    JSON body:
        - ids: [mistake_id1, mistake_id2, ...]
    """
    data = request.get_json()
    ids = data.get('ids', [])

    if not ids:
        return jsonify({'error': '没有选择错题'}), 400

    try:
        Mistake.query.filter(Mistake.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'成功删除{len(ids)}道错题'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/batch-master', methods=['POST'])
def batch_master():
    """
    批量标记已掌握

    JSON body:
        - ids: [mistake_id1, mistake_id2, ...]
    """
    data = request.get_json()
    ids = data.get('ids', [])

    if not ids:
        return jsonify({'error': '没有选择错题'}), 400

    try:
        Mistake.query.filter(Mistake.id.in_(ids)).update(
            {'is_mastered': True},
            synchronize_session=False
        )
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'成功标记{len(ids)}道错题为已掌握'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/explain-text', methods=['POST'])
def explain_text():
    """对任意题目文本生成 AI 详解"""
    data = request.get_json()
    question_text = (data or {}).get('question_text', '').strip()
    if not question_text:
        return jsonify({'error': '题目内容不能为空'}), 400

    try:
        ai_service = AIService()
        explanation = ai_service.generate_explanation(question_text)

        formulas = {}
        def protect_formula(m):
            key = f'FORMULA_{len(formulas)}'
            formulas[key] = m.group(0)
            return key
        protected = re.sub(r'\$\$[\s\S]*?\$\$', protect_formula, explanation)
        protected = re.sub(r'\$[^\$]+\$', protect_formula, protected)
        html = markdown.markdown(protected, extensions=['tables', 'fenced_code'])
        for key, formula in formulas.items():
            html = html.replace(key, formula)

        return jsonify({'success': True, 'explanation': html})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
