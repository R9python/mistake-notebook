from .schemas import db, KnowledgePoint
from services.knowledge_points import KNOWLEDGE_POINTS_DATA

def init_db(app):
    """初始化数据库"""
    db.init_app(app)

    with app.app_context():
        db.create_all()
        # 迁移：为已存在的数据库添加 source 列
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE mistakes ADD COLUMN source VARCHAR(200)'))
                conn.commit()
        except Exception:
            pass  # 列已存在则忽略

        # 检查是否需要预填充知识点数据
        if KnowledgePoint.query.count() == 0:
            _populate_knowledge_points()
            db.session.commit()
            print("知识点数据初始化完成")


def _populate_knowledge_points():
    """预填充知识点数据"""
    for category_name, category_data in KNOWLEDGE_POINTS_DATA.items():
        for grade_level, points in category_data.items():
            for item in points:
                name, desc, semester, chapter = item
                kp = KnowledgePoint(
                    name=name,
                    category=category_name,
                    grade_level=grade_level,
                    description=desc,
                    semester=semester,
                    chapter=chapter,
                )
                db.session.add(kp)
