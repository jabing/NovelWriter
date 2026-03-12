import pytest
import sys
from pathlib import Path

# 在导入前添加 src 到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
src_path = PROJECT_ROOT / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from novel.cognitive_graph import CognitiveGraph


class TestCognitiveGraphInit:
    """测试初始化功能"""
    
    def test_default_init(self):
        """测试默认初始化"""
        graph = CognitiveGraph()
        assert graph.graph_id == "default"
        assert graph.get_node_count() == 0
        assert graph.get_edge_count() == 0
    
    def test_custom_id_init(self):
        """测试自定义 ID 初始化"""
        graph = CognitiveGraph(graph_id="test_graph")
        assert graph.graph_id == "test_graph"


class TestCharacterNodes:
    """测试角色节点操作"""
    
    def test_add_character_node(self):
        """测试添加角色节点"""
        graph = CognitiveGraph()
        graph.add_character_node(
            "char_001",
            {"name": "张三", "age": 25, "occupation": "程序员"}
        )
        
        assert graph.has_node("char_001")
        node_info = graph.get_node_info("char_001")
        assert node_info["node_type"] == "character"
        assert node_info["name"] == "张三"
        assert node_info["age"] == 25
    
    def test_get_character_knowledge(self):
        """测试获取角色认知信息"""
        graph = CognitiveGraph()
        graph.add_character_node(
            "char_002",
            {"name": "李四", "skill": "武术"}
        )
        
        knowledge = graph.get_character_knowledge("char_002")
        assert knowledge["node_type"] == "character"
        assert knowledge["name"] == "李四"
        assert knowledge["skill"] == "武术"
    
    def test_get_nonexistent_character(self):
        """测试获取不存在的角色"""
        graph = CognitiveGraph()
        knowledge = graph.get_character_knowledge("nonexistent")
        assert knowledge == {}
    
    def test_add_multiple_characters(self):
        """测试添加多个角色"""
        graph = CognitiveGraph()
        graph.add_character_node("char_001", {"name": "张三"})
        graph.add_character_node("char_002", {"name": "李四"})
        graph.add_character_node("char_003", {"name": "王五"})
        
        assert graph.get_node_count() == 3
        characters = graph.get_all_nodes_by_type("character")
        assert len(characters) == 3


class TestLocationNodes:
    """测试地点节点操作"""
    
    def test_add_location_node(self):
        """测试添加地点节点"""
        graph = CognitiveGraph()
        graph.add_location_node(
            "loc_001",
            {"name": "北京", "type": "城市", "country": "中国"}
        )
        
        assert graph.has_node("loc_001")
        node_info = graph.get_node_info("loc_001")
        assert node_info["node_type"] == "location"
        assert node_info["name"] == "北京"
    
    def test_add_multiple_locations(self):
        """测试添加多个地点"""
        graph = CognitiveGraph()
        graph.add_location_node("loc_001", {"name": "北京"})
        graph.add_location_node("loc_002", {"name": "上海"})
        
        locations = graph.get_all_nodes_by_type("location")
        assert len(locations) == 2


class TestPlotThreadNodes:
    """测试情节线索节点操作"""
    
    def test_add_plot_thread_node(self):
        """测试添加情节线索节点"""
        graph = CognitiveGraph()
        graph.add_plot_thread_node(
            "plot_001",
            {"title": "复仇之路", "status": "进行中"}
        )
        
        assert graph.has_node("plot_001")
        node_info = graph.get_node_info("plot_001")
        assert node_info["node_type"] == "plot_thread"
        assert node_info["title"] == "复仇之路"


