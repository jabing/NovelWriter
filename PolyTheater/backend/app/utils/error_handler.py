"""统一错误处理中间件

提供标准化的错误响应格式、错误码定义和全局错误处理装饰器。
"""
from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, Type, Union

from flask import Flask, jsonify, request
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """标准错误码定义"""
    # 客户端错误 (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    
    # 服务端错误 (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    
    # 业务逻辑错误
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    INVALID_STATE = "INVALID_STATE"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


@dataclass
class ErrorDefinition:
    """错误定义"""
    status: int
    message: str
    description: str = ""


# 错误码定义表
ERROR_CODE_DEFINITIONS: Dict[ErrorCode, ErrorDefinition] = {
    # 客户端错误
    ErrorCode.VALIDATION_ERROR: ErrorDefinition(
        status=400,
        message="Validation failed",
        description="请求数据验证失败"
    ),
    ErrorCode.INVALID_REQUEST: ErrorDefinition(
        status=400,
        message="Invalid request",
        description="请求格式无效"
    ),
    ErrorCode.BAD_REQUEST: ErrorDefinition(
        status=400,
        message="Bad request",
        description="请求无效"
    ),
    ErrorCode.UNAUTHORIZED: ErrorDefinition(
        status=401,
        message="Unauthorized",
        description="未授权访问"
    ),
    ErrorCode.FORBIDDEN: ErrorDefinition(
        status=403,
        message="Forbidden",
        description="禁止访问"
    ),
    ErrorCode.NOT_FOUND: ErrorDefinition(
        status=404,
        message="Resource not found",
        description="资源不存在"
    ),
    ErrorCode.RESOURCE_NOT_FOUND: ErrorDefinition(
        status=404,
        message="Resource not found",
        description="指定的资源不存在"
    ),
    ErrorCode.CONFLICT: ErrorDefinition(
        status=409,
        message="Conflict",
        description="资源冲突"
    ),
    ErrorCode.DUPLICATE_RESOURCE: ErrorDefinition(
        status=409,
        message="Duplicate resource",
        description="资源已存在"
    ),
    ErrorCode.OPERATION_NOT_ALLOWED: ErrorDefinition(
        status=403,
        message="Operation not allowed",
        description="操作不被允许"
    ),
    ErrorCode.RATE_LIMIT_EXCEEDED: ErrorDefinition(
        status=429,
        message="Rate limit exceeded",
        description="请求频率超限"
    ),
    
    # 服务端错误
    ErrorCode.INTERNAL_ERROR: ErrorDefinition(
        status=500,
        message="Internal server error",
        description="服务器内部错误"
    ),
    ErrorCode.SERVICE_UNAVAILABLE: ErrorDefinition(
        status=503,
        message="Service unavailable",
        description="服务不可用"
    ),
    ErrorCode.DATABASE_ERROR: ErrorDefinition(
        status=500,
        message="Database error",
        description="数据库操作失败"
    ),
    ErrorCode.EXTERNAL_SERVICE_ERROR: ErrorDefinition(
        status=502,
        message="External service error",
        description="外部服务调用失败"
    ),
    ErrorCode.INVALID_STATE: ErrorDefinition(
        status=500,
        message="Invalid state",
        description="系统状态异常"
    ),
}


@dataclass
class AppError(Exception):
    """应用错误基类"""
    error_code: ErrorCode
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def to_response(self) -> Tuple[Dict[str, Any], int]:
        """转换为错误响应"""
        definition = ERROR_CODE_DEFINITIONS.get(
            self.error_code,
            ERROR_CODE_DEFINITIONS[ErrorCode.INTERNAL_ERROR]
        )
        
        return {
            "error": {
                "code": self.error_code.value,
                "message": self.message or definition.message,
                "details": self.details or {}
            }
        }, definition.status


class APIError(AppError):
    """API 错误"""
    pass


class ValidationError(APIError):
    """验证错误"""
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details or {}
        )


class NotFoundError(APIError):
    """资源不存在错误"""
    def __init__(self, resource: str = "Resource", identifier: Optional[str] = None):
        message = f"{resource} not found"
        details = {}
        if identifier:
            details["identifier"] = identifier
        super().__init__(
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message,
            details=details
        )


class ConflictError(APIError):
    """资源冲突错误"""
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.CONFLICT,
            message=message,
            details=details or {}
        )


