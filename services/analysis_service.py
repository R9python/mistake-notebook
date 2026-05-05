"""数据分析服务"""
from datetime import datetime, timedelta
from sqlalchemy import func
from models import db, Mistake, KnowledgePoint, Tag, MistakeTag


class AnalysisService:
    """数据分析统计服务"""

    @staticmethod
    def get_mistakes_statistics(start_date=None, end_date=None, grade_level=None):
        """
        获取错题统计数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            grade_level: 年级筛选

        Returns:
            统计数据字典
        """
        query = Mistake.query

        # 日期筛选
        if start_date:
            query = query.filter(Mistake.created_at >= start_date)
        if end_date:
            query = query.filter(Mistake.created_at <= end_date)

        # 年级筛选
        if grade_level:
            query = query.filter(Mistake.grade_level == grade_level)

        total = query.count()
        mastered = query.filter(Mistake.is_mastered == True).count()
        unmastered = total - mastered

        return {
            'total': total,
            'mastered': mastered,
            'unmastered': unmastered,
            'mastery_rate': round(mastered / total * 100, 1) if total > 0 else 0
        }

    @staticmethod
    def get_knowledge_point_statistics(grade_level=None, limit=10):
        """
        获取知识点错误统计

        Args:
            grade_level: 年级筛选
            limit: 返回数量限制

        Returns:
            知识点统计列表
        """
        query = db.session.query(
            KnowledgePoint.id,
            KnowledgePoint.name,
            KnowledgePoint.category,
            func.count(Mistake.id).label('total_count'),
            func.sum(func.cast(Mistake.is_mastered, db.Integer)).label('mastered_count')
        ).join(Mistake).group_by(KnowledgePoint.id)

        if grade_level:
            query = query.filter(KnowledgePoint.grade_level == grade_level)

        results = query.order_by(func.count(Mistake.id).desc()).limit(limit).all()

        statistics = []
        for row in results:
            total = row.total_count
            mastered = row.mastered_count or 0
            unmastered = total - mastered
            error_rate = round(unmastered / total * 100, 1) if total > 0 else 0

            statistics.append({
                'knowledge_point_id': row.id,
                'knowledge_point': row.name,
                'category': row.category,
                'total_count': total,
                'mastered_count': mastered,
                'unmastered_count': unmastered,
                'error_rate': error_rate
            })

        return statistics

    @staticmethod
    def get_weak_points_data(grade_level=None, min_count=2):
        """
        获取薄弱知识点数据（用于AI分析）

        Args:
            grade_level: 年级筛选
            min_count: 最小错题数量（过滤掉错题太少的知识点）

        Returns:
            薄弱知识点数据列表
        """
        query = db.session.query(
            KnowledgePoint.name,
            func.count(Mistake.id).label('count'),
            func.sum(func.cast(Mistake.is_mastered, db.Integer)).label('mastered_count')
        ).join(Mistake).filter(
            Mistake.is_mastered == False
        ).group_by(KnowledgePoint.id)

        if grade_level:
            query = query.filter(KnowledgePoint.grade_level == grade_level)

        results = query.having(func.count(Mistake.id) >= min_count).all()

        weak_points = []
        for row in results:
            # 获取该知识点的示例题目
            examples = db.session.query(Mistake.question_text).filter(
                Mistake.knowledge_point_id == KnowledgePoint.query.filter_by(name=row.name).first().id,
                Mistake.is_mastered == False
            ).limit(3).all()

            weak_points.append({
                'knowledge_point': row.name,
                'count': row.count,
                'mastered_count': row.mastered_count or 0,
                'examples': [ex[0][:100] + '...' if len(ex[0]) > 100 else ex[0] for ex in examples]
            })

        return weak_points

    @staticmethod
    def get_weak_tags_data(grade_level=None, min_count=2):
        """
        获取薄弱标签数据（用于AI分析）

        Args:
            grade_level: 年级筛选
            min_count: 最小错题数量（过滤掉错题太少的标签）

        Returns:
            薄弱标签数据列表
        """
        query = db.session.query(
            Tag.id,
            Tag.name,
            Tag.color,
            func.count(MistakeTag.mistake_id).label('count'),
            func.sum(func.cast(Mistake.is_mastered, db.Integer)).label('mastered_count')
        ).select_from(Tag).join(
            MistakeTag, Tag.id == MistakeTag.tag_id
        ).join(
            Mistake, MistakeTag.mistake_id == Mistake.id
        ).filter(
            Mistake.is_mastered == False
        ).group_by(Tag.id)

        if grade_level:
            query = query.filter(Mistake.grade_level == grade_level)

        results = query.having(func.count(MistakeTag.mistake_id) >= min_count).all()

        weak_tags = []
        for row in results:
            # 获取该标签的示例题目
            examples = db.session.query(Mistake.question_text).join(
                MistakeTag, Mistake.id == MistakeTag.mistake_id
            ).filter(
                MistakeTag.tag_id == row.id,
                Mistake.is_mastered == False
            ).limit(3).all()

            weak_tags.append({
                'tag': row.name,
                'count': row.count,
                'mastered_count': row.mastered_count or 0,
                'examples': [ex[0][:100] + '...' if len(ex[0]) > 100 else ex[0] for ex in examples]
            })

        return weak_tags

    @staticmethod
    def get_time_series_data(days=30, grade_level=None):
        """
        获取时间序列数据（用于趋势图）

        Args:
            days: 天数
            grade_level: 年级筛选

        Returns:
            时间序列数据
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = db.session.query(
            func.date(Mistake.created_at).label('date'),
            func.count(Mistake.id).label('count')
        ).filter(
            Mistake.created_at >= start_date
        ).group_by(func.date(Mistake.created_at))

        if grade_level:
            query = query.filter(Mistake.grade_level == grade_level)

        results = query.order_by('date').all()

        return [
            {
                'date': row.date.strftime('%Y-%m-%d'),
                'count': row.count
            }
            for row in results
        ]

    @staticmethod
    def get_difficulty_distribution(grade_level=None):
        """
        获取难度分布

        Args:
            grade_level: 年级筛选

        Returns:
            难度分布数据
        """
        query = db.session.query(
            Mistake.difficulty,
            func.count(Mistake.id).label('count')
        ).group_by(Mistake.difficulty)

        if grade_level:
            query = query.filter(Mistake.grade_level == grade_level)

        results = query.all()

        return {
            row.difficulty or 'unknown': row.count
            for row in results
        }