class TestRelationships:
    """测试关系操作"""
    
    def test_add_relationship(self):
        """测试添加关系"""
        graph = CognitiveGraph()
        graph.add_character_node("char_001", {"name": "张三"})
        graph.add_character_node("char_002", {"name": "李四"})
        
        graph.add_relationship(
            "char_001",
            "char_002",
            "knows",
            {"since": "2020", "strength": "strong"}
        )
        
        assert graph.has_edge("char_001", "char_002")
        edge_info = graph.get_edge_info("char_001", "char_002")
        assert edge_info["relation_type"] == "knows"
        assert edge_info["since"] == "2020"
    
    def test_add_location_relationship(self):
        """测试添加地点关系"""
        graph = CognitiveGraph()
        graph.add_character_node("char_001", {"name": "张三"})
        graph.add_location_node("loc_001", {"name": "北京"})
        
        graph.add_relationship(
            "char_001",
            "loc_001",
            "located_at"
        )
        
        assert graph.has_edge("char_001", "loc_001")
        edge_info = graph.get_edge_info("char_001", "loc_001")
        assert edge_info["relation_type"] == "located_at"
    
    def test_add_plot_relationship(self):
        """测试添加情节关系"""
        graph = CognitiveGraph()
        graph.add_character_node("char_001", {"name": "张三"})
        graph.add_plot_thread_node("plot_001", {"title": "复仇之路"})
        
        graph.add_relationship(
            "char_001",
            "plot_001",
            "involved_in"
        )
        
        assert graph.has_edge("char_001", "plot_001")


class TestNeighbors:
    """测试邻居节点查询"""
    
    def test_get_neighbors_all(self):
        """测试获取所有邻居"""
        graph = CognitiveGraph()
        graph.add_character_node("char_001", {"name": "张三"})
        graph.add_character_node("char_002", {"name": "李四"})
        graph.add_character_node("char_003", {"name": "王五"})
        
        graph.add_relationship("char_001", "char_002", "knows")
        graph.add_relationship("char_001", "char_003", "knows")
        
        neighbors = graph.get_neighbors("char_001")
        assert len(neighbors) == 2
        assert "char_002" in neighbors
        assert "char_003" in neighbors
    
    def test_get_neighbors_filtered(self):
        """测试按关系类型过滤邻居"""
        graph = CognitiveGraph()
        graph.add_character_node("char_001", {"name": "张三"})
        graph.add_character_node("char_002", {"name": "李四"})
        graph.add_character_node("char_003", {"name": "王五"})
        
        graph.add_relationship("char_001", "char_002", "knows")
        graph.add_relationship("char_001", "char_003", "hates")
        
        knows_neighbors = graph.get_neighbors("char_001", relation_type="knows")
        assert len(knows_neighbors) == 1
        assert "char_002" in knows_neighbors
        
        hates_neighbors = graph.get_neighbors("char_001", relation_type="hates")
        assert len(hates_neighbors) == 1
        assert "char_003" in hates_neighbors
    
    def test_get_neighbors_nonexistent_node(self):
        """测试获取不存在节点的邻居"""
        graph = CognitiveGraph()
        neighbors = graph.get_neighbors("nonexistent")
        assert neighbors == []
    
    def test_get_predecessors(self):
        """测试获取前驱节点"""
        graph = CognitiveGraph()
        graph.add_character_node("char_001", {"name": "张三"})
        graph.add_character_node("char_002", {"name": "李四"})
        
        graph.add_relationship("char_001", "char_002", "knows")
        
        predecessors = graph.get_predecessors("char_002")
        assert len(predecessors) == 1
        assert "char_001" in predecessors


class TestNodeRemoval:
    """测试节点移除"""
    
    def test_remove_node(self):
        """测试移除节点"""
        graph = CognitiveGraph()
        graph.add_character_node("char_001", {"name": "张三"})
        
        assert graph.has_node("char_001")
        graph.remove_node("char_001")
        assert not graph.has_node("char_001")
    
    def test_remove_edge(self):
        """测试移除边"""
        graph = CognitiveGraph()
        graph.add_character_node("char_001", {"name": "张三"})
        graph.add_character_node("char_002", {"name": "李四"})
        graph.add_relationship("char_001", "char_002", "knows")
        
        assert graph.has_edge("char_001", "char_002")
        graph.remove_edge("char_001", "char_002")
        assert not graph.has_edge("char_001", "char_002")


