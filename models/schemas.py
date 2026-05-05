from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Mistake(db.Model):
    """错题表"""
    __tablename__ = 'mistakes'

    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    question_text = db.Column(db.Text, nullable=False)
    knowledge_point_id = db.Column(db.Integer, db.ForeignKey('knowledge_points.id'))
    grade_level = db.Column(db.Integer, nullable=False)  # 7/8/9
    difficulty = db.Column(db.String(20))  # easy/medium/hard
    ai_explanation = db.Column(db.Text)
    similar_questions = db.Column(db.Text)  # JSON格式
    notes = db.Column(db.Text)  # 用户笔记
    source = db.Column(db.String(200))  # 错题来源
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_mastered = db.Column(db.Boolean, default=False)
    review_count = db.Column(db.Integer, default=0)
    last_review_at = db.Column(db.DateTime)

    # 关系
    knowledge_point = db.relationship('KnowledgePoint', backref='mistakes')
    tags = db.relationship('Tag', secondary='mistake_tags', backref='mistakes')


class KnowledgePoint(db.Model):
    """知识点表"""
    __tablename__ = 'knowledge_points'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 代数/几何/统计等
    grade_level = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    semester = db.Column(db.Integer)   # 1=上册, 2=下册
    chapter = db.Column(db.String(50)) # 章节，如 "第三章"
    parent_id = db.Column(db.Integer, db.ForeignKey('knowledge_points.id'))

    # 自引用关系
    children = db.relationship('KnowledgePoint', backref=db.backref('parent', remote_side=[id]))


class AnalysisReport(db.Model):
    """分析报告表"""
    __tablename__ = 'analysis_reports'

    id = db.Column(db.Integer, primary_key=True)
    report_date = db.Column(db.Date, nullable=False)
    total_mistakes = db.Column(db.Integer, default=0)
    weak_points = db.Column(db.Text)  # JSON格式
    improvement_suggestions = db.Column(db.Text)
    statistics = db.Column(db.Text)  # JSON格式
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Tag(db.Model):
    """标签表"""
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(20))  # 标签颜色


class MistakeTag(db.Model):
    """错题-标签关联表"""
    __tablename__ = 'mistake_tags'

    mistake_id = db.Column(db.Integer, db.ForeignKey('mistakes.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), primary_key=True)


class ClassicQuestion(db.Model):
    """经典题表"""
    __tablename__ = 'classic_questions'

    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    question_text = db.Column(db.Text, nullable=False)
    knowledge_point_id = db.Column(db.Integer, db.ForeignKey('knowledge_points.id'))
    grade_level = db.Column(db.Integer, nullable=False)  # 7/8/9
    difficulty = db.Column(db.String(20))  # easy/medium/hard
    ai_explanation = db.Column(db.Text)
    notes = db.Column(db.Text)  # 用户笔记
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_mastered = db.Column(db.Boolean, default=False)
    review_count = db.Column(db.Integer, default=0)
    last_review_at = db.Column(db.DateTime)

    # 关系
    knowledge_point = db.relationship('KnowledgePoint', backref='classic_questions')
    tags = db.relationship('Tag', secondary='classic_question_tags', backref='classic_questions')


class ClassicQuestionTag(db.Model):
    """经典题-标签关联表"""
    __tablename__ = 'classic_question_tags'

    classic_question_id = db.Column(db.Integer, db.ForeignKey('classic_questions.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), primary_key=True)
