"""项目管理 REST API"""
import logging
from datetime import datetime
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)

from app.database import db
from app.utils.error_handler import error_response, ErrorCode

projects_bp = Blueprint('projects', __name__)


def _project_to_dict(project) -> Dict[str, Any]:
    """Convert ProjectDB model to dictionary for JSON response"""
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


@projects_bp.route('/api/projects', methods=['GET'])
def list_projects():
    """列出所有项目"""
    try:
        from app.models.db_models import ProjectDB
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        pagination = ProjectDB.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        projects_list = [_project_to_dict(p) for p in pagination.items]
        
        return jsonify({
            "projects": projects_list,
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages
        }), 200
    
    except ImportError:
        return jsonify({"projects": [], "total": 0, "page": 1, "per_page": 20, "pages": 0}), 200
    except Exception as e:
        logger.exception("Failed to list projects")
        return error_response(ErrorCode.DATABASE_ERROR, message=f"Failed to list projects: {str(e)}")


@projects_bp.route('/api/projects', methods=['POST'])
def create_project():
    """创建项目"""
    from app.schemas import ProjectCreate
    
    data = request.get_json()
    
    if not data:
        return error_response(ErrorCode.INVALID_REQUEST, message="Request body is required")
    
    try:
        validated_data = ProjectCreate(**data)
    except PydanticValidationError as e:
        errors = e.errors()
        error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in errors]
        return error_response(
            ErrorCode.VALIDATION_ERROR,
            message="; ".join(error_messages),
            details={"fields": [{"field": err["loc"], "message": err["msg"]} for err in errors]}
        )
    
    try:
        from app.models.db_models import ProjectDB
        
        now = datetime.now().isoformat()
        
        project = ProjectDB(
            name=validated_data.name,
            description=validated_data.description or "",
            created_at=now,
            updated_at=now,
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify(_project_to_dict(project)), 201
    
    except ImportError:
        return error_response(ErrorCode.INTERNAL_ERROR, message="Project model not available")
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to create project")
        return error_response(ErrorCode.DATABASE_ERROR, message=f"Failed to create project: {str(e)}")


@projects_bp.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id: int):
    """获取项目详情"""
    try:
        from app.models.db_models import ProjectDB
        
        project = ProjectDB.query.get(project_id)
        
        if not project:
            return error_response(ErrorCode.RESOURCE_NOT_FOUND, message="Project not found", details={"id": project_id})
        
        return jsonify(_project_to_dict(project)), 200
    
    except ImportError:
        return error_response(ErrorCode.INTERNAL_ERROR, message="Project model not available")
    except Exception as e:
        logger.exception("Failed to get project")
        return error_response(ErrorCode.DATABASE_ERROR, message=f"Failed to get project: {str(e)}")


@projects_bp.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id: int):
    """更新项目"""
    from app.schemas import ProjectUpdate
    
    try:
        from app.models.db_models import ProjectDB
        
        project = ProjectDB.query.get(project_id)
        
        if not project:
            return error_response(ErrorCode.RESOURCE_NOT_FOUND, message="Project not found", details={"id": project_id})
        
        data = request.get_json()
        
        if not data:
            return error_response(ErrorCode.INVALID_REQUEST, message="Request body is required")
        
        try:
            validated_data = ProjectUpdate(**data)
        except PydanticValidationError as e:
            errors = e.errors()
            error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in errors]
            return error_response(
                ErrorCode.VALIDATION_ERROR,
                message="; ".join(error_messages),
                details={"fields": [{"field": err["loc"], "message": err["msg"]} for err in errors]}
            )
        
        update_fields = validated_data.model_dump(exclude_unset=True)
        
        for field, value in update_fields.items():
            if value is not None:
                setattr(project, field, value)
        
        project.updated_at = datetime.now().isoformat()
        
        db.session.commit()
        
        return jsonify(_project_to_dict(project)), 200
    
    except ImportError:
        return error_response(ErrorCode.INTERNAL_ERROR, message="Project model not available")
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to update project")
        return error_response(ErrorCode.DATABASE_ERROR, message=f"Failed to update project: {str(e)}")


@projects_bp.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id: int):
    """删除项目"""
    try:
        from app.models.db_models import ProjectDB
        
        project = ProjectDB.query.get(project_id)
        
        if not project:
            return error_response(ErrorCode.RESOURCE_NOT_FOUND, message="Project not found", details={"id": project_id})
        
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({"message": "Project deleted successfully"}), 200
    
    except ImportError:
        return error_response(ErrorCode.INTERNAL_ERROR, message="Project model not available")
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to delete project")
        return error_response(ErrorCode.DATABASE_ERROR, message=f"Failed to delete project: {str(e)}")
