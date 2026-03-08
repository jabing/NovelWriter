"""Event Pydantic schemas for API request/response validation"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class EntityType(str, Enum):
    """实体类型"""
    CHARACTER = "Character"
    LOCATION = "Location"
    ITEM = "Item"
    EVENT = "Event"
    CONCEPT = "Concept"
    ORGANIZATION = "Organization"


class EventCreate(BaseModel):
    """创建事件的请求模型"""
    name: str = Field(..., min_length=1, max_length=200, description="事件名称")
    entity_type: EntityType = Field(default=EntityType.EVENT, description="实体类型")
    description: Optional[str] = Field(None, max_length=1000, description="事件描述")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="属性")
    
    # 事件信息
    event_type: str = Field(default="", max_length=100, description="事件类型")
    title: str = Field(default="", max_length=200, description="事件标题")
    description_detail: str = Field(default="", max_length=2000, description="事件详细描述")
    
    # 参与者
    participants: List[str] = Field(default_factory=list, description="参与者 ID 列表")
    witnesses: List[str] = Field(default_factory=list, description="目击者 ID 列表")
    location_id: Optional[str] = Field(None, description="地点 ID")
    
    # 时间信息
    occurred_at: str = Field(default="", max_length=50, description="发生时间")
    duration: Optional[int] = Field(None, ge=0, description="持续时间 (分钟)")
    timeline_position: Optional[int] = Field(None, description="时间线位置")
    
    # 影响
    impact_level: int = Field(default=1, ge=1, le=10, description="影响等级")
    is_milestone: bool = Field(default=False, description="是否为里程碑事件")
    is_public: bool = Field(default=False, description="是否公开")
    
    # 知识传播
    who_knows: List[str] = Field(default_factory=list, description="知情者 ID 列表")
    public_knowledge: bool = Field(default=False, description="是否公开知识")
    
    # 因果关系
    consequences: List[str] = Field(default_factory=list, description="后果列表")
    causes: List[str] = Field(default_factory=list, description="原因列表")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "第一次相遇",
                "event_type": "meeting",
                "title": "咖啡馆的邂逅",
                "description_detail": "在一个雨天的下午，两人在咖啡馆相遇",
                "participants": ["char-001", "char-002"],
                "occurred_at": "2024-01-15T14:30:00",
                "impact_level": 5,
                "is_milestone": True
            }
        }


class EventUpdate(BaseModel):
    """更新事件的请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="事件名称")
    entity_type: Optional[EntityType] = Field(None, description="实体类型")
    description: Optional[str] = Field(None, max_length=1000, description="事件描述")
    properties: Optional[Dict[str, Any]] = Field(None, description="属性")
    
    # 事件信息
    event_type: Optional[str] = Field(None, max_length=100, description="事件类型")
    title: Optional[str] = Field(None, max_length=200, description="事件标题")
    description_detail: Optional[str] = Field(None, max_length=2000, description="事件详细描述")
    
    # 参与者
    participants: Optional[List[str]] = Field(None, description="参与者 ID 列表")
    witnesses: Optional[List[str]] = Field(None, description="目击者 ID 列表")
    location_id: Optional[str] = Field(None, description="地点 ID")
    
    # 时间信息
    occurred_at: Optional[str] = Field(None, max_length=50, description="发生时间")
    duration: Optional[int] = Field(None, ge=0, description="持续时间 (分钟)")
    timeline_position: Optional[int] = Field(None, description="时间线位置")
    
    # 影响
    impact_level: Optional[int] = Field(None, ge=1, le=10, description="影响等级")
    is_milestone: Optional[bool] = Field(None, description="是否为里程碑事件")
    is_public: Optional[bool] = Field(None, description="是否公开")
    
    # 知识传播
    who_knows: Optional[List[str]] = Field(None, description="知情者 ID 列表")
    public_knowledge: Optional[bool] = Field(None, description="是否公开知识")
    
    # 因果关系
    consequences: Optional[List[str]] = Field(None, description="后果列表")
    causes: Optional[List[str]] = Field(None, description="原因列表")


class EventResponse(BaseModel):
    """事件响应模型"""
    id: str
    entity_id: str
    entity_type: str
    name: str
    description: Optional[str]
    properties: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str
    
    # 事件信息
    event_type: str
    title: str
    description_detail: str
    
    # 参与者
    participants: List[str]
    witnesses: List[str]
    location_id: Optional[str]
    
    # 时间信息
    occurred_at: str
    duration: Optional[int]
    timeline_position: Optional[int]
    
    # 影响
    impact_level: int
    is_milestone: bool
    is_public: bool
    
    # 知识传播
    who_knows: List[str]
    public_knowledge: bool
    
    # 因果关系
    consequences: List[str]
    causes: List[str]

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "entity_id": "event-001",
                "entity_type": "Event",
                "name": "第一次相遇",
                "event_type": "meeting",
                "title": "咖啡馆的邂逅",
                "participants": ["char-001", "char-002"],
                "impact_level": 5,
                "is_milestone": True
            }
        }
