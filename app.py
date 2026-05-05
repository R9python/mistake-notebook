from flask import Flask, render_template
from config import Config
from models.database import init_db, db
from models.schemas import Mistake, ClassicQuestion, Tag, MistakeTag
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(Config)

# 验证配置
try:
    Config.validate()
except ValueError as e:
    print(f"配置错误: {e}")
    print("请复制.env.example为.env并填写正确的配置")
    exit(1)

# 初始化数据库
init_db(app)

# 注册路由
from routes import upload, mistakes, analysis, tags, classics

app.register_blueprint(upload.bp)
app.register_blueprint(mistakes.bp)
app.register_blueprint(analysis.bp)
app.register_blueprint(tags.bp)
app.register_blueprint(classics.bp)


@app.route('/')
def index():
    """首页概览"""
    # 统计数据
    total_mistakes = Mistake.query.count()
    total_classics = ClassicQuestion.query.count()

    # 待复习（未掌握的）
    to_review = Mistake.query.filter_by(is_mastered=False).count()

    # 薄弱标签统计（基于未掌握的错题）
    from sqlalchemy import func
    tag_stats = db.session.query(
        Tag.id,
        Tag.name,
        Tag.color,
        func.count(MistakeTag.mistake_id).label('count')
    ).join(MistakeTag).join(Mistake).filter(
        Mistake.is_mastered == False
    ).group_by(
        Tag.id
    ).order_by(
        func.count(MistakeTag.mistake_id).desc()
    ).limit(10).all()

    # 转换为字典列表供 ECharts 使用
    weak_tags = [
        {
            'id': tag.id,
            'name': tag.name,
            'color': tag.color,
            'count': tag.count
        }
        for tag in tag_stats
    ]

    return render_template('index.html',
                         total_mistakes=total_mistakes,
                         total_classics=total_classics,
                         to_review=to_review,
                         weak_tags=weak_tags)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
