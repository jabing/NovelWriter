"""Character Pydantic schemas for API request/response validation"""

from pydantic import BaseModel, Field, field_validator
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


class ThinkingStyle(str, Enum):
    """思维风格"""
    ANALYTICAL = "analytical"
    INTUITIVE = "intuitive"
    EMOTIONAL = "emotional"


class NarrativeVoice(str, Enum):
    """叙事声音"""
    FORMAL = "formal"
    CASUAL = "casual"
    LYRICAL = "lyrical"
    INTIMATE = "intimate"


class PerspectiveBiasSchema(BaseModel):
    """视角偏向配置"""
    gender_bias: Dict[str, float] = Field(default_factory=dict)
    mbti_bias: Dict[str, float] = Field(default_factory=dict)
    cognitive_bias: Dict[str, float] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "gender_bias": {"male": 0.3, "female": 0.7},
                "mbti_bias": {"thinking": 0.6, "feeling": 0.4},
                "cognitive_bias": {"optimism": 0.8}
            }
        }


class CharacterCreate(BaseModel):
    """创建角色的请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="角色名称")
    entity_type: EntityType = Field(default=EntityType.CHARACTER, description="实体类型")
    description: Optional[str] = Field(None, max_length=500, description="角色描述")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="属性")
    
    # 基本信息
    age: Optional[int] = Field(None, ge=0, le=150, description="年龄")
    gender: Optional[str] = Field(None, max_length=50, description="性别")
    occupation: Optional[str] = Field(None, max_length=100, description="职业")
    
    # 人格特征
    mbti: Optional[str] = Field(None, max_length=10, description="MBTI 类型")
    personality_traits: List[str] = Field(default_factory=list, description="人格特征")
    core_values: List[str] = Field(default_factory=list, description="核心价值观")
    thinking_style: Optional[ThinkingStyle] = Field(None, description="思维风格")
    emotional_tone: Optional[str] = Field(None, max_length=100, description="情感基调")
    
    # 视角属性
    narrative_voice: Optional[NarrativeVoice] = Field(None, description="叙事声音")
    perspective_bias: Optional[PerspectiveBiasSchema] = Field(None, description="视角偏向")
    belief_graph_id: Optional[str] = Field(None, description="认知图谱 ID")
    
    # 角色层级
    character_layer: int = Field(default=1, ge=1, le=4, description="角色层级")
    has_pov: bool = Field(default=False, description="是否有视角")
    activity_level: float = Field(default=0.5, ge=0.0, le=1.0, description="活跃度")
    influence_weight: float = Field(default=1.0, ge=0.0, le=10.0, description="影响力权重")
    
    # 详细信息
    bio: str = Field(default="", max_length=5000, description="传记")
    detailed_persona: str = Field(default="", max_length=5000, description="详细人格")
    background_story: str = Field(default="", max_length=5000, description="背景故事")
    motivations: List[str] = Field(default_factory=list, description="动机")
    fears: List[str] = Field(default_factory=list, description="恐惧")
    goals: List[str] = Field(default_factory=list, description="目标")
    
    # 关系
    friend_ids: List[str] = Field(default_factory=list, description="朋友 ID 列表")
    enemy_ids: List[str] = Field(default_factory=list, description="敌人 ID 列表")
    family_ids: List[str] = Field(default_factory=list, description="家人 ID 列表")
    
    # 来源
    source_entity_uuid: Optional[str] = Field(None, description="源实体 UUID")
    source_entity_type: Optional[str] = Field(None, max_length=50, description="源实体类型")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "张三",
                "age": 25,
                "gender": "男",
                "occupation": "程序员",
                "mbti": "INTJ",
                "personality_traits": ["理性", "独立", "完美主义"],
                "thinking_style": "analytical",
                "narrative_voice": "formal"
            }
        }


class CharacterUpdate(BaseModel):
    """更新角色的请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="角色名称")
    entity_type: Optional[EntityType] = Field(None, description="实体类型")
    description: Optional[str] = Field(None, max_length=500, description="角色描述")
    properties: Optional[Dict[str, Any]] = Field(None, description="属性")
    
    # 基本信息
    age: Optional[int] = Field(None, ge=0, le=150, description="年龄")
    gender: Optional[str] = Field(None, max_length=50, description="性别")
    occupation: Optional[str] = Field(None, max_length=100, description="职业")
    
    # 人格特征
    mbti: Optional[str] = Field(None, max_length=10, description="MBTI 类型")
    personality_traits: Optional[List[str]] = Field(None, description="人格特征")
    core_values: Optional[List[str]] = Field(None, description="核心价值观")
    thinking_style: Optional[ThinkingStyle] = Field(None, description="思维风格")
    emotional_tone: Optional[str] = Field(None, max_length=100, description="情感基调")
    
    # 视角属性
    narrative_voice: Optional[NarrativeVoice] = Field(None, description="叙事声音")
    perspective_bias: Optional[PerspectiveBiasSchema] = Field(None, description="视角偏向")
    belief_graph_id: Optional[str] = Field(None, description="认知图谱 ID")
    
    # 角色层级
    character_layer: Optional[int] = Field(None, ge=1, le=4, description="角色层级")
    has_pov: Optional[bool] = Field(None, description="是否有视角")
    activity_level: Optional[float] = Field(None, ge=0.0, le=1.0, description="活跃度")
    influence_weight: Optional[float] = Field(None, ge=0.0, le=10.0, description="影响力权重")
    
    # 详细信息
    bio: Optional[str] = Field(None, max_length=5000, description="传记")
    detailed_persona: Optional[str] = Field(None, max_length=5000, description="详细人格")
    background_story: Optional[str] = Field(None, max_length=5000, description="背景故事")
    motivations: Optional[List[str]] = Field(None, description="动机")
    fears: Optional[List[str]] = Field(None, description="恐惧")
    goals: Optional[List[str]] = Field(None, description="目标")
    
    # 关系
    friend_ids: Optional[List[str]] = Field(None, description="朋友 ID 列表")
    enemy_ids: Optional[List[str]] = Field(None, description="敌人 ID 列表")
    family_ids: Optional[List[str]] = Field(None, description="家人 ID 列表")
    
    # 来源
    source_entity_uuid: Optional[str] = Field(None, description="源实体 UUID")
    source_entity_type: Optional[str] = Field(None, max_length=50, description="源实体类型")


class CharacterResponse(BaseModel):
    """角色响应模型"""
    id: str
    entity_id: str
    entity_type: str
    name: str
    description: Optional[str]
    properties: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str
    age: Optional[int]
    gender: Optional[str]
    occupation: Optional[str]
    mbti: Optional[str]
    personality_traits: List[str]
    core_values: List[str]
    thinking_style: Optional[str]
    emotional_tone: Optional[str]
    narrative_voice: Optional[str]
    perspective_bias: Optional[Dict[str, Any]]
    belief_graph_id: Optional[str]
    character_layer: int
    has_pov: bool
    activity_level: float
    influence_weight: float
    bio: str
    detailed_persona: str
    background_story: str
    motivations: List[str]
    fears: List[str]
    goals: List[str]
    friend_ids: List[str]
    enemy_ids: List[str]
    family_ids: List[str]
    source_entity_uuid: Optional[str]
    source_entity_type: Optional[str]

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "entity_id": "char-001",
                "entity_type": "Character",
                "name": "张三",
                "age": 25,
                "gender": "男",
                "occupation": "程序员",
                "mbti": "INTJ",
                "thinking_style": "analytical",
                "narrative_voice": "formal"
            }
        }
