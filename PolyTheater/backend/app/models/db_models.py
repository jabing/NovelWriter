"""
SQLAlchemy 数据库模型
映射到现有 dataclass，提供持久化支持
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import JSON, String, Integer, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import db
from app.models.character import Character, PerspectiveBias
from app.models.event import StoryEvent
from app.models.enums import EntityType, ThinkingStyle, NarrativeVoice


class ProjectDB(db.Model):
    """项目数据库模型"""
    __tablename__ = 'projects'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String(32), default=lambda: datetime.now().isoformat())
    updated_at: Mapped[str] = mapped_column(String(32), default=lambda: datetime.now().isoformat())
    
    characters: Mapped[List['CharacterDB']] = relationship('CharacterDB', back_populates='project')
    events: Mapped[List['StoryEventDB']] = relationship('StoryEventDB', back_populates='project')
    
    def __repr__(self) -> str:
        return f'<Project {self.name}>'


class CharacterDB(db.Model):
    """角色数据库模型"""
    __tablename__ = 'characters'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('projects.id'), nullable=True)
    
    entity_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(32), default="Character")
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    properties: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String(32), default=lambda: datetime.now().isoformat())
    updated_at: Mapped[str] = mapped_column(String(32), default=lambda: datetime.now().isoformat())
    
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    occupation: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    
    mbti: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    personality_traits: Mapped[List[str]] = mapped_column(JSON, default=list)
    core_values: Mapped[List[str]] = mapped_column(JSON, default=list)
    thinking_style: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    emotional_tone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    narrative_voice: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    perspective_bias: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    belief_graph_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    character_layer: Mapped[int] = mapped_column(Integer, default=1)
    has_pov: Mapped[bool] = mapped_column(Boolean, default=False)
    activity_level: Mapped[float] = mapped_column(Float, default=0.5)
    influence_weight: Mapped[float] = mapped_column(Float, default=1.0)
    
    bio: Mapped[str] = mapped_column(Text, default="")
    detailed_persona: Mapped[str] = mapped_column(Text, default="")
    background_story: Mapped[str] = mapped_column(Text, default="")
    motivations: Mapped[List[str]] = mapped_column(JSON, default=list)
    fears: Mapped[List[str]] = mapped_column(JSON, default=list)
    goals: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    friend_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    enemy_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    family_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    source_entity_uuid: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_entity_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    
    project: Mapped[Optional['ProjectDB']] = relationship('ProjectDB', back_populates='characters')
    
    def to_dataclass(self) -> Character:
        """转换为 Character dataclass"""
        pb = None
        if self.perspective_bias:
            pb = PerspectiveBias(
                gender_bias=self.perspective_bias.get('gender_bias', {}),
                mbti_bias=self.perspective_bias.get('mbti_bias', {}),
                cognitive_bias=self.perspective_bias.get('cognitive_bias', {})
            )
        
        return Character(
            entity_id=self.entity_id,
            entity_type=EntityType(self.entity_type) if self.entity_type else EntityType.CHARACTER,
            name=self.name,
            description=self.description,
            properties=self.properties or {},
            created_at=self.created_at,
            updated_at=self.updated_at,
            age=self.age,
            gender=self.gender,
            occupation=self.occupation,
            mbti=self.mbti,
            personality_traits=self.personality_traits or [],
            core_values=self.core_values or [],
            thinking_style=ThinkingStyle(self.thinking_style) if self.thinking_style else None,
            emotional_tone=self.emotional_tone,
            narrative_voice=NarrativeVoice(self.narrative_voice) if self.narrative_voice else None,
            perspective_bias=pb,
            belief_graph_id=self.belief_graph_id,
            character_layer=self.character_layer,
            has_pov=self.has_pov,
            activity_level=self.activity_level,
            influence_weight=self.influence_weight,
            bio=self.bio,
            detailed_persona=self.detailed_persona,
            background_story=self.background_story,
            motivations=self.motivations or [],
            fears=self.fears or [],
            goals=self.goals or [],
            friend_ids=self.friend_ids or [],
            enemy_ids=self.enemy_ids or [],
            family_ids=self.family_ids or [],
            source_entity_uuid=self.source_entity_uuid,
            source_entity_type=self.source_entity_type
        )
    
    @classmethod
    def from_dataclass(cls, character: Character) -> 'CharacterDB':
        """从 Character dataclass 创建数据库模型"""
        pb_dict = None
        if character.perspective_bias:
            pb_dict = {
                'gender_bias': character.perspective_bias.gender_bias,
                'mbti_bias': character.perspective_bias.mbti_bias,
                'cognitive_bias': character.perspective_bias.cognitive_bias
            }
        
        return cls(
            entity_id=character.entity_id,
            entity_type=character.entity_type.value if character.entity_type else "Character",
            name=character.name,
            description=character.description,
            properties=character.properties,
            created_at=character.created_at,
            updated_at=character.updated_at,
            age=character.age,
            gender=character.gender,
            occupation=character.occupation,
            mbti=character.mbti,
            personality_traits=character.personality_traits,
            core_values=character.core_values,
            thinking_style=character.thinking_style.value if character.thinking_style else None,
            emotional_tone=character.emotional_tone,
            narrative_voice=character.narrative_voice.value if character.narrative_voice else None,
            perspective_bias=pb_dict,
            belief_graph_id=character.belief_graph_id,
            character_layer=character.character_layer,
            has_pov=character.has_pov,
            activity_level=character.activity_level,
            influence_weight=character.influence_weight,
            bio=character.bio,
            detailed_persona=character.detailed_persona,
            background_story=character.background_story,
            motivations=character.motivations,
            fears=character.fears,
            goals=character.goals,
            friend_ids=character.friend_ids,
            enemy_ids=character.enemy_ids,
            family_ids=character.family_ids,
            source_entity_uuid=character.source_entity_uuid,
            source_entity_type=character.source_entity_type
        )


class StoryEventDB(db.Model):
    """故事事件数据库模型"""
    __tablename__ = 'story_events'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('projects.id'), nullable=True)
    
    entity_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(32), default="Event")
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    properties: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String(32), default=lambda: datetime.now().isoformat())
    updated_at: Mapped[str] = mapped_column(String(32), default=lambda: datetime.now().isoformat())
    
    event_type: Mapped[str] = mapped_column(String(64), default="")
    title: Mapped[str] = mapped_column(String(256), default="")
    
    participants: Mapped[List[str]] = mapped_column(JSON, default=list)
    witnesses: Mapped[List[str]] = mapped_column(JSON, default=list)
    location_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    occurred_at: Mapped[str] = mapped_column(String(32), default="")
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timeline_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    impact_level: Mapped[int] = mapped_column(Integer, default=1)
    is_milestone: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    
    who_knows: Mapped[List[str]] = mapped_column(JSON, default=list)
    public_knowledge: Mapped[bool] = mapped_column(Boolean, default=False)
    
    consequences: Mapped[List[str]] = mapped_column(JSON, default=list)
    causes: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    project: Mapped[Optional['ProjectDB']] = relationship('ProjectDB', back_populates='events')
    
    def to_dataclass(self) -> StoryEvent:
        """转换为 StoryEvent dataclass"""
        return StoryEvent(
            entity_id=self.entity_id,
            entity_type=EntityType(self.entity_type) if self.entity_type else EntityType.EVENT,
            name=self.name,
            description=self.description,
            properties=self.properties or {},
            created_at=self.created_at,
            updated_at=self.updated_at,
            event_type=self.event_type,
            title=self.title,
            participants=self.participants or [],
            witnesses=self.witnesses or [],
            location_id=self.location_id,
            occurred_at=self.occurred_at,
            duration=self.duration,
            timeline_position=self.timeline_position,
            impact_level=self.impact_level,
            is_milestone=self.is_milestone,
            is_public=self.is_public,
            who_knows=self.who_knows or [],
            public_knowledge=self.public_knowledge,
            consequences=self.consequences or [],
            causes=self.causes or []
        )
    
    @classmethod
    def from_dataclass(cls, event: StoryEvent) -> 'StoryEventDB':
        """从 StoryEvent dataclass 创建数据库模型"""
        return cls(
            entity_id=event.entity_id,
            entity_type=event.entity_type.value if event.entity_type else "Event",
            name=event.name,
            description=event.description,
            properties=event.properties,
            created_at=event.created_at,
            updated_at=event.updated_at,
            event_type=event.event_type,
            title=event.title,
            participants=event.participants,
            witnesses=event.witnesses,
            location_id=event.location_id,
            occurred_at=event.occurred_at,
            duration=event.duration,
            timeline_position=event.timeline_position,
            impact_level=event.impact_level,
            is_milestone=event.is_milestone,
            is_public=event.is_public,
            who_knows=event.who_knows,
            public_knowledge=event.public_knowledge,
            consequences=event.consequences,
            causes=event.causes
        )
