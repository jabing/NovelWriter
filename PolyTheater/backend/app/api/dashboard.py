"""
Dashboard API - 统计和活动日志
"""
from flask import Blueprint, jsonify
from datetime import datetime, timezone, timedelta
from app.database import db
from app.models.db_models import ProjectDB, CharacterDB, StoryEventDB

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取 Dashboard 统计数据"""
    try:
        # 项目统计
        projects_count = ProjectDB.query.count()
        
        # 角色统计
        characters_count = CharacterDB.query.count()
        
        # 事件统计
        events_count = StoryEventDB.query.count()
        
        # 计算活跃项目（最近 7 天有更新）
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        active_projects = ProjectDB.query.filter(
            ProjectDB.updated_at >= seven_days_ago
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'projects': projects_count,
                'active_projects': active_projects,
                'characters': characters_count,
                'events': events_count
            },
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'STATS_ERROR',
                'message': f'Failed to get stats: {str(e)}'
            }
        }), 500


@dashboard_bp.route('/activity', methods=['GET'])
def get_activity():
    """获取最近活动日志"""
    try:
        activities = []
        
        # 最近创建的项目
        recent_projects = ProjectDB.query.order_by(
            ProjectDB.created_at.desc()
        ).limit(5).all()
        
        for project in recent_projects:
            activities.append({
                'id': f'project_{project.id}',
                'type': 'project',
                'action': 'created',
                'entity_name': project.name,
                'entity_id': project.id,
                'timestamp': project.created_at.isoformat().replace('+00:00', 'Z') if project.created_at else None
            })
        
        # 最近创建的角色
        recent_characters = CharacterDB.query.order_by(
            CharacterDB.created_at.desc()
        ).limit(5).all()
        
        for character in recent_characters:
            activities.append({
                'id': f'character_{character.id}',
                'type': 'character',
                'action': 'created',
                'entity_name': character.name,
                'entity_id': character.id,
                'timestamp': character.created_at.isoformat().replace('+00:00', 'Z') if character.created_at else None
            })
        
        # 按时间排序
        activities.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        
        # 返回最近 10 条
        activities = activities[:10]
        
        return jsonify({
            'success': True,
            'data': activities,
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'ACTIVITY_ERROR',
                'message': f'Failed to get activity: {str(e)}'
            }
        }), 500


@dashboard_bp.route('/health/detailed', methods=['GET'])
def get_detailed_health():
    """获取详细的系统健康信息"""
    import time
    
    try:
        # 测试数据库连接
        db_start = time.time()
        with db.engine.connect() as conn:
            conn.execute(db.text('SELECT 1'))
        db_time = (time.time() - db_start) * 1000  # ms
        
        db_status = 'connected'
    except Exception as e:
        db_status = 'disconnected'
        db_time = None
    
    return jsonify({
        'success': True,
        'data': {
            'database': {
                'status': db_status,
                'response_time_ms': db_time
            },
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
    }), 200
