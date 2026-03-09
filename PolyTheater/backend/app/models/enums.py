"""枚举类型定义"""
from enum import Enum


class EntityType(Enum):
    """实体类型"""
    CHARACTER = "Character"        # 人物
    LOCATION = "Location"          # 地点
    ITEM = "Item"                  # 物品
    EVENT = "Event"                # 事件
    CONCEPT = "Concept"            # 概念
    ORGANIZATION = "Organization"  # 组织
    BELIEF = "Belief"              # 信念


class RelationType(Enum):
    """关系类型"""
    # 人物关系
    LOVES = "loves"
    HATES = "hates"
    KNOWS = "knows"
    FAMILY_OF = "family_of"
    FRIEND_OF = "friend_of"
    ENEMY_OF = "enemy_of"
    
    # 物品关系
    OWNS = "owns"
    USES = "uses"
    
    # 地点关系
    LOCATED_IN = "located_in"
    VISITED = "visited"
    
    # 事件关系
    PARTICIPATES_IN = "participates_in"
    WITNESSES = "witnesses"
    CAUSES = "causes"


class CharacterLayer(Enum):
    """角色层级"""
    CORE_PROTAGONIST = 1      # 核心主角 (2-5个)
    IMPORTANT_SUPPORTING = 2  # 重要配角 (10-20个)
    MINOR_SUPPORTING = 3      # 普通配角 (50-100个)
    THE_CROWD = 4            # 社会公众 (100-1000+个)


class ThinkingStyle(Enum):
    """思维风格"""
    ANALYTICAL = "analytical"    # 分析型
    INTUITIVE = "intuitive"      # 直觉型
    EMOTIONAL = "emotional"      # 情感型


class NarrativeVoice(Enum):
    """叙事声音"""
    FORMAL = "formal"        # 正式
    CASUAL = "casual"        # 随意
    LYRICAL = "lyrical"      # 抒情
    INTIMATE = "intimate"    # 亲密
