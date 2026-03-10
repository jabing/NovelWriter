"""全链路测试

测试从创建项目到生成章节的完整流程:
1. 创建故事世界
2. 添加角色
3. 运行模拟
4. 生成叙事
5. 验证结果完整性
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from dataclasses import dataclass, field
from typing import Any

# Import the Flask app
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))



# ============================================================================
# Mock Classes
# ============================================================================

class MockLLMClient:
    """模拟 LLM 客户端"""
    
    def __init__(self, *args, **kwargs):
        pass
    
    def chat(self, messages: list, temperature: float = 0.7, **kwargs) -> str:
        """模拟聊天响应"""
        return self._generate_narrative_content()
    
    def chat_json(self, messages: list, temperature: float = 0.7, **kwargs) -> dict:
        """模拟 JSON 响应"""
        return self._generate_events_response()
    
    def _generate_events_response(self) -> dict:
        """生成事件响应"""
        return {
            "events": [
                {
                    "title": "Alice 发现神秘信件",
                    "description": "Alice 在阁楼的旧箱子里发现了一封尘封已久的信件",
                    "event_type": "发现",
                    "participants": ["alice"],
                    "witnesses": [],
                    "impact_level": 3,
                    "is_milestone": False,
                    "is_public": False,
                    "who_knows": ["alice"]
                },
                {
                    "title": "Bob 与 Alice 相遇",
                    "description": "Bob 在走廊遇到了 Alice，两人交谈了关于信件的事情",
                    "event_type": "对话",
                    "participants": ["alice", "bob"],
                    "witnesses": [],
                    "impact_level": 2,
                    "is_milestone": False,
                    "is_public": False,
                    "who_knows": ["alice", "bob"]
                },
                {
                    "title": "神秘人出现",
                    "description": "一个戴面具的神秘人在花园中出现，注视着 Alice 的窗户",
                    "event_type": "事件",
                    "participants": ["mystery-person"],
                    "witnesses": [],
                    "impact_level": 4,
                    "is_milestone": True,
                    "is_public": True,
                    "who_knows": ["alice", "bob", "mystery-person"]
                }
            ]
        }
    
    def _generate_narrative_content(self) -> str:
        """生成叙事内容"""
        return """夜幕降临，阁楼的尘埃在月光下缓缓飘浮。Alice 的手指触碰到那封泛黄的信件时，
心跳不自觉地加快了。信封上的蜡封已经碎裂，但那熟悉的字迹依然清晰可辨。

"这不可能..." 她喃喃自语，指尖划过那些曾经刻骨铭心的文字。

窗外的花园里，一个身影悄然站立。面具遮住了他的面容，却遮不住那双注视着
Alice 窗户的眼睛。他是谁？为什么会在深夜出现？

走廊传来了脚步声，是 Bob。他看着 Alice 手中的信件，眼中闪过一丝复杂的神色。
"Alice，你...发现了什么？"

这一刻，命运的齿轮开始转动。"""
    
    def _generate_perspective_narrative(self, character_name: str) -> str:
        """生成角色视角叙事"""
        narratives = {
            "Alice": """阁楼里的空气凝滞而沉重。当我的手指触碰到那封信的瞬间，
一段尘封的记忆猛然苏醒。那是十年前的笔迹，父亲失踪前留给我的最后一封信。

我一直以为它已经遗失在时光中，没想到它一直就在这里，静静地等待被发现。

窗外的月光透过破碎的窗棂洒落，在地上投下斑驳的影子。我忽然意识到，
这不是偶然，一切都是命运的安排。

Bob 的脚步声打断了我的思绪。"Alice，你...发现了什么？"

我转过身，看着他眼中的复杂神情。他知道什么，他一定知道什么。""",
            
            "Bob": """走进阁楼的那一刻，我就知道一切都完了。

Alice 手里拿着那封信，她的表情从震惊到困惑，再到某种我无法解读的情绪。
十年的秘密，就这样在今晚被揭开了。

我该怎么告诉她？该怎么解释当年的选择？

窗外的花园里，一个黑影静静地站立。那是谁？难道是...他回来了？

"Alice，你...发现了什么？" 我听到自己干涩的声音。

