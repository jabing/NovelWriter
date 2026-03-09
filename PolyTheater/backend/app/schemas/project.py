"""Project Pydantic schemas for API request/response validation"""

from pydantic import BaseModel, Field
from typing import Optional


class ProjectCreate(BaseModel):
    """创建项目的请求模型"""
    name: str = Field(..., min_length=1, max_length=128, description="项目名称")
    description: Optional[str] = Field(None, max_length=1000, description="项目描述")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "悬疑小说项目",
                "description": "一个多视角悬疑故事的创作项目"
            }
        }


class ProjectUpdate(BaseModel):
    """更新项目的请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=128, description="项目名称")
    description: Optional[str] = Field(None, max_length=1000, description="项目描述")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "更新后的项目名称",
                "description": "更新后的项目描述"
            }
        }


class ProjectResponse(BaseModel):
    """项目响应模型"""
    id: int
    name: str
    description: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "悬疑小说项目",
                "description": "一个多视角悬疑故事的创作项目",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
