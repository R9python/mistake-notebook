"""
标签管理路由
提供标签的增删改查接口
"""

from flask import Blueprint, request, jsonify, render_template
from models import db, Tag, Mistake

bp = Blueprint('tags', __name__, url_prefix='/tags')


@bp.route('/')
def index():
    """标签管理页面"""
    tags = Tag.query.order_by(Tag.name).all()

    # 统计每个标签的使用次数
    tag_stats = []
    for tag in tags:
        count = db.session.query(Mistake).join(Mistake.tags).filter(Tag.id == tag.id).count()
        tag_stats.append({
            'id': tag.id,
            'name': tag.name,
            'color': tag.color,
            'count': count
        })

    return render_template('tags.html', tags=tag_stats)


@bp.route('/api/list')
def api_list():
    """获取所有标签（API）"""
    tags = Tag.query.order_by(Tag.name).all()
    return jsonify([{
        'id': tag.id,
        'name': tag.name,
        'color': tag.color
    } for tag in tags])


@bp.route('/api/create', methods=['POST'])
def api_create():
    """创建新标签"""
    data = request.get_json()
    name = data.get('name', '').strip()
    color = data.get('color', '#0078D4')

    if not name:
        return jsonify({'success': False, 'message': '标签名称不能为空'}), 400

    # 检查是否已存在
    existing = Tag.query.filter_by(name=name).first()
    if existing:
        return jsonify({'success': False, 'message': '标签已存在'}), 400

    # 创建新标签
    tag = Tag(name=name, color=color)
    db.session.add(tag)
    db.session.commit()

    return jsonify({
        'success': True,
        'tag': {
            'id': tag.id,
            'name': tag.name,
            'color': tag.color
        }
    })


@bp.route('/api/update/<int:tag_id>', methods=['PUT'])
def api_update(tag_id):
    """更新标签"""
    tag = db.session.get(Tag, tag_id)
    if not tag:
        return jsonify({'success': False, 'message': '标签不存在'}), 404

    data = request.get_json()
    name = data.get('name', '').strip()
    color = data.get('color')

    if name:
        # 检查名称是否与其他标签冲突
        existing = Tag.query.filter(Tag.name == name, Tag.id != tag_id).first()
        if existing:
            return jsonify({'success': False, 'message': '标签名称已被使用'}), 400
        tag.name = name

    if color:
        tag.color = color

    db.session.commit()

    return jsonify({
        'success': True,
        'tag': {
            'id': tag.id,
            'name': tag.name,
            'color': tag.color
        }
    })


@bp.route('/api/delete/<int:tag_id>', methods=['DELETE'])
def api_delete(tag_id):
    """删除标签"""
    tag = db.session.get(Tag, tag_id)
    if not tag:
        return jsonify({'success': False, 'message': '标签不存在'}), 404

    # 检查是否有错题使用此标签
    count = db.session.query(Mistake).join(Mistake.tags).filter(Tag.id == tag_id).count()
    if count > 0:
        return jsonify({
            'success': False,
            'message': f'无法删除：有 {count} 道错题正在使用此标签'
        }), 400

    db.session.delete(tag)
    db.session.commit()

    return jsonify({'success': True, 'message': '标签已删除'})
