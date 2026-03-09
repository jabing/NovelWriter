"""BeliefGraphManager 单元测试

测试信念图谱管理器的重构实现，验证使用 StoryGraphManager 存储信念的功能。
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from app.agents.belief_graph_manager import BeliefGraphManager, Belief, BeliefGraphError
from app.graph.story_graph_manager import StoryGraphManager
from app.models import StoryEntity, EntityType


class TestBeliefGraphManager:
    """BeliefGraphManager 测试类"""
    
    @pytest.fixture
    def mock_graph_manager(self):
        """创建模拟的 StoryGraphManager"""
        manager = Mock(spec=StoryGraphManager)
        manager.create_graph = Mock(return_value="test_graph")
        manager.add_entity = Mock(return_value="entity_id")
        manager.query_entities = Mock(return_value=[])
        return manager
    
    @pytest.fixture
    def belief_manager(self, mock_graph_manager):
        """创建 BeliefGraphManager 实例"""
        return BeliefGraphManager(graph_manager=mock_graph_manager)
    
    def test_create_belief_graph(self, belief_manager, mock_graph_manager):
        """测试创建信念图谱"""
        graph_id = belief_manager.create_belief_graph("character_1")
        
        assert graph_id.startswith("belief_character_1_")
        mock_graph_manager.create_graph.assert_called_once_with(graph_id)
    
    def test_add_belief(self, belief_manager, mock_graph_manager):
        """测试添加信念"""
        graph_id = "belief_test_001"
        belief = Belief(
            belief_id="belief_001",
            holder="character_1",
            subject="character_2",
            content="是个好人",
            confidence=0.8,
            source="observation",
        )
        
        result = belief_manager.add_belief(graph_id, belief)
        
        assert result == "belief_001"
        mock_graph_manager.add_entity.assert_called_once()
        
        # 验证添加的实体
        call_args = mock_graph_manager.add_entity.call_args
        entity = call_args[0][1]
        assert isinstance(entity, StoryEntity)
        assert entity.entity_type == EntityType.BELIEF
        assert entity.properties["belief_holder"] == "character_1"
        assert entity.properties["belief_subject"] == "character_2"
        assert entity.properties["confidence"] == 0.8
    
    def test_add_belief_auto_generate_id(self, belief_manager, mock_graph_manager):
        """测试自动生成信念 ID"""
        graph_id = "belief_test_001"
        belief = Belief(
            belief_id="",
            holder="character_1",
            subject="character_2",
            content="是个好人",
        )
        
        result = belief_manager.add_belief(graph_id, belief)
        
        assert result.startswith("belief_")
        assert belief.belief_id == result
    
    def test_get_all_beliefs_empty(self, belief_manager, mock_graph_manager):
        """测试获取所有信念（空列表）"""
        mock_graph_manager.query_entities.return_value = []
        
        beliefs = belief_manager.get_all_beliefs("belief_test_001")
        
        assert beliefs == []
        mock_graph_manager.query_entities.assert_called_once()
    
    def test_get_all_beliefs_with_data(self, belief_manager, mock_graph_manager):
        """测试获取所有信念（有数据）"""
        # 创建模拟实体
        entity1 = StoryEntity(
            entity_id="belief_001",
            entity_type=EntityType.BELIEF,
            name="Alice likes Bob",
            properties={
                "belief_id": "belief_001",
                "belief_holder": "Alice",
                "belief_subject": "Bob",
                "belief_content": "likes",
                "confidence": 0.9,
                "source": "observation",
                "graph_id": "belief_test_001",
            },
        )
        
        mock_graph_manager.query_entities.return_value = [entity1]
        
        beliefs = belief_manager.get_all_beliefs("belief_test_001")
        
        assert len(beliefs) == 1
        assert beliefs[0].holder == "Alice"
        assert beliefs[0].subject == "Bob"
        assert beliefs[0].confidence == 0.9
    
    def test_get_beliefs_about(self, belief_manager, mock_graph_manager):
        """测试获取关于某实体的信念"""
        entity1 = StoryEntity(
            entity_id="belief_001",
            entity_type=EntityType.BELIEF,
            name="Alice likes Bob",
            properties={
                "belief_id": "belief_001",
                "belief_holder": "Alice",
                "belief_subject": "Bob",
                "belief_content": "likes",
                "confidence": 0.9,
                "source": "observation",
                "graph_id": "belief_test_001",
            },
        )
        
        mock_graph_manager.query_entities.return_value = [entity1]
        
        beliefs = belief_manager.get_beliefs_about("belief_test_001", "Bob")
        
        assert len(beliefs) == 1
        assert beliefs[0].subject == "Bob"
    
    def test_get_beliefs_by_source(self, belief_manager, mock_graph_manager):
        """测试按来源获取信念"""
        entity1 = StoryEntity(
            entity_id="belief_001",
            entity_type=EntityType.BELIEF,
            name="Alice likes Bob",
            properties={
                "belief_id": "belief_001",
                "belief_holder": "Alice",
                "belief_subject": "Bob",
                "belief_content": "likes",
                "confidence": 0.9,
                "source": "observation",
                "graph_id": "belief_test_001",
            },
        )
        
        entity2 = StoryEntity(
            entity_id="belief_002",
            entity_type=EntityType.CONCEPT,
            name="Alice hates Charlie",
            properties={
                "belief_id": "belief_002",
                "belief_holder": "Alice",
                "belief_subject": "Charlie",
                "belief_content": "hates",
                "confidence": 0.7,
                "source": "rumor",
                "graph_id": "belief_test_001",
            },
        )
        
        mock_graph_manager.query_entities.return_value = [entity1, entity2]
        
        beliefs = belief_manager.get_beliefs_by_source("belief_test_001", "observation")
        
        assert len(beliefs) == 1
        assert beliefs[0].source == "observation"
    
    def test_check_consistency_no_conflicts(self, belief_manager, mock_graph_manager):
        """测试一致性检查（无冲突）"""
        entity1 = StoryEntity(
            entity_id="belief_001",
            entity_type=EntityType.CONCEPT,
            name="Alice is kind",
            properties={
                "belief_id": "belief_001",
                "belief_holder": "Bob",
                "belief_subject": "Alice",
                "belief_content": "is kind",
                "confidence": 0.9,
                "source": "observation",
                "graph_id": "belief_test_001",
            },
        )
        
        mock_graph_manager.query_entities.return_value = [entity1]
        
        report = belief_manager.check_consistency("belief_test_001")
        
        assert report.is_consistent
        assert len(report.conflicts) == 0
    
    def test_check_consistency_with_conflicts(self, belief_manager, mock_graph_manager):
        """测试一致性检查（有冲突）"""
        entity1 = StoryEntity(
            entity_id="belief_001",
            entity_type=EntityType.BELIEF,
            name="Alice 是诚实的",
            properties={
                "belief_id": "belief_001",
                "belief_holder": "Bob",
                "belief_subject": "Alice",
                "belief_content": "是诚实的",
                "confidence": 0.9,
                "source": "observation",
                "graph_id": "belief_test_001",
            },
        )
        
        entity2 = StoryEntity(
            entity_id="belief_002",
            entity_type=EntityType.BELIEF,
            name="Alice 是骗子",
            properties={
                "belief_id": "belief_002",
                "belief_holder": "Bob",
                "belief_subject": "Alice",
                "belief_content": "是骗子",
                "confidence": 0.8,
                "source": "rumor",
                "graph_id": "belief_test_001",
            },
        )
        
        mock_graph_manager.query_entities.return_value = [entity1, entity2]
        
        report = belief_manager.check_consistency("belief_test_001")
        
        assert not report.is_consistent
        assert len(report.conflicts) > 0
    
    def test_belief_validation(self):
        """测试信念验证"""
        # 有效的信念
        belief = Belief(
            belief_id="belief_001",
            holder="Alice",
            subject="Bob",
            content="is kind",
            confidence=0.8,
        )
        assert belief.confidence == 0.8
        
        # 无效的置信度
        with pytest.raises(ValueError):
            Belief(
                belief_id="belief_002",
                holder="Alice",
                subject="Bob",
                content="is kind",
                confidence=1.5,
            )
    
    def test_belief_to_entity_conversion(self, belief_manager):
        """测试信念到实体的转换"""
        belief = Belief(
            belief_id="belief_001",
            holder="Alice",
            subject="Bob",
            content="loves",
            confidence=0.95,
            source="observation",
        )
        
        entity = belief_manager._belief_to_entity("belief_graph_001", belief)
        
        assert entity.entity_type == EntityType.BELIEF
        assert entity.name == "Alice loves Bob"
        assert entity.properties["belief_holder"] == "Alice"
        assert entity.properties["belief_subject"] == "Bob"
        assert entity.properties["confidence"] == 0.95
    
    def test_entity_to_belief_conversion(self, belief_manager):
        """测试实体到信念的转换"""
        entity = StoryEntity(
            entity_id="belief_001",
            entity_type=EntityType.CONCEPT,
            name="Alice loves Bob",
            properties={
                "belief_id": "belief_001",
                "belief_holder": "Alice",
                "belief_subject": "Bob",
                "belief_content": "loves",
                "confidence": 0.95,
                "source": "observation",
                "graph_id": "belief_graph_001",
            },
        )
        
        belief = belief_manager._entity_to_belief(entity)
        
        assert belief.holder == "Alice"
        assert belief.subject == "Bob"
        assert belief.content == "loves"
        assert belief.confidence == 0.95


    def test_update_belief(self, belief_manager, mock_graph_manager):
        """测试更新信念"""
        graph_id = "belief_test_001"
        belief_id = "belief_001"
        
        # 模拟查询返回现有信念
        entity = StoryEntity(
            entity_id="belief_001",
            entity_type=EntityType.BELIEF,
            name="Alice likes Bob",
            properties={
                "belief_id": belief_id,
                "belief_holder": "Alice",
                "belief_subject": "Bob",
                "belief_content": "likes",
                "confidence": 0.8,
                "source": "observation",
                "graph_id": graph_id,
            },
        )
        mock_graph_manager.query_entities.return_value = [entity]
        
        # 更新信念内容和置信度
        updated_belief = belief_manager.update_belief(
            graph_id,
            belief_id,
            new_content="loves",
            new_confidence=0.95,
        )
        
        assert updated_belief.content == "loves"
        assert updated_belief.confidence == 0.95
        mock_graph_manager.add_entity.assert_called()
    
    def test_update_belief_not_found(self, belief_manager, mock_graph_manager):
        """测试更新不存在的信念"""
        mock_graph_manager.query_entities.return_value = []
        
        with pytest.raises(BeliefGraphError, match="信念不存在"):
            belief_manager.update_belief("belief_test_001", "nonexistent", new_content="test")
    
    def test_update_belief_invalid_confidence(self, belief_manager, mock_graph_manager):
        """测试更新信念时无效的置信度"""
        entity = StoryEntity(
            entity_id="belief_001",
            entity_type=EntityType.BELIEF,
            name="Alice likes Bob",
            properties={
                "belief_id": "belief_001",
                "belief_holder": "Alice",
                "belief_subject": "Bob",
                "belief_content": "likes",
                "confidence": 0.8,
                "source": "observation",
                "graph_id": "belief_test_001",
            },
        )
        mock_graph_manager.query_entities.return_value = [entity]
        
        with pytest.raises(BeliefGraphError, match="置信度必须在"):
            belief_manager.update_belief(
                "belief_test_001",
                "belief_001",
                new_confidence=1.5,
            )
    
    def test_remove_belief(self, belief_manager, mock_graph_manager):
        """测试删除信念"""
        graph_id = "belief_test_001"
        belief_id = "belief_001"
        
        # 模拟查询返回现有信念
        entity = StoryEntity(
            entity_id="belief_001",
            entity_type=EntityType.BELIEF,
            name="Alice likes Bob",
            properties={
                "belief_id": belief_id,
                "belief_holder": "Alice",
                "belief_subject": "Bob",
                "belief_content": "likes",
                "confidence": 0.8,
                "source": "observation",
                "graph_id": graph_id,
            },
        )
        mock_graph_manager.query_entities.return_value = [entity]
        
        # 删除信念
        belief_manager.remove_belief(graph_id, belief_id)
        
        # 验证调用了 add_entity（逻辑删除）
        mock_graph_manager.add_entity.assert_called()
        
        # 验证删除标记
        call_args = mock_graph_manager.add_entity.call_args
        updated_entity = call_args[0][1]
        assert updated_entity.properties.get("is_deleted") is True
        assert updated_entity.properties.get("deleted_at") is not None
        assert updated_entity.properties.get("confidence") == 0.0
    
    def test_remove_belief_not_found(self, belief_manager, mock_graph_manager):
        """测试删除不存在的信念"""
        mock_graph_manager.query_entities.return_value = []
        
        with pytest.raises(BeliefGraphError, match="信念不存在"):
            belief_manager.remove_belief("belief_test_001", "nonexistent")
    
    def test_check_consistency_conflict_detection(self, belief_manager, mock_graph_manager):
        """测试冲突检测：loves vs hates"""
        graph_id = "belief_test_001"
        
        # 创建冲突的信念
        entity1 = StoryEntity(
            entity_id="belief_001",
            entity_type=EntityType.BELIEF,
            name="Alice loves Bob",
            properties={
                "belief_id": "belief_001",
                "belief_holder": "Alice",
                "belief_subject": "Bob",
                "belief_content": "loves",
                "confidence": 0.9,
                "source": "observation",
                "graph_id": graph_id,
            },
        )
        
        entity2 = StoryEntity(
            entity_id="belief_002",
            entity_type=EntityType.BELIEF,
            name="Alice hates Bob",
            properties={
                "belief_id": "belief_002",
                "belief_holder": "Alice",
                "belief_subject": "Bob",
                "belief_content": "hates",
                "confidence": 0.8,
                "source": "rumor",
                "graph_id": graph_id,
            },
        )
        
        mock_graph_manager.query_entities.return_value = [entity1, entity2]
        
        report = belief_manager.check_consistency(graph_id)
        
        assert not report.is_consistent
        assert len(report.conflicts) > 0
        
        # 验证冲突对
        conflict_pair = report.conflicts[0]
        assert conflict_pair[0].content in ["loves", "hates"]
        assert conflict_pair[1].content in ["loves", "hates"]
    
    def test_check_consistency_multiple_conflicts(self, belief_manager, mock_graph_manager):
        """测试多个冲突检测"""
        graph_id = "belief_test_001"
        
        entities = [
            StoryEntity(
                entity_id="belief_001",
                entity_type=EntityType.BELIEF,
                name="Alice is honest",
                properties={
                    "belief_id": "belief_001",
                    "belief_holder": "Bob",
                    "belief_subject": "Alice",
                    "belief_content": "是诚实的",
                    "confidence": 0.9,
                    "source": "observation",
                    "graph_id": graph_id,
                },
            ),
            StoryEntity(
                entity_id="belief_002",
                entity_type=EntityType.BELIEF,
                name="Alice is a liar",
                properties={
                    "belief_id": "belief_002",
                    "belief_holder": "Bob",
                    "belief_subject": "Alice",
                    "belief_content": "是骗子",
                    "confidence": 0.8,
                    "source": "rumor",
                    "graph_id": graph_id,
                },
            ),
            StoryEntity(
                entity_id="belief_003",
                entity_type=EntityType.BELIEF,
                name="Alice is brave",
                properties={
                    "belief_id": "belief_003",
                    "belief_holder": "Bob",
                    "belief_subject": "Alice",
                    "belief_content": "很勇敢",
                    "confidence": 0.7,
                    "source": "observation",
                    "graph_id": graph_id,
                },
            ),
            StoryEntity(
                entity_id="belief_004",
                entity_type=EntityType.BELIEF,
                name="Alice is cowardly",
                properties={
                    "belief_id": "belief_004",
                    "belief_holder": "Bob",
                    "belief_subject": "Alice",
                    "belief_content": "很懦弱",
                    "confidence": 0.6,
                    "source": "rumor",
                    "graph_id": graph_id,
                },
            ),
        ]
        
        mock_graph_manager.query_entities.return_value = entities
        
        report = belief_manager.check_consistency(graph_id)
        
        assert not report.is_consistent
        assert len(report.conflicts) >= 2  # 至少有两个冲突对
    
    def test_get_all_beliefs_excludes_deleted(self, belief_manager, mock_graph_manager):
        """测试获取所有信念时排除已删除的"""
        graph_id = "belief_test_001"
        
        entities = [
            StoryEntity(
                entity_id="belief_001",
                entity_type=EntityType.BELIEF,
                name="Alice likes Bob",
                properties={
                    "belief_id": "belief_001",
                    "belief_holder": "Alice",
                    "belief_subject": "Bob",
                    "belief_content": "likes",
                    "confidence": 0.9,
                    "source": "observation",
                    "graph_id": graph_id,
                    "is_deleted": False,
                },
            ),
            StoryEntity(
                entity_id="belief_002",
                entity_type=EntityType.BELIEF,
                name="Alice hates Charlie",
                properties={
                    "belief_id": "belief_002",
                    "belief_holder": "Alice",
                    "belief_subject": "Charlie",
                    "belief_content": "hates",
                    "confidence": 0.0,
                    "source": "rumor",
                    "graph_id": graph_id,
                    "is_deleted": True,
                },
            ),
        ]
        
        mock_graph_manager.query_entities.return_value = entities
        
        # 默认不包含已删除的
        beliefs = belief_manager.get_all_beliefs(graph_id)
        assert len(beliefs) == 1
        assert beliefs[0].belief_id == "belief_001"
        
        # 明确要求包含已删除的
        beliefs_with_deleted = belief_manager.get_all_beliefs(graph_id, include_deleted=True)
        assert len(beliefs_with_deleted) == 2
    
    def test_get_beliefs_about_excludes_deleted(self, belief_manager, mock_graph_manager):
        """测试获取关于某实体的信念时排除已删除的"""
        graph_id = "belief_test_001"
        subject = "Bob"
        
        entities = [
            StoryEntity(
                entity_id="belief_001",
                entity_type=EntityType.BELIEF,
                name="Alice likes Bob",
                properties={
                    "belief_id": "belief_001",
                    "belief_holder": "Alice",
                    "belief_subject": subject,
                    "belief_content": "likes",
                    "confidence": 0.9,
                    "source": "observation",
                    "graph_id": graph_id,
                    "is_deleted": False,
                },
            ),
            StoryEntity(
                entity_id="belief_002",
                entity_type=EntityType.BELIEF,
                name="Alice hates Bob",
                properties={
                    "belief_id": "belief_002",
                    "belief_holder": "Alice",
                    "belief_subject": subject,
                    "belief_content": "hates",
                    "confidence": 0.0,
                    "source": "rumor",
                    "graph_id": graph_id,
                    "is_deleted": True,
                },
            ),
        ]
        
        mock_graph_manager.query_entities.return_value = entities
        
        # 默认不包含已删除的
        beliefs = belief_manager.get_beliefs_about(graph_id, subject)
        assert len(beliefs) == 1
        assert beliefs[0].content == "likes"
        
        # 明确要求包含已删除的
        beliefs_with_deleted = belief_manager.get_beliefs_about(graph_id, subject, include_deleted=True)
        assert len(beliefs_with_deleted) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
