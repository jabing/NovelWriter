# 错误码文档

本文档定义了 PolyTheater API 的统一错误响应格式和错误码。

## 错误响应格式

所有 API 错误都遵循统一的响应格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "additional": "context"
    }
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | string | 错误码标识符，用于程序化处理 |
| `message` | string | 人类可读的错误描述 |
| `details` | object | 可选的详细错误信息，包含上下文数据 |

## 错误码列表

### 客户端错误 (4xx)

#### VALIDATION_ERROR
- **状态码**: 400
- **消息**: Validation failed
- **描述**: 请求数据验证失败
- **示例**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "fields": [
        {"field": ["name"], "message": "field required"},
        {"field": ["age"], "message": "value is not a valid integer"}
      ]
    }
  }
}
```

#### INVALID_REQUEST
- **状态码**: 400
- **消息**: Invalid request
- **描述**: 请求格式无效

#### BAD_REQUEST
- **状态码**: 400
- **消息**: Bad request
- **描述**: 请求无效

#### UNAUTHORIZED
- **状态码**: 401
- **消息**: Unauthorized
- **描述**: 未授权访问

#### FORBIDDEN
- **状态码**: 403
- **消息**: Forbidden
- **描述**: 禁止访问

#### NOT_FOUND
- **状态码**: 404
- **消息**: Resource not found
- **描述**: 资源不存在

#### RESOURCE_NOT_FOUND
- **状态码**: 404
- **消息**: Resource not found
- **描述**: 指定的资源不存在
- **示例**:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Character not found",
    "details": {
      "identifier": "char_123"
    }
  }
}
```

#### CONFLICT
- **状态码**: 409
- **消息**: Conflict
- **描述**: 资源冲突

#### DUPLICATE_RESOURCE
- **状态码**: 409
- **消息**: Duplicate resource
- **描述**: 资源已存在
- **示例**:
```json
{
  "error": {
    "code": "DUPLICATE_RESOURCE",
    "message": "Character with this entity_id already exists",
    "details": {}
  }
}
```

#### OPERATION_NOT_ALLOWED
- **状态码**: 403
- **消息**: Operation not allowed
- **描述**: 操作不被允许

#### RATE_LIMIT_EXCEEDED
- **状态码**: 429
- **消息**: Rate limit exceeded
- **描述**: 请求频率超限

### 服务端错误 (5xx)

#### INTERNAL_ERROR
- **状态码**: 500
- **消息**: Internal server error
- **描述**: 服务器内部错误

#### SERVICE_UNAVAILABLE
- **状态码**: 503
- **消息**: Service unavailable
- **描述**: 服务不可用

#### DATABASE_ERROR
- **状态码**: 500
- **消息**: Database error
- **描述**: 数据库操作失败

#### EXTERNAL_SERVICE_ERROR
- **状态码**: 502
- **消息**: External service error
- **描述**: 外部服务调用失败

#### INVALID_STATE
- **状态码**: 500
- **消息**: Invalid state
- **描述**: 系统状态异常

## 使用示例

### Python 后端

```python
from app.utils.error_handler import error_response, ErrorCode, handle_api_errors

# 方式 1: 使用 error_response 函数
@characters_bp.route('/api/v1/characters/<character_id>', methods=['GET'])
def get_character(character_id: str):
    character = CharacterDB.query.filter_by(entity_id=character_id).first()
    
    if not character:
        return error_response(
            ErrorCode.RESOURCE_NOT_FOUND,
            message=f"Character not found",
            details={"identifier": character_id}
        )
    
    return jsonify(character.to_dict()), 200

# 方式 2: 使用装饰器自动处理异常
@handle_api_errors
def create_character():
    # 抛出异常会自动转换为错误响应
    if not data:
        raise ValidationError("Request body is required")
    
    character = find_character(character_id)
    if not character:
        raise NotFoundError("Character", character_id)
```

### 自定义错误类

```python
from app.utils.error_handler import (
    APIError, ValidationError, NotFoundError, 
    ConflictError, InternalError, DatabaseError
)

# 抛出预定义的错误类
def get_resource(resource_id: str):
    resource = db.query.get(resource_id)
    if not resource:
        raise NotFoundError("Resource", resource_id)

def create_user(email: str):
    existing = User.query.filter_by(email=email).first()
    if existing:
        raise ConflictError("User with this email already exists")
```

## 最佳实践

1. **使用错误码而非 HTTP 状态码进行程序化判断**
   - 客户端应该检查 `error.code` 而不是 HTTP 状态码

2. **提供有意义的错误消息**
   - 错误消息应该清晰描述问题
   - 避免泄露敏感信息

3. **使用 details 字段提供上下文**
   - 包含有助于调试的额外信息
   - 例如：字段验证错误、资源标识符等

4. **记录详细日志**
   - 在返回错误响应前记录完整的错误堆栈
   - 便于问题排查

5. **保持一致性**
   - 所有 API 端点使用相同的错误响应格式
   - 使用预定义的错误码

## 错误处理流程

```
请求 → 参数验证 → 业务逻辑 → 数据访问 → 响应
        ↓           ↓           ↓
    ValidationError  APIError   DatabaseError
        ↓           ↓           ↓
        统一错误处理器 → 标准错误响应
```

## 附录：完整错误码表

| 错误码 | 状态码 | 消息 | 描述 |
|--------|--------|------|------|
| VALIDATION_ERROR | 400 | Validation failed | 请求数据验证失败 |
| INVALID_REQUEST | 400 | Invalid request | 请求格式无效 |
| BAD_REQUEST | 400 | Bad request | 请求无效 |
| UNAUTHORIZED | 401 | Unauthorized | 未授权访问 |
| FORBIDDEN | 403 | Forbidden | 禁止访问 |
| NOT_FOUND | 404 | Resource not found | 资源不存在 |
| RESOURCE_NOT_FOUND | 404 | Resource not found | 指定的资源不存在 |
| CONFLICT | 409 | Conflict | 资源冲突 |
| DUPLICATE_RESOURCE | 409 | Duplicate resource | 资源已存在 |
| OPERATION_NOT_ALLOWED | 403 | Operation not allowed | 操作不被允许 |
| RATE_LIMIT_EXCEEDED | 429 | Rate limit exceeded | 请求频率超限 |
| INTERNAL_ERROR | 500 | Internal server error | 服务器内部错误 |
| SERVICE_UNAVAILABLE | 503 | Service unavailable | 服务不可用 |
| DATABASE_ERROR | 500 | Database error | 数据库操作失败 |
| EXTERNAL_SERVICE_ERROR | 502 | External service error | 外部服务调用失败 |
| INVALID_STATE | 500 | Invalid state | 系统状态异常 |
