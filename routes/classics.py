"""经典题管理路由"""
from flask import Blueprint, request, jsonify, render_template, current_app, url_for
from datetime import datetime
from werkzeug.utils import secure_filename
from models import db, ClassicQuestion, KnowledgePoint, Tag
from services.ai_service import AIService
from services.image_service import ImageService
import os
import json
import re
import markdown

bp = Blueprint('classics', __name__, url_prefix='/classics')


@bp.route('/upload')
def upload_page():
    """上传页面"""
    # 按年级分组知识点，供前端级联选择
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

    return render_template('classic_upload.html', kp_data=kp_data, tags=tags)


@bp.route('/upload/image', methods=['POST'])
def upload_image():
    """
    上传单张图片并AI处理

    Form data:
        - file: 图片文件
        - grade_level: 年级 (7/8/9)
    """
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400

    grade_level = request.form.get('grade_level', type=int)
    if not grade_level or grade_level not in [7, 8, 9]:
        return jsonify({'error': '年级参数无效'}), 400

    knowledge_point_id = request.form.get('knowledge_point_id', type=int)
    tag_ids = request.form.getlist('tag_ids[]')  # 获取标签ID列表

    try:
        # 保存图片
        image_service = ImageService()
        image_path, thumbnail_path = image_service.save_uploaded_image(file)

        # 获取完整路径用于AI处理
        full_image_path = f"static/{image_path}"

        # AI处理：提取题目
        ai_service = AIService()
        extraction_result = ai_service.extract_question_from_image(
            full_image_path,
            grade_level
        )

        if 'error' in extraction_result:
            return jsonify({
                'success': True,
                'ocr_failed': True,
                'image_path': image_path,
                'thumbnail_path': thumbnail_path,
                'message': '图片识别失败，请手动输入题目'
            })

        question_text = extraction_result.get('question_text', '')
        student_answer = extraction_result.get('student_answer', '')

        if not question_text:
            return jsonify({
                'success': True,
                'ocr_failed': True,
                'image_path': image_path,
                'thumbnail_path': thumbnail_path,
                'message': '未能识别题目文字，请手动输入'
            })

        # 知识点：优先用用户选择的，否则AI分类
        if knowledge_point_id:
            knowledge_point = KnowledgePoint.query.get(knowledge_point_id)
            difficulty = 'medium'
            primary_point_name = knowledge_point.name if knowledge_point else None
        else:
            classification_result = ai_service.classify_knowledge_point(question_text, grade_level)
            primary_point_name = classification_result.get('primary_point', '').split('(')[0].strip()
            difficulty = classification_result.get('difficulty', 'medium')
            knowledge_point = KnowledgePoint.query.filter_by(
                name=primary_point_name, grade_level=grade_level
            ).first() or KnowledgePoint.query.filter_by(grade_level=grade_level).first()

        # 创建经典题记录
        classic = ClassicQuestion(
            image_path=image_path,
            thumbnail_path=thumbnail_path,
            question_text=question_text,
            knowledge_point_id=knowledge_point.id if knowledge_point else None,
            grade_level=grade_level,
            difficulty=difficulty
        )

        # 关联标签
        if tag_ids:
            tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
            classic.tags.extend(tags)

        db.session.add(classic)
        db.session.commit()

        return jsonify({
            'success': True,
            'classic_id': classic.id,
            'question_text': question_text,
            'knowledge_point': primary_point_name,
            'difficulty': difficulty,
            'image_path': image_path,
            'thumbnail_path': thumbnail_path
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/upload/batch', methods=['POST'])
def upload_batch():
    """
    批量上传图片

    Form data:
        - files[]: 多个图片文件
        - grade_level: 年级
    """
    if 'files[]' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    files = request.files.getlist('files[]')
    grade_level = request.form.get('grade_level', type=int)
    tag_ids = request.form.getlist('tag_ids[]')  # 获取标签ID列表

    if not grade_level or grade_level not in [7, 8, 9]:
        return jsonify({'error': '年级参数无效'}), 400

    results = []
    image_service = ImageService()
    ai_service = AIService()

    for file in files:
        if file.filename == '':
            continue

        try:
            # 保存图片
            image_path, thumbnail_path = image_service.save_uploaded_image(file)
            full_image_path = f"static/{image_path}"

            # AI处理
            extraction_result = ai_service.extract_question_from_image(
                full_image_path,
                grade_level
            )

            question_text = extraction_result.get('question_text', '')

            if question_text:
                classification_result = ai_service.classify_knowledge_point(
                    question_text,
                    grade_level
                )

                primary_point_name = classification_result.get('primary_point')
                difficulty = classification_result.get('difficulty', 'medium')

                knowledge_point = KnowledgePoint.query.filter_by(
                    name=primary_point_name,
                    grade_level=grade_level
                ).first()

                classic = ClassicQuestion(
                    image_path=image_path,
                    thumbnail_path=thumbnail_path,
                    question_text=question_text,
                    knowledge_point_id=knowledge_point.id if knowledge_point else None,
                    grade_level=grade_level,
                    difficulty=difficulty
                )

                # 关联标签
                if tag_ids:
                    tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
                    classic.tags.extend(tags)

                db.session.add(classic)
                db.session.commit()

                results.append({
                    'success': True,
                    'filename': file.filename,
                    'classic_id': classic.id
                })
            else:
                results.append({
                    'success': False,
                    'filename': file.filename,
                    'error': 'OCR识别失败'
                })

        except Exception as e:
            results.append({
                'success': False,
                'filename': file.filename,
                'error': str(e)
            })

    return jsonify({
        'success': True,
        'results': results,
        'total': len(files),
        'succeeded': sum(1 for r in results if r.get('success'))
    })


@bp.route('/')
def classic_list():
    """经典题列表页面"""
    # 获取筛选参数
    grade_level = request.args.get('grade', type=int)
    semester = request.args.get('semester', type=int)
    knowledge_point_id = request.args.get('kp', type=int)
    tag_id = request.args.get('tag', type=int)
    is_mastered = request.args.get('mastered')
    page = request.args.get('page', 1, type=int)

    # 构建查询
    query = ClassicQuestion.query

    if grade_level:
        query = query.filter_by(grade_level=grade_level)

    if semester:
        # 通过关联知识点的学期字段筛选
        query = query.join(KnowledgePoint, ClassicQuestion.knowledge_point_id == KnowledgePoint.id)\
                     .filter(KnowledgePoint.semester == semester)

    if knowledge_point_id:
        query = query.filter(ClassicQuestion.knowledge_point_id == knowledge_point_id)

    if tag_id:
        # 按标签筛选
        query = query.join(ClassicQuestion.tags).filter(Tag.id == tag_id)

    if is_mastered is not None and is_mastered != '':
        query = query.filter_by(is_mastered=(is_mastered == 'true'))

    # 获取所有经典题
    classics = query.order_by(ClassicQuestion.created_at.desc()).all()

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

    return render_template('classic_list.html',
                           classics=classics,
                           kp_data=kp_data,
                           tags=tags)


@bp.route('/<int:classic_id>')
def classic_detail(classic_id):
    """经典题详情页面"""
    classic = ClassicQuestion.query.get_or_404(classic_id)

    # 兼容历史数据：若 ai_explanation 存的是 markdown 原文或被错误包裹在代码块里，自动转为 HTML
    needs_convert = False
    if classic.ai_explanation:
        if '<' not in classic.ai_explanation:
            needs_convert = True  # 纯 markdown 原文
        elif classic.ai_explanation.strip().startswith('<pre') and 'language-markdown' in classic.ai_explanation:
            needs_convert = True  # 被 codehilite 错误包裹的 markdown

    if needs_convert:
        raw = classic.ai_explanation
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
        classic.ai_explanation = html
        db.session.commit()

    # 按 id 升序找紧邻的上一题和下一题
    prev_classic = ClassicQuestion.query.filter(ClassicQuestion.id < classic_id).order_by(ClassicQuestion.id.desc()).first()
    next_classic = ClassicQuestion.query.filter(ClassicQuestion.id > classic_id).order_by(ClassicQuestion.id.asc()).first()

    return render_template('classic_detail.html',
                           classic=classic,
                           prev_classic=prev_classic,
                           next_classic=next_classic)


@bp.route('/<int:classic_id>', methods=['PUT'])
def update_classic(classic_id):
    """
    更新经典题

    JSON body:
        - question_text: 题目文字（可选）
        - knowledge_point_id: 知识点ID（可选）
        - notes: 笔记（可选）
        - is_mastered: 是否已掌握（可选）
        - tag_ids: 标签ID列表（可选）
    """
    classic = ClassicQuestion.query.get_or_404(classic_id)
    data = request.get_json()

    if 'question_text' in data:
        classic.question_text = data['question_text']

    if 'knowledge_point_id' in data:
        classic.knowledge_point_id = data['knowledge_point_id']

    if 'notes' in data:
        classic.notes = data['notes']

    if 'tag_ids' in data:
        # 更新标签关联
        tag_ids = data['tag_ids']
        classic.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()

    if 'is_mastered' in data:
        classic.is_mastered = data['is_mastered']

    classic.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': '更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:classic_id>', methods=['DELETE'])
def delete_classic(classic_id):
    """删除经典题"""
    classic = ClassicQuestion.query.get_or_404(classic_id)

    try:
        db.session.delete(classic)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:classic_id>/explanation', methods=['POST'])
def generate_explanation(classic_id):
    """
    生成AI解析

    返回markdown格式的解析
    """
    classic = ClassicQuestion.query.get_or_404(classic_id)

    # 如果已有解析且未要求重新生成，直接返回
    data = request.get_json(silent=True) or {}
    regenerate = data.get('regenerate', False)
    if classic.ai_explanation and not regenerate:
        return jsonify({
            'success': True,
            'explanation': classic.ai_explanation
        })

    try:
        ai_service = AIService()

        # 构建原题图片的完整路径（几何题时传入，让AI看图解题）
        image_full_path = os.path.join(
            current_app.root_path, 'static', classic.image_path
        )
        image_full_path = image_full_path if os.path.exists(image_full_path) else None

        # 组装题目基本信息，告知AI年级范围避免超纲解题
        grade_map = {7: '初一（7年级）', 8: '初二（8年级）', 9: '初三（9年级）'}
        semester_map = {1: '上学期', 2: '下学期'}
        kp = classic.knowledge_point
        knowledge_info = {
            'grade_label': grade_map.get(classic.grade_level, f'{classic.grade_level}年级'),
            'semester_label': semester_map.get(kp.semester, '') if kp else '',
            'chapter': kp.chapter or '' if kp else '',
            'category': kp.category or '' if kp else '',
            'description': kp.description or '' if kp else '',
        }

        explanation = ai_service.generate_explanation(
            classic.question_text,
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
        if ai_service._is_geometry_question(classic.question_text) and image_full_path:
            img_src = url_for('static', filename=classic.image_path)
            img_html = (
                f'<div class="geometry-original-img">'
                f'<p class="geometry-img-label">📐 题目原图</p>'
                f'<img src="{img_src}" alt="题目原图">'
                f'</div>'
            )
            html_explanation = img_html + html_explanation

        # Save explanation
        classic.ai_explanation = html_explanation
        db.session.commit()

        return jsonify({
            'success': True,
            'explanation': html_explanation
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:classic_id>/review', methods=['POST'])
def record_review(classic_id):
    """
    记录复习

    更新复习次数和最后复习时间
    """
    classic = ClassicQuestion.query.get_or_404(classic_id)

    classic.review_count += 1
    classic.last_review_at = datetime.utcnow()

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'review_count': classic.review_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/batch-delete', methods=['POST'])
def batch_delete():
    """
    批量删除经典题

    JSON body:
        - ids: [classic_id1, classic_id2, ...]
    """
    data = request.get_json()
    ids = data.get('ids', [])

    if not ids:
        return jsonify({'error': '没有选择经典题'}), 400

    try:
        ClassicQuestion.query.filter(ClassicQuestion.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'成功删除{len(ids)}道经典题'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/batch-master', methods=['POST'])
def batch_master():
    """
    批量标记已掌握

    JSON body:
        - ids: [classic_id1, classic_id2, ...]
    """
    data = request.get_json()
    ids = data.get('ids', [])

    if not ids:
        return jsonify({'error': '没有选择经典题'}), 400

    try:
        ClassicQuestion.query.filter(ClassicQuestion.id.in_(ids)).update(
            {'is_mastered': True},
            synchronize_session=False
        )
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'成功标记{len(ids)}道经典题为已掌握'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
