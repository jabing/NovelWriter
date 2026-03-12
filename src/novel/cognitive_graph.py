"""
Cognitive Graph - 简化版认知图谱（原型）

使用 NetworkX 实现基础事实存储和关系管理。
"""

import networkx as nx
from typing import Dict, List, Any, Optional


class CognitiveGraph:
    """简化版认知图谱（原型）
    
    用于存储和管理小说世界中的角色、地点、情节等元素及其关系。
    
    Attributes:
        graph_id: 图谱标识符
        graph: NetworkX 有向图对象
    """
    
    def __init__(self, graph_id: str = "default"):
        """初始化认知图谱
        
        Args:
            graph_id: 图谱标识符，默认为 "default"
        """
        self.graph_id = graph_id
        self.graph = nx.DiGraph()
    
    def add_character_node(self, character_id: str, properties: Dict[str, Any]):
        """添加角色节点
        
        Args:
            character_id: 角色唯一标识符
            properties: 角色属性字典，如 {"name": "张三", "age": 25}
        """
        self.graph.add_node(
            character_id,
            node_type="character",
            **properties
        )
    
    def add_location_node(self, location_id: str, properties: Dict[str, Any]):
        """添加地点节点
        
        Args:
            location_id: 地点唯一标识符
            properties: 地点属性字典，如 {"name": "北京", "type": "城市"}
        """
        self.graph.add_node(
            location_id,
            node_type="location",
            **properties
        )
    
    def add_plot_thread_node(self, plot_thread_id: str, properties: Dict[str, Any]):
        """添加情节线索节点
        
        Args:
            plot_thread_id: 情节线索唯一标识符
            properties: 情节线索属性字典
        """
        self.graph.add_node(
            plot_thread_id,
            node_type="plot_thread",
            **properties
        )
    
    def add_relationship(self, from_id: str, to_id: str, relation_type: str, 
                        properties: Optional[Dict[str, Any]] = None):
        """添加关系边
        
        Args:
            from_id: 起始节点 ID
            to_id: 目标节点 ID
            relation_type: 关系类型，如 "knows", "located_at", "involved_in"
            properties: 可选的关系属性字典
        """
        self.graph.add_edge(
            from_id,
            to_id,
            relation_type=relation_type,
            **(properties or {})
        )
    
    def get_character_knowledge(self, character_id: str) -> Dict[str, Any]:
        """获取角色的认知信息
        
        Args:
            character_id: 角色唯一标识符
            
        Returns:
            角色节点的属性字典，如果角色不存在则返回空字典
        """
        if character_id not in self.graph:
            return {}
        return dict(self.graph.nodes[character_id])
    
    def get_node_info(self, node_id: str) -> Dict[str, Any]:
        """获取节点的完整信息
        
        Args:
            node_id: 节点唯一标识符
            
        Returns:
            节点的属性字典，如果节点不存在则返回空字典
        """
        if node_id not in self.graph:
            return {}
        return dict(self.graph.nodes[node_id])
    
    def get_neighbors(self, node_id: str, relation_type: Optional[str] = None) -> List[str]:
        """获取邻居节点
        
        Args:
            node_id: 节点唯一标识符
            relation_type: 可选的关系类型过滤器
            
        Returns:
            邻居节点 ID 列表
        """
        if node_id not in self.graph:
            return []
        
        if relation_type:
            # 过滤特定关系类型
            neighbors = []
            for neighbor in self.graph.neighbors(node_id):
                edge_data = self.graph.get_edge_data(node_id, neighbor)
                if edge_data and edge_data.get("relation_type") == relation_type:
                    neighbors.append(neighbor)
            return neighbors
        
        return list(self.graph.neighbors(node_id))
    
    def get_predecessors(self, node_id: str, relation_type: Optional[str] = None) -> List[str]:
        """获取前驱节点
        
        Args:
            node_id: 节点唯一标识符
            relation_type: 可选的关系类型过滤器
            
        Returns:
            前驱节点 ID 列表
        """
        if node_id not in self.graph:
            return []
        
        if relation_type:
            predecessors = []
            for pred in self.graph.predecessors(node_id):
                edge_data = self.graph.get_edge_data(pred, node_id)
                if edge_data and edge_data.get("relation_type") == relation_type:
                    predecessors.append(pred)
            return predecessors
        
        return list(self.graph.predecessors(node_id))
    
    def has_node(self, node_id: str) -> bool:
        """检查节点是否存在
        
        Args:
            node_id: 节点唯一标识符
            
        Returns:
            如果节点存在返回 True，否则返回 False
        """
        return node_id in self.graph
    
    def has_edge(self, from_id: str, to_id: str) -> bool:
        """检查边是否存在
        
        Args:
            from_id: 起始节点 ID
            to_id: 目标节点 ID
            
        Returns:
            如果边存在返回 True，否则返回 False
        """
        return self.graph.has_edge(from_id, to_id)
    
    def get_all_nodes_by_type(self, node_type: str) -> List[str]:
        """获取指定类型的所有节点
        
        Args:
            node_type: 节点类型，如 "character", "location", "plot_thread"
            
        Returns:
            节点 ID 列表
        """
        nodes = []
        for node_id, attrs in self.graph.nodes(data=True):
            if attrs.get("node_type") == node_type:
                nodes.append(node_id)
        return nodes
    
    def get_edge_info(self, from_id: str, to_id: str) -> Dict[str, Any]:
        """获取边的信息
        
        Args:
            from_id: 起始节点 ID
            to_id: 目标节点 ID
            
        Returns:
            边的属性字典，如果边不存在则返回空字典
        """
        if not self.graph.has_edge(from_id, to_id):
            return {}
        return dict(self.graph.get_edge_data(from_id, to_id))
    
    def remove_node(self, node_id: str):
        """移除节点及其相关的边
        
        Args:
            node_id: 节点唯一标识符
        """
        if node_id in self.graph:
            self.graph.remove_node(node_id)
    
    def remove_edge(self, from_id: str, to_id: str):
        """移除边
        
        Args:
            from_id: 起始节点 ID
            to_id: 目标节点 ID
        """
        if self.graph.has_edge(from_id, to_id):
            self.graph.remove_edge(from_id, to_id)
    
    def get_node_count(self) -> int:
        """获取节点总数
        
        Returns:
            节点数量
        """
        return self.graph.number_of_nodes()
    
    def get_edge_count(self) -> int:
        """获取边总数
        
        Returns:
            边数量
        """
        return self.graph.number_of_edges()
    
    def clear(self):
        """清空图谱"""
        self.graph.clear()