class TestClearGraph:
    """测试清空图谱"""
    
    def test_clear(self):
        """测试清空图谱"""
        graph = CognitiveGraph()
        graph.add_character_node("char_001", {"name": "张三"})
        graph.add_location_node("loc_001", {"name": "北京"})
        graph.add_relationship("char_001", "loc_001", "located_at")
        
        assert graph.get_node_count() == 2
        assert graph.get_edge_count() == 1
        
        graph.clear()
        
        assert graph.get_node_count() == 0
        assert graph.get_edge_count() == 0


class TestEdgeCases:
    """测试边界情况"""
    
    def test_add_relationship_nonexistent_nodes(self):
        """测试添加不存在节点之间的关系"""
        graph = CognitiveGraph()
        # NetworkX 允许添加不存在节点之间的边
        graph.add_relationship("nonexistent1", "nonexistent2", "knows")
        assert graph.has_edge("nonexistent1", "nonexistent2")
    
    def test_get_edge_info_nonexistent_edge(self):
        """测试获取不存在边的信息"""
        graph = CognitiveGraph()
        edge_info = graph.get_edge_info("nonexistent1", "nonexistent2")
        assert edge_info == {}
    
    def test_remove_nonexistent_node(self):
        """测试移除不存在的节点"""
        graph = CognitiveGraph()
        # 不应该抛出异常
        graph.remove_node("nonexistent")
    
    def test_remove_nonexistent_edge(self):
        """测试移除不存在的边"""
        graph = CognitiveGraph()
        # 不应该抛出异常
        graph.remove_edge("nonexistent1", "nonexistent2")


class TestIntegration:
    """集成测试"""
    
    def test_complete_scenario(self):
        """测试完整场景"""
        graph = CognitiveGraph(graph_id="novel_world")
        
        # 添加角色
        graph.add_character_node("protagonist", {
            "name": "林风",
            "age": 20,
            "role": "主角"
        })
        graph.add_character_node("mentor", {
            "name": "老者",
            "age": 80,
            "role": "导师"
        })
        graph.add_character_node("antagonist", {
            "name": "魔头",
            "age": 500,
            "role": "反派"
        })
        
        # 添加地点
        graph.add_location_node("village", {
            "name": "青石村",
            "type": "村庄"
        })
        graph.add_location_node("mountain", {
            "name": "青云山",
            "type": "山脉"
        })
        
        # 添加情节线索
        graph.add_plot_thread_node("main_plot", {
            "title": "修仙之路",
            "status": "active"
        })
        
        # 添加关系
        graph.add_relationship("protagonist", "village", "located_at")
        graph.add_relationship("protagonist", "mentor", "knows")
        graph.add_relationship("mentor", "protagonist", "teaches")
        graph.add_relationship("protagonist", "antagonist", "opposes")
        graph.add_relationship("protagonist", "main_plot", "involved_in")
        graph.add_relationship("mentor", "mountain", "located_at")
        
        # 验证
        assert graph.get_node_count() == 6
        assert graph.get_edge_count() == 6
        
        # 查询主角的认知
        knowledge = graph.get_character_knowledge("protagonist")
        assert knowledge["name"] == "林风"
        assert knowledge["role"] == "主角"
        
        # 查询主角的位置
        location_neighbors = graph.get_neighbors("protagonist", relation_type="located_at")
        assert len(location_neighbors) == 1
        assert location_neighbors[0] == "village"
        
        # 查询主角认识的人
        knows_neighbors = graph.get_neighbors("protagonist", relation_type="knows")
        assert len(knows_neighbors) == 1
        assert knows_neighbors[0] == "mentor"
        
        # 查询所有角色
        all_characters = graph.get_all_nodes_by_type("character")
        assert len(all_characters) == 3
        
        # 查询所有地点
        all_locations = graph.get_all_nodes_by_type("location")
        assert len(all_locations) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
