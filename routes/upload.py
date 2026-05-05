"""上传路由"""
from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from services.image_service import ImageService
from services.ai_service import AIService
from models import db, Mistake, KnowledgePoint, Tag
import json

bp = Blueprint('upload', __name__, url_prefix='/upload')


@bp.route('/')
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

    return render_template('upload.html', kp_data=kp_data, tags=tags)


@bp.route('/image', methods=['POST'])
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

        # 创建错题记录
        mistake = Mistake(
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
            mistake.tags.extend(tags)

        db.session.add(mistake)
        db.session.commit()

        return jsonify({
            'success': True,
            'mistake_id': mistake.id,
            'question_text': question_text,
            'knowledge_point': primary_point_name,
            'difficulty': difficulty,
            'image_path': image_path,
            'thumbnail_path': thumbnail_path
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/batch', methods=['POST'])
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

                mistake = Mistake(
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
                    mistake.tags.extend(tags)

                db.session.add(mistake)
                db.session.commit()

                results.append({
                    'success': True,
                    'filename': file.filename,
                    'mistake_id': mistake.id
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