命运的齿轮已经开始转动，我无力阻止，只能眼睁睁看着一切发生。"""
        }
        return narratives.get(character_name, self._generate_narrative_content())


class MockZepClient:
    """模拟 Zep 客户端"""
    
    def __init__(self, *args, **kwargs):
        self._graphs: dict[str, Any] = {}
        self._entities: dict[str, list] = {}
        self._relations: dict[str, list] = {}
    
    def create_graph(self, graph_id: str) -> str:
        """模拟创建图谱"""
        self._graphs[graph_id] = {"id": graph_id, "created": True}
        self._entities[graph_id] = []
        self._relations[graph_id] = []
        return graph_id
    
    def add_entity(self, graph_id: str, entity: Any) -> str:
        """模拟添加实体"""
        import uuid
        entity_uuid = str(uuid.uuid4())
        self._entities[graph_id].append({
            "uuid": entity_uuid,
            "name": entity.name,
            "type": entity.entity_type,
            "description": entity.description,
            "metadata": entity.metadata
        })
        return entity_uuid
    
    def add_relation(self, graph_id: str, relation: Any) -> str:
        """模拟添加关系"""
        import uuid
        relation_uuid = str(uuid.uuid4())
        self._relations[graph_id].append({
            "uuid": relation_uuid,
            "source": relation.source_entity_name,
            "target": relation.target_entity_name,
            "type": relation.relation_type,
            "metadata": relation.metadata
        })
        return relation_uuid
    
    def list_entities(self, graph_id: str, entity_type: str | None = None) -> list:
        """模拟列出实体"""
        entities = self._entities.get(graph_id, [])
        if entity_type:
            entities = [e for e in entities if e.get("type") == entity_type]
        
        @dataclass
        class MockEntity:
            name: str
            type: str
            description: str
            metadata: dict
            uuid: str = ""
            created_at: Any = None
        
        return [MockEntity(
            name=e["name"],
            type=e["type"],
            description=e.get("description", ""),
            metadata=e.get("metadata", {}),
            uuid=e.get("uuid", "")
        ) for e in entities]
    
    def get_character_beliefs(self, graph_id: str, character_name: str) -> dict:
        """模拟获取角色信念"""
        entities = [e for e in self._entities.get(graph_id, []) 
                   if character_name.lower() in e.get("name", "").lower()]
        
        relations = [r for r in self._relations.get(graph_id, [])
                    if character_name.lower() in r.get("source", "").lower() 
                    or character_name.lower() in r.get("target", "").lower()]
        
        return {
            "character": character_name,
            "entities": entities,
            "relations": relations
        }


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def client(test_app):
    """创建测试客户端"""
    with test_app.test_client() as client:
        yield client

@pytest.fixture
def mock_llm():
    """模拟 LLM 客户端"""
    with patch('app.utils.llm_client.LLMClient', MockLLMClient):
        yield MockLLMClient()


@pytest.fixture
def mock_zep():
    """模拟 Zep 客户端"""
    with patch('app.utils.zep_client.ZepClient', MockZepClient):
        yield MockZepClient()


@pytest.fixture
def mock_graph_manager(mock_zep):
    """模拟图谱管理器"""
    from app.graph.story_graph_manager import StoryGraphManager
    with patch('app.graph.story_graph_manager.StoryGraphManager') as MockManager:
        manager = StoryGraphManager(zep_client=mock_zep)
        MockManager.return_value = manager
        yield manager


# ============================================================================
# Test Data
# ============================================================================

def get_sample_character_data() -> dict:
    """获取示例角色数据"""
    return {
        "name": "Alice",
        "description": "一个好奇心强的年轻女性",
        "age": 25,
        "gender": "female",
        "occupation": "图书管理员",
        "mbti": "INFP",
        "personality_traits": ["好奇", "敏感", "理想主义", "内向"],
        "core_values": ["真理", "自由", "美"],
        "thinking_style": "intuitive",
        "emotional_tone": "contemplative",
        "narrative_voice": "intimate",
        "perspective_bias": {
            "gender_bias": {"female": 0.8, "male": 0.2},
            "mbti_bias": {"feeling": 0.7, "intuition": 0.8},
            "cognitive_bias": {"optimism": 0.6, "detail_oriented": 0.4}
        },
        "character_layer": 1,
        "has_pov": True,
        "activity_level": 0.9,
        "bio": "Alice 是一个热爱阅读的年轻女性，在图书馆工作。她有着强烈的好奇心和对未知的渴望。",
        "background_story": "Alice 的父亲在她十岁时神秘失踪，只留下一封信。十年来，她一直在寻找真相。",
        "motivations": ["寻找父亲失踪的真相", "保护身边的人"],
        "fears": ["被背叛", "失去记忆"],
        "goals": ["解开神秘信件的谜团", "找到父亲的下落"]
    }


def get_sample_character_bob() -> dict:
    """获取 Bob 角色数据"""
    return {
        "name": "Bob",
        "description": "Alice 的青梅竹马，性格稳重",
        "age": 27,
        "gender": "male",
        "occupation": "律师",
        "mbti": "ISTJ",
        "personality_traits": ["稳重", "负责", "保守", "忠诚"],
        "core_values": ["责任", "正义", "家庭"],
        "thinking_style": "analytical",
        "emotional_tone": "serious",
        "narrative_voice": "intimate",
        "character_layer": 2,
        "has_pov": True,
        "activity_level": 0.7,
        "bio": "Bob 是 Alice 的青梅竹马，现在是一名律师。他隐藏着一个关于 Alice 父亲的秘密。",
        "background_story": "Bob 的父亲是 Alice 父亲的好友，也是最后见到他的人之一。",
        "motivations": ["保护 Alice", "守护秘密"],
        "fears": ["真相大白", "失去 Alice 的信任"],
        "goals": ["帮助 Alice", "维持现状"]
    }


# ============================================================================
# Test Classes
# ============================================================================

class TestEndToEndFlow:
    """全链路测试"""
    
    def test_01_health_check(self, client):
        """测试健康检查"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"
    
    def test_02_create_story_world(self, client):
        """创建故事世界 - 通过状态检查"""
        response = client.get('/api/v1/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "running"
        assert data["version"] == "1.0.0"
    
    def test_03_create_character_alice(self, client):
        """创建角色 Alice"""
        char_data = get_sample_character_data()
        
        response = client.post(
            '/api/v1/characters',
            json=char_data,
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        # 验证响应数据
        assert data["name"] == "Alice"
        assert data["age"] == 25
        assert data["mbti"] == "INFP"
        assert data["character_layer"] == 1
        assert data["has_pov"] is True
        assert len(data["personality_traits"]) == 4
        assert len(data["motivations"]) == 2
        assert "entity_id" in data
    
    def test_04_create_character_bob(self, client):
        """创建角色 Bob"""
        char_data = get_sample_character_bob()
        
        response = client.post(
            '/api/v1/characters',
            json=char_data,
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert data["name"] == "Bob"
        assert data["character_layer"] == 2
    
    def test_05_list_characters(self, client):
        """列出所有角色"""
        # 先创建两个角色
        client.post('/api/v1/characters', json=get_sample_character_data())
        client.post('/api/v1/characters', json=get_sample_character_bob())
        
        response = client.get('/api/v1/characters')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "characters" in data
        assert "total" in data
        assert data["total"] >= 2
    
    def test_06_get_character(self, client):
        """获取单个角色"""
        # 先创建角色
        create_response = client.post(
            '/api/v1/characters',
            json=get_sample_character_data()
        )
        char_data = json.loads(create_response.data)
        char_id = char_data["entity_id"]
        
        # 获取角色
        response = client.get(f'/api/v1/characters/{char_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Alice"
    
    def test_07_update_character(self, client):
        """更新角色"""
        # 先创建角色
        create_response = client.post(
            '/api/v1/characters',
            json=get_sample_character_data()
        )
        char_data = json.loads(create_response.data)
        char_id = char_data["entity_id"]
        
        # 更新角色
        update_data = {"age": 26, "bio": "更新后的简介"}
        response = client.put(
            f'/api/v1/characters/{char_id}',
            json=update_data,
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["age"] == 26
    
    def test_08_start_simulation(self, client, mock_llm, mock_zep):
        """运行模拟"""
        # 准备模拟请求数据
        alice_data = get_sample_character_data()
        bob_data = get_sample_character_bob()
        
        sim_request = {
            "chapter_id": "chapter-001",
            "graph_id": "story-mystery-001",
            "outline": "Alice 在阁楼发现了一封神秘信件，这封信可能与她父亲十年前的失踪有关。Bob 知道一些关于这件事的秘密，但他选择了沉默。一个神秘人在花园中出现，似乎在监视 Alice。",
            "characters": [alice_data, bob_data],
            "target_events": 3,
            "context": {
                "setting": "维多利亚风格的老宅",
                "time": "深夜",
                "weather": "月光明亮"
            }
        }
        
        # Mock LLM 和 Zep
        with patch('app.simulation.story_world_simulator.LLMClient', return_value=mock_llm), \
             patch('app.graph.story_graph_manager.ZepClient', return_value=mock_zep):
            
            response = client.post(
                '/api/v1/simulation/start',
                json=sim_request,
                content_type='application/json'
            )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        # 验证响应
        assert "simulation_id" in data
        assert data["status"] in ["running", "completed"]
    
    def test_09_get_simulation_status(self, client, mock_llm, mock_zep):
        """查询模拟状态"""
        # 先启动模拟
        alice_data = get_sample_character_data()
        bob_data = get_sample_character_bob()
        
        sim_request = {
            "chapter_id": "chapter-002",
            "graph_id": "story-mystery-002",
            "outline": "测试大纲",
            "characters": [alice_data, bob_data],
            "target_events": 2
        }
        
        with patch('app.simulation.story_world_simulator.LLMClient', return_value=mock_llm), \
             patch('app.graph.story_graph_manager.ZepClient', return_value=mock_zep):
            
            create_response = client.post(
                '/api/v1/simulation/start',
                json=sim_request,
                content_type='application/json'
            )
        
        sim_data = json.loads(create_response.data)
        sim_id = sim_data["simulation_id"]
        
        # 查询状态
        response = client.get(f'/api/v1/simulation/status/{sim_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["simulation_id"] == sim_id
        assert data["status"] in ["running", "completed", "failed"]
    
    def test_10_list_simulations(self, client):
        """列出所有模拟"""
        response = client.get('/api/v1/simulation/list')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "simulations" in data
    
    def test_11_generate_narrative(self, client, mock_llm):
        """生成叙事"""
        alice_data = get_sample_character_data()
        bob_data = get_sample_character_bob()
        
        narrative_request = {
            "chapter_id": "chapter-003",
            "characters": [alice_data, bob_data],
            "events": [
                {
                    "entity_id": "event-001",
                    "name": "发现信件",
                    "title": "Alice 发现神秘信件",
                    "description": "Alice 在阁楼发现了一封尘封的信件",
                    "event_type": "发现",
                    "participants": ["alice-001"],
                    "witnesses": [],
                    "impact_level": 3,
                    "is_public": False,
                    "who_knows": ["alice-001"]
                },
                {
                    "entity_id": "event-002",
                    "name": "相遇对话",
                    "title": "Bob 与 Alice 相遇",
                    "description": "Bob 在走廊遇到了 Alice",
                    "event_type": "对话",
                    "participants": ["alice-001", "bob-001"],
                    "witnesses": [],
                    "impact_level": 2,
                    "is_public": False,
                    "who_knows": ["alice-001", "bob-001"]
                }
            ],
            "context": "维多利亚风格的老宅，深夜",
            "temperature": 0.8
        }
        
        with patch('app.narrative.narrative_generator.LLMClient', return_value=mock_llm), \
             patch('app.narrative.perspective_agent.LLMClient', return_value=mock_llm):
            
            response = client.post(
                '/api/v1/narratives/generate',
                json=narrative_request,
                content_type='application/json'
            )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        # 验证响应结构
        assert data["chapter_id"] == "chapter-003"
        assert "narratives" in data
        assert "total_characters" in data
        assert data["total_characters"] >= 1
    
    def test_12_get_narrative(self, client, mock_llm):
        """获取叙事"""
        # 先生成叙事
        alice_data = get_sample_character_data()
        
        narrative_request = {
            "chapter_id": "chapter-004",
            "characters": [alice_data],
            "events": [
                {
                    "entity_id": "event-001",
                    "name": "测试事件",
                    "title": "测试事件标题",
                    "description": "测试事件描述",
                    "event_type": "测试",
                    "participants": [],
                    "witnesses": [],
                    "impact_level": 1
                }
            ]
        }
        
        with patch('app.narrative.narrative_generator.LLMClient', return_value=mock_llm), \
             patch('app.narrative.perspective_agent.LLMClient', return_value=mock_llm):
            
            create_response = client.post(
                '/api/v1/narratives/generate',
                json=narrative_request,
                content_type='application/json'
            )
        
        narrative_data = json.loads(create_response.data)
        narrative_id = narrative_data.get("id")
        
        if narrative_id:
            # 获取叙事
            response = client.get(f'/api/v1/narratives/{narrative_id}')
            assert response.status_code == 200
    
    def test_13_list_narratives(self, client):
        """列出所有叙事"""
        response = client.get('/api/v1/narratives')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "narratives" in data
        assert "total" in data
    
    def test_14_delete_character(self, client):
        """删除角色"""
        # 先创建角色
        create_response = client.post(
            '/api/v1/characters',
            json=get_sample_character_data()
        )
        char_data = json.loads(create_response.data)
        char_id = char_data["entity_id"]
        
        # 删除角色
        response = client.delete(f'/api/v1/characters/{char_id}')
        
        assert response.status_code == 200
        
        # 验证已删除
        get_response = client.get(f'/api/v1/characters/{char_id}')
        assert get_response.status_code == 404


class TestFullIntegration:
    """完整集成测试"""
    
    def test_complete_story_flow(self, client, mock_llm, mock_zep):
        """完整故事流程测试
        
        测试从创建角色到生成叙事的完整流程。
        """
        # 1. 创建故事世界（状态检查）
        status_response = client.get('/api/v1/status')
        assert status_response.status_code == 200
        
        # 2. 创建角色
        alice_data = get_sample_character_data()
        bob_data = get_sample_character_bob()
        
        alice_response = client.post(
            '/api/v1/characters',
            json=alice_data,
            content_type='application/json'
        )
        assert alice_response.status_code == 201
        alice = json.loads(alice_response.data)
        
        bob_response = client.post(
            '/api/v1/characters',
            json=bob_data,
            content_type='application/json'
        )
        assert bob_response.status_code == 201
        bob = json.loads(bob_response.data)
        
        # 3. 运行模拟
        sim_request = {
            "chapter_id": "chapter-integration",
            "graph_id": "story-integration",
            "outline": "完整集成测试大纲：Alice 发现神秘信件，Bob 知道真相，神秘人出现。",
            "characters": [alice, bob],
            "target_events": 3
        }
        
        with patch('app.simulation.story_world_simulator.LLMClient', return_value=mock_llm), \
             patch('app.graph.story_graph_manager.ZepClient', return_value=mock_zep):
            
            sim_response = client.post(
                '/api/v1/simulation/start',
                json=sim_request,
                content_type='application/json'
            )
        
        assert sim_response.status_code == 201
        sim_result = json.loads(sim_response.data)
        
        # 4. 查询模拟状态
        if sim_result.get("simulation_id"):
            status_response = client.get(f'/api/v1/simulation/status/{sim_result["simulation_id"]}')
            assert status_response.status_code == 200
        
        # 5. 生成叙事
        narrative_request = {
            "chapter_id": "chapter-integration",
            "characters": [alice, bob],
            "events": [
                {
                    "entity_id": "event-1",
                    "name": "发现",
                    "title": "Alice 发现信件",
                    "description": "Alice 在阁楼发现了神秘信件",
                    "event_type": "发现",
                    "participants": [alice["entity_id"]],
                    "witnesses": [],
                    "impact_level": 3,
                    "is_public": False,
                    "who_knows": [alice["entity_id"]]
                },
                {
                    "entity_id": "event-2",
                    "name": "对话",
                    "title": "Bob 与 Alice 交谈",
                    "description": "Bob 与 Alice 讨论信件的内容",
                    "event_type": "对话",
                    "participants": [alice["entity_id"], bob["entity_id"]],
                    "witnesses": [],
                    "impact_level": 2,
                    "is_public": False,
                    "who_knows": [alice["entity_id"], bob["entity_id"]]
                }
            ],
            "context": "老宅深夜，月光如水"
        }
        
        with patch('app.narrative.narrative_generator.LLMClient', return_value=mock_llm), \
             patch('app.narrative.perspective_agent.LLMClient', return_value=mock_llm):
            
            narrative_response = client.post(
                '/api/v1/narratives/generate',
                json=narrative_request,
                content_type='application/json'
            )
        
        assert narrative_response.status_code == 201
        narrative_result = json.loads(narrative_response.data)
        
        # 6. 验证结果完整性
        assert narrative_result["chapter_id"] == "chapter-integration"
        assert "narratives" in narrative_result
        assert narrative_result["total_characters"] >= 1
        
        # 验证每个叙事都有必要字段
        for narr in narrative_result.get("narratives", []):
            assert "character_id" in narr
            assert "chapter_id" in narr
            assert "content" in narr
            assert len(narr["content"]) > 0


class TestErrorHandling:
    """错误处理测试"""
    
    def test_create_character_missing_name(self, client):
        """测试创建角色缺少名称"""
        response = client.post(
            '/api/v1/characters',
            json={"age": 25},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
    
    def test_get_nonexistent_character(self, client):
        """测试获取不存在的角色"""
        response = client.get('/api/v1/characters/nonexistent-id')
        
        assert response.status_code == 404
    
    def test_simulation_missing_fields(self, client):
        """测试模拟请求缺少必需字段"""
        response = client.post(
            '/api/v1/simulation/start',
            json={},
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_narrative_missing_events(self, client):
        """测试叙事生成缺少事件"""
        response = client.post(
            '/api/v1/narratives/generate',
            json={"chapter_id": "test", "characters": []},
            content_type='application/json'
        )
        
        assert response.status_code == 400


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
