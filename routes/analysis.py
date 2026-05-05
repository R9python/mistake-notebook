"""分析报告路由"""
from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, date
from models import db, AnalysisReport
from services.analysis_service import AnalysisService
from services.ai_service import AIService
import json

bp = Blueprint('analysis', __name__, url_prefix='/analysis')


@bp.route('/')
def analysis_page():
    """分析报告页面"""
    # 获取最近的报告列表
    reports = AnalysisReport.query.order_by(
        AnalysisReport.created_at.desc()
    ).limit(10).all()

    return render_template('analysis.html', reports=reports)


@bp.route('/current')
def current_analysis():
    """当前薄弱环节分析"""
    grade_level = request.args.get('grade', type=int)

    # 获取统计数据
    analysis_service = AnalysisService()
    stats = analysis_service.get_mistakes_statistics(grade_level=grade_level)
    kp_stats = analysis_service.get_knowledge_point_statistics(
        grade_level=grade_level,
        limit=10
    )

    return jsonify({
        'success': True,
        'statistics': stats,
        'knowledge_points': kp_stats
    })


@bp.route('/generate', methods=['POST'])
def generate_report():
    """
    生成新的分析报告

    JSON body:
        - grade_level: 年级（可选）
    """
    data = request.get_json() or {}
    grade_level = data.get('grade_level')

    try:
        analysis_service = AnalysisService()

        # 获取薄弱标签数据（改为基于标签统计）
        weak_tags_data = analysis_service.get_weak_tags_data(
            grade_level=grade_level,
            min_count=2
        )

        if not weak_tags_data:
            return jsonify({
                'error': '错题数据不足，无法生成分析报告（每个标签至少需要2道错题）'
            }), 400

        # 使用AI分析（调用新的标签分析方法）
        ai_service = AIService()
        analysis_result = ai_service.analyze_weak_tags(weak_tags_data)

        # 获取总体统计
        stats = analysis_service.get_mistakes_statistics(grade_level=grade_level)

        # 保存报告
        report = AnalysisReport(
            report_date=date.today(),
            total_mistakes=stats['total'],
            weak_points=json.dumps(
                analysis_result.get('weak_tags_ranking', []),
                ensure_ascii=False
            ),
            improvement_suggestions=analysis_result.get('analysis', ''),
            statistics=json.dumps({
                'mastery_rate': stats['mastery_rate'],
                'grade_level': grade_level
            }, ensure_ascii=False)
        )

        db.session.add(report)
        db.session.commit()

        return jsonify({
            'success': True,
            'report_id': report.id,
            'weak_tags': analysis_result.get('weak_tags_ranking', []),
            'analysis': analysis_result.get('analysis', ''),
            'suggestions': analysis_result.get('suggestions', [])
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:report_id>')
def view_report(report_id):
    """查看历史报告"""
    report = AnalysisReport.query.get_or_404(report_id)

    try:
        weak_points = json.loads(report.weak_points) if report.weak_points else []
        statistics = json.loads(report.statistics) if report.statistics else {}
    except:
        weak_points = []
        statistics = {}

    return jsonify({
        'success': True,
        'report': {
            'id': report.id,
            'report_date': report.report_date.strftime('%Y-%m-%d'),
            'total_mistakes': report.total_mistakes,
            'weak_points': weak_points,
            'analysis': report.improvement_suggestions,
            'statistics': statistics,
            'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })


@bp.route('/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    """删除历史报告"""
    report = AnalysisReport.query.get_or_404(report_id)
    try:
        db.session.delete(report)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/statistics')
def get_statistics():
    """
    获取统计数据（用于图表）

    Query params:
        - grade: 年级筛选
        - days: 时间范围（天数）
    """
    grade_level = request.args.get('grade', type=int)
    days = request.args.get('days', 30, type=int)

    analysis_service = AnalysisService()

    # 时间序列数据
    time_series = analysis_service.get_time_series_data(
        days=days,
        grade_level=grade_level
    )

    # 难度分布
    difficulty_dist = analysis_service.get_difficulty_distribution(
        grade_level=grade_level
    )

    # 知识点统计
    kp_stats = analysis_service.get_knowledge_point_statistics(
        grade_level=grade_level,
        limit=10
    )

    return jsonify({
        'success': True,
        'time_series': time_series,
        'difficulty_distribution': difficulty_dist,
        'knowledge_points': kp_stats
    })