class UnauthorizedError(APIError):
    """未授权错误"""
    def __init__(self, message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.UNAUTHORIZED,
            message=message,
            details=details or {}
        )


class ForbiddenError(APIError):
    """禁止访问错误"""
    def __init__(self, message: str = "Forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.FORBIDDEN,
            message=message,
            details=details or {}
        )


class InternalError(APIError):
    """内部错误"""
    def __init__(self, message: str = "Internal server error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.INTERNAL_ERROR,
            message=message,
            details=details or {}
        )


class DatabaseError(APIError):
    """数据库错误"""
    def __init__(self, message: str = "Database error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.DATABASE_ERROR,
            message=message,
            details=details or {}
        )


def error_response(
    error_code: Union[ErrorCode, str],
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    status: Optional[int] = None
) -> Tuple[Any, int]:
    """生成标准错误响应
    
    Args:
        error_code: 错误码 (ErrorCode 枚举或字符串)
        message: 错误消息 (可选，默认使用错误码定义的消息)
        details: 详细错误信息 (可选)
        status: HTTP 状态码 (可选，默认使用错误码定义的状态码)
    
    Returns:
        Tuple[Response, int]: Flask 响应元组
    """
    if isinstance(error_code, str):
        try:
            error_code = ErrorCode(error_code)
        except ValueError:
            error_code = ErrorCode.INTERNAL_ERROR
    
    definition = ERROR_CODE_DEFINITIONS.get(
        error_code,
        ERROR_CODE_DEFINITIONS[ErrorCode.INTERNAL_ERROR]
    )
    
    response = {
        "error": {
            "code": error_code.value,
            "message": message or definition.message,
            "details": details or {}
        }
    }
    
    return jsonify(response), status or definition.status


def handle_api_errors(f: Callable[..., Any]) -> Callable[..., Any]:
    """API 错误处理装饰器
    
    自动捕获并转换常见异常为标准错误响应。
    
    Usage:
        @handle_api_errors
        def my_api_endpoint():
            ...
    """
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return f(*args, **kwargs)
        except PydanticValidationError as e:
            # Pydantic 验证错误
            errors = e.errors()  # type: ignore[attr-defined]
            error_details = {
                "fields": [
                    {"field": err["loc"], "message": err["msg"]}
                    for err in errors
                ]
            }
            response, status = error_response(
                ErrorCode.VALIDATION_ERROR,
                message="Validation failed",
                details=error_details
            )
            logger.warning("Validation error: %s", errors)
            return response, status
        except AppError as e:
            # 应用错误直接返回
            response, status = e.to_response()
            logger.warning("API error: %s - %s", e.error_code.value, e.message)
            return response, status
        except Exception as e:
            # 未知错误
            logger.exception("Unexpected error in %s: %s", f.__name__, str(e))
            response, status = error_response(
                ErrorCode.INTERNAL_ERROR,
                message="An unexpected error occurred"
            )
            return response, status
    return wrapper


def init_error_handlers(app: Flask) -> None:
    """初始化 Flask 应用的全局错误处理器
    
    Args:
        app: Flask 应用实例
    """
    
    @app.errorhandler(404)
    def not_found_error(error):
        return error_response(
            ErrorCode.NOT_FOUND,
            message="The requested resource was not found"
        )
    
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        return error_response(
            ErrorCode.INVALID_REQUEST,
            message="Method not allowed"
        )
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.exception("Internal server error: %s", error)
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            message="An internal server error occurred"
        )
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.exception("Unhandled exception: %s", error)
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred"
        )
    
    logger.info("Error handlers initialized")


def get_error_code_info(error_code: Union[ErrorCode, str]) -> Optional[ErrorDefinition]:
    """获取错误码详细信息
    
    Args:
        error_code: 错误码
    
    Returns:
        ErrorDefinition 或 None
    """
    if isinstance(error_code, str):
        try:
            error_code = ErrorCode(error_code)
        except ValueError:
            return None
    
    return ERROR_CODE_DEFINITIONS.get(error_code)


def list_error_codes() -> Dict[str, Dict[str, Any]]:
    """列出所有错误码及其定义
    
    Returns:
        错误码字典 {code: {status, message, description}}
    """
    return {
        code.value: {
            "status": definition.status,
            "message": definition.message,
            "description": definition.description
        }
        for code, definition in ERROR_CODE_DEFINITIONS.items()
    }
