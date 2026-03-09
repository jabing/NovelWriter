"""认知图谱管理器

管理角色认知图谱，包括信念的创建、更新、一致性检查等。
认知图谱存储角色主观认知，而非客观事实。
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.graph.story_graph_manager import StoryGraphManager
from app.models import StoryEntity, EntityType

logger = logging.getLogger(__name__)


class BeliefGraphError(Exception):
    """认知图谱错误"""
    pass


@dataclass
class Belief:
    """信念
    
    表示角色对某实体的主观认知。
    信念可能是正确的，也可能是错误或片面的。
    
    Attributes:
        belief_id: 信念唯一标识
        holder: 信念持有者（角色 entity_id）
        subject: 信念对象（实体 ID 或名称）
        content: 信念内容（如 "是个好人"、"喜欢我"）
        confidence: 信念置信度 (0.0-1.0)
        source: 信念来源（observation/rumor/inference）
        created_at: 创建时间
        updated_at: 更新时间
    """
    belief_id: str
    holder: str  # 信念持有者
    subject: str  # 信念对象
    content: str  # 信念内容
    confidence: float = 1.0
    source: str | None = None  # 来源 (观察/传闻/推断)
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        """验证信念参数"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"置信度必须在 0.0-1.0 之间，当前：{self.confidence}")
        
        if self.source and self.source not in ("observation", "rumor", "inference", "other"):
            logger.warning("未知的信念来源：%s", self.source)


@dataclass
class ConsistencyReport:
    """一致性报告
    
    检测信念冲突的结果。
    
    Attributes:
        is_consistent: 是否一致
        conflicts: 冲突的信念对列表
        warnings: 潜在矛盾的警告（非直接冲突）
    """
    is_consistent: bool
    conflicts: list[tuple[Belief, Belief]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    def add_conflict(self, belief1: Belief, belief2: Belief) -> None:
        """添加冲突"""
        self.conflicts.append((belief1, belief2))
        self.is_consistent = False


class BeliefGraphManager:
    """认知图谱管理器
    
    管理角色的主观认知图谱。每个角色有独立的认知图谱，
    存储其对故事世界中实体和关系的信念。
    
    注意：认知图谱存储的是主观信念，而非客观事实。
    不同角色对同一实体可能有完全不同的信念。
    
    Example:
        >>> manager = BeliefGraphManager()
        >>> graph_id = manager.create_belief_graph("alice")
        >>> belief = Belief(
        ...     belief_id="b1",
        ...     holder="alice",
        ...     subject="bob",
        ...     content="是个好人",
        ...     confidence=0.8,
        ...     source="observation"
        ... )
        >>> manager.add_belief(graph_id, belief)
    """
    
    def __init__(self, graph_manager: StoryGraphManager | None = None):
        """初始化认知图谱管理器
        
        Args:
            graph_manager: 故事图谱管理器，用于存储信念
        """
        self.graph_manager = graph_manager or StoryGraphManager()
        # 图谱到角色的映射
        self._graph_to_character: dict[str, str] = {}
    
    def _belief_to_entity(self, graph_id: str, belief: Belief) -> StoryEntity:
        """将信念转换为 StoryEntity（Belief 类型）
        
        Args:
            graph_id: 认知图谱 ID
            belief: 信念对象
            
        Returns:
            StoryEntity 对象
        """
        # 生成信念的自然语言名称
        name = f"{belief.holder} {belief.content} {belief.subject}"
        
        return StoryEntity(
            entity_id=belief.belief_id,
            entity_type=EntityType.BELIEF,
            name=name,
            description=f"{belief.holder}'s belief about {belief.subject}",
            properties={
                "belief_holder": belief.holder,
                "belief_subject": belief.subject,
                "belief_content": belief.content,
                "confidence": belief.confidence,
                "source": belief.source or "other",
                "created_at": belief.created_at or datetime.now().isoformat(),
                "updated_at": belief.updated_at or datetime.now().isoformat(),
                "belief_id": belief.belief_id,
                "graph_id": graph_id,
            },
        )
    
    def _entity_to_belief(self, entity: StoryEntity) -> Belief:
        """将 StoryEntity 转换为信念
        
        Args:
            entity: StoryEntity 对象
            
        Returns:
            Belief 对象
        """
        props = entity.properties
        return Belief(
            belief_id=props.get("belief_id", entity.entity_id),
            holder=props.get("belief_holder", ""),
            subject=props.get("belief_subject", ""),
            content=props.get("belief_content", ""),
            confidence=props.get("confidence", 1.0),
            source=props.get("source", "other"),
            created_at=props.get("created_at", entity.created_at),
            updated_at=props.get("updated_at", entity.updated_at),
        )
    
    def create_belief_graph(self, character_id: str) -> str:
        """创建角色认知图谱
        
        为指定角色创建独立的认知图谱。
        图谱 ID 格式：belief_{character_id}_{uuid}
        
        Args:
            character_id: 角色实体 ID
            
        Returns:
            创建的图谱 ID
            
        Raises:
            BeliefGraphError: 创建失败时抛出
        """
        graph_id = f"belief_{character_id}_{uuid.uuid4().hex[:8]}"
        
        try:
            self.graph_manager.create_graph(graph_id)
            self._graph_to_character[graph_id] = character_id
            
            logger.info("创建认知图谱成功：%s (角色：%s)", graph_id, character_id)
            return graph_id
        except Exception as e:
            raise BeliefGraphError(f"创建认知图谱失败：{e}") from e
    
    def add_belief(self, graph_id: str, belief: Belief) -> str:
        """添加信念到认知图谱
        
        Args:
            graph_id: 认知图谱 ID
            belief: 要添加的信念
            
        Returns:
            信念 ID
            
        Raises:
            BeliefGraphError: 添加失败时抛出
        """
        try:
            if not belief.belief_id:
                belief.belief_id = f"belief_{uuid.uuid4().hex[:8]}"
            
            now = datetime.now().isoformat()
            if not belief.created_at:
                belief.created_at = now
            if not belief.updated_at:
                belief.updated_at = now
            
            entity = self._belief_to_entity(graph_id, belief)
            self.graph_manager.add_entity(graph_id, entity)
            
            logger.info(
                "添加信念成功：%s -> %s: %s (置信度：%.2f)",
                graph_id,
                belief.subject,
                belief.content,
                belief.confidence,
            )
            return belief.belief_id
        except Exception as e:
            raise BeliefGraphError(f"添加信念失败：{e}") from e
    
    def update_belief(
        self,
        graph_id: str,
        belief_id: str,
        new_content: str | None = None,
        new_confidence: float | None = None,
    ) -> Belief:
        """更新信念
        
        更新指定信念的内容或置信度。
        
        Args:
            graph_id: 认知图谱 ID
            belief_id: 信念 ID
            new_content: 新的信念内容（可选）
            new_confidence: 新的置信度（可选）
            
        Returns:
            更新后的信念对象
            
        Raises:
            BeliefGraphError: 信念不存在或更新失败时抛出
        """
        try:
            entities = self.graph_manager.query_entities(
                graph_id,
                entity_type=EntityType.BELIEF,
                filters={"belief_id": belief_id},
            )
            
            if not entities:
                raise BeliefGraphError(f"信念不存在：{belief_id}")
            
            entity = entities[0]
            belief = self._entity_to_belief(entity)
            
            if new_content is not None:
                belief.content = new_content
            if new_confidence is not None:
                if not 0.0 <= new_confidence <= 1.0:
                    raise ValueError(f"置信度必须在 0.0-1.0 之间：{new_confidence}")
                belief.confidence = new_confidence
            
            belief.updated_at = datetime.now().isoformat()
            
            updated_entity = self._belief_to_entity(graph_id, belief)
            self.graph_manager.add_entity(graph_id, updated_entity)
            
            logger.info("更新信念成功：%s", belief_id)
            return belief
        except BeliefGraphError:
            raise
        except Exception as e:
            raise BeliefGraphError(f"更新信念失败：{e}") from e
    
    def _remove_belief_entity(self, graph_id: str, belief_id: str) -> None:
        """移除信念实体（内部方法）
        
        通过标记信念的 is_deleted 属性来实现逻辑删除。
        这样可以保持数据完整性，同时支持恢复操作。
        
        Args:
            graph_id: 认知图谱 ID
            belief_id: 信念 ID
            
        Raises:
            BeliefGraphError: 信念不存在时抛出
        """
        try:
            entities = self.graph_manager.query_entities(
                graph_id,
                entity_type=EntityType.BELIEF,
                filters={"belief_id": belief_id},
            )
            
            if not entities:
                raise BeliefGraphError(f"信念不存在：{belief_id}")
            
            entity = entities[0]
            belief = self._entity_to_belief(entity)
            
            # 标记为已删除（逻辑删除）
            belief.confidence = 0.0
            belief.updated_at = datetime.now().isoformat()
            
            # 更新实体，添加删除标记
            updated_entity = self._belief_to_entity(graph_id, belief)
            updated_entity.properties["is_deleted"] = True
            updated_entity.properties["deleted_at"] = belief.updated_at
            
            # 由于 ZepClient 不支持直接更新，我们通过添加新实体来实现
            # 在实际使用中，查询时会自动过滤 is_deleted=True 的实体
            self.graph_manager.add_entity(graph_id, updated_entity)
            
            logger.info("标记信念为已删除：%s", belief_id)
        except BeliefGraphError:
            raise
        except Exception as e:
            raise BeliefGraphError(f"移除信念失败：{e}") from e
    
    def remove_belief(self, graph_id: str, belief_id: str) -> None:
        """移除信念
        
        从认知图谱中移除指定信念。
        
        Args:
            graph_id: 认知图谱 ID
            belief_id: 信念 ID
            
        Raises:
            BeliefGraphError: 移除失败时抛出
        """
        try:
            self._remove_belief_entity(graph_id, belief_id)
            logger.info("移除信念成功：%s", belief_id)
        except Exception as e:
            raise BeliefGraphError(f"移除信念失败：{e}") from e
    
    def check_consistency(self, graph_id: str) -> ConsistencyReport:
        """检查信念一致性
        
        检测认知图谱中的信念冲突。
        冲突定义：同一主体存在矛盾的认知。
        
        例如：
        - "爱 Alice" vs "恨 Alice"
        - "是诚实的人" vs "是个骗子"
        
        Args:
            graph_id: 认知图谱 ID
            
        Returns:
            一致性报告，包含冲突列表
            
        Raises:
            BeliefGraphError: 检查失败时抛出
        """
        try:
            beliefs = self.get_all_beliefs(graph_id)
            report = ConsistencyReport(is_consistent=True)
            
            # 按主体分组
            beliefs_by_subject: dict[str, list[Belief]] = {}
            for belief in beliefs:
                if belief.subject not in beliefs_by_subject:
                    beliefs_by_subject[belief.subject] = []
                beliefs_by_subject[belief.subject].append(belief)
            
            # 检查每个主体的信念冲突
            for _subject, subject_beliefs in beliefs_by_subject.items():
                conflicts = self._detect_conflicts(subject_beliefs)
                for b1, b2 in conflicts:
                    report.add_conflict(b1, b2)
            
            if report.is_consistent:
                logger.info("信念一致性检查通过：%s", graph_id)
            else:
                logger.warning(
                    "检测到信念冲突：%s (冲突数：%d)",
                    graph_id,
                    len(report.conflicts),
                )
            
            return report
        except Exception as e:
            raise BeliefGraphError(f"一致性检查失败：{e}") from e
    
    def get_beliefs_about(self, graph_id: str, entity_id: str, include_deleted: bool = False) -> list[Belief]:
        """获取对某实体的所有信念
        
        Args:
            graph_id: 认知图谱 ID
            entity_id: 实体 ID
            include_deleted: 是否包含已删除的信念（默认 False）
            
        Returns:
            对该实体的信念列表
            
        Raises:
            BeliefGraphError: 查询失败时抛出
        """
        try:
            entities = self.graph_manager.query_entities(
                graph_id,
                entity_type=EntityType.BELIEF,
                filters={"belief_subject": entity_id},
            )
            
            beliefs = []
            for e in entities:
                if not include_deleted and e.properties.get("is_deleted"):
                    continue
                beliefs.append(self._entity_to_belief(e))
            
            logger.info("获取实体信念：%s -> %s (数量：%d)", graph_id, entity_id, len(beliefs))
            return beliefs
        except Exception as e:
            raise BeliefGraphError(f"查询信念失败：{e}") from e
    
    def get_all_beliefs(self, graph_id: str, include_deleted: bool = False) -> list[Belief]:
        """获取认知图谱中的所有信念
        
        Args:
            graph_id: 认知图谱 ID
            include_deleted: 是否包含已删除的信念（默认 False）
            
        Returns:
            所有信念列表
            
        Raises:
            BeliefGraphError: 查询失败时抛出
        """
        try:
            entities = self.graph_manager.query_entities(
                graph_id,
                entity_type=EntityType.BELIEF,
            )
            
            # 过滤出信念实体（通过 graph_id 匹配）
            beliefs = []
            for e in entities:
                if e.properties.get("graph_id") == graph_id:
                    # 跳过已删除的信念（除非明确要求包含）
                    if not include_deleted and e.properties.get("is_deleted"):
                        continue
                    beliefs.append(self._entity_to_belief(e))
            
            return beliefs
        except Exception as e:
            raise BeliefGraphError(f"查询所有信念失败：{e}") from e
    
    def get_beliefs_by_source(
        self,
        graph_id: str,
        source: str,
    ) -> list[Belief]:
        """获取特定来源的信念
        
        Args:
            graph_id: 认知图谱 ID
            source: 信念来源 (observation/rumor/inference)
            
        Returns:
            匹配的信念列表
            
        Raises:
            BeliefGraphError: 查询失败时抛出
        """
        try:
            all_beliefs = self.get_all_beliefs(graph_id)
            beliefs = [b for b in all_beliefs if b.source == source]
            
            logger.info("获取来源信念：%s -> %s (数量：%d)", graph_id, source, len(beliefs))
            return beliefs
        except Exception as e:
            raise BeliefGraphError(f"查询来源信念失败：{e}") from e
    
    # ==================== 私有辅助方法 ====================
    
    def _detect_conflicts(
        self,
        beliefs: list[Belief],
    ) -> list[tuple[Belief, Belief]]:
        """检测同一主体的信念冲突
        
        Args:
            beliefs: 对该主体的信念列表
            
        Returns:
            冲突的信念对列表
        """
        conflicts = []
        
        # 定义冲突关键词对（支持正则表达式，中英文）
        conflict_pairs = [
            # 情感冲突
            (r"(爱|喜欢|倾心|迷恋|爱慕|钟爱|love|likes|like)", r"(恨|讨厌|厌恶|憎恶|痛恨|憎恨|hate|hates|hated)"),
            (r"(爱|喜欢|love|likes|like)", r"(恨|讨厌|hate|hates|hated)"),
            # 品质冲突
            (r"(诚实|正直|诚信|真诚|honest|integrity)", r"(骗子|虚伪|虚假|狡诈|欺诈|liar|fake|deceitful)"),
            (r"(善良|仁慈|慈悲|kind|kindness)", r"(邪恶|恶毒|狠毒|残忍|evil|cruel|vicious)"),
            (r"(勇敢|无畏|英勇|brave|bravery|courage)", r"(懦弱|胆小|怯懦|怯弱|coward|cowardly)"),
            (r"(聪明|智慧|机智|聪慧|smart|clever|wise)", r"(愚蠢|笨|傻|愚钝|stupid|fool|dumb)"),
            (r"(富有|有钱|富裕|rich|wealthy)", r"(贫穷|穷|贫困|潦倒|poor|broke)"),
            # 关系冲突
            (r"(朋友|挚友|好友|友人|friend|friends)", r"(敌人|仇人|对手|敌|enemy|enemies|foe)"),
            (r"(忠诚|忠心|忠贞|loyal|loyalty)", r"(背叛|不忠|叛徒|背弃|betray|betrayal|traitor)"),
            (r"(信任|信赖|trust|trusts)", r"(怀疑|猜疑|猜忌|doubt|suspect|suspicion)"),
            # 能力冲突
            (r"(强大|厉害|强|强力|strong|powerful)", r"(弱|弱小|无能|虚弱|weak|weakness|incompetent)"),
            (r"(可靠|可信|值得信赖|可靠|reliable|trustworthy)", r"(不可靠|不可信|靠不住|unreliable|untrustworthy)"),
            (r"(优秀|出色|卓越|excellent|outstanding)", r"(平庸|差劲|低劣|mediocre|terrible)"),
            # 道德冲突
            (r"(正义|公正|公平|justice|fair)", r"(邪恶|偏私|不公|evil|unfair|unjust)"),
            (r"(宽容|大度|tolerant|generous)", r"(狭隘|小气|吝啬|narrow-minded|stingy)"),
            # 性格冲突
            (r"(开朗|乐观|积极|cheerful|optimistic|positive)", r"(悲观|消极|阴郁|pessimistic|negative|gloomy)"),
            (r"(慷慨|大方|generous|generosity)", r"(吝啬|小气|抠门|stingy|cheap|miserly)"),
        ]
        
        # 检查每对信念
        for i, b1 in enumerate(beliefs):
            for b2 in beliefs[i + 1:]:
                if self._are_conflicting(b1.content, b2.content, conflict_pairs):
                    conflicts.append((b1, b2))
        
        return conflicts
    
    def _are_conflicting(
        self,
        content1: str,
        content2: str,
        conflict_pairs: list[tuple[str, str]],
    ) -> bool:
        """检查两个信念内容是否冲突
        
        Args:
            content1: 第一个信念内容
            content2: 第二个信念内容
            conflict_pairs: 冲突关键词对
            
        Returns:
            是否冲突
        """
        for pattern1, pattern2 in conflict_pairs:
            if (re.search(pattern1, content1) and re.search(pattern2, content2)) or \
               (re.search(pattern2, content1) and re.search(pattern1, content2)):
                return True
        
        # 检查明显的否定冲突
        # 例如："是好人" vs "不是好人"
        if self._are_negations(content1, content2):
            return True
        
        return False
    
    def _are_negations(self, content1: str, content2: str) -> bool:
        """检查两个内容是否互为否定
        
        Args:
            content1: 第一个内容
            content2: 第二个内容
            
        Returns:
            是否互为否定
        """
        # 去除空白
        c1 = content1.strip()
        c2 = content2.strip()
        
        # 检查 "是 X" vs "不是 X" 或 "不 X"
        if c1.startswith("是") and (c2.startswith("不是") or c2.startswith("不")):
            if c1[1:] in c2[2:] or c2[2:] in c1[1:]:
                return True
        
        if c2.startswith("是") and (c1.startswith("不是") or c1.startswith("不")):
            if c2[1:] in c1[2:] or c1[2:] in c2[1:]:
                return True
        
        # 检查 "有 X" vs "没有 X"
        if c1.startswith("有") and c2.startswith("没有"):
            if c1[1:] in c2[2:] or c2[2:] in c1[1:]:
                return True
        
        if c2.startswith("有") and c1.startswith("没有"):
            if c2[1:] in c1[2:] or c1[2:] in c2[1:]:
                return True
        
        return False
    
    def merge_beliefs(
        self,
        graph_id: str,
        new_belief: Belief,
        strategy: str = "keep_higher_confidence",
    ) -> Belief | None:
        """合并信念
        
        当新信念与现有信念冲突时，根据策略决定如何处理。
        
        Args:
            graph_id: 认知图谱 ID
            new_belief: 新信念
            strategy: 合并策略
                - "keep_higher_confidence": 保留置信度更高的
                - "keep_newer": 保留新信念
                - "keep_both": 都保留（默认）
                
        Returns:
            被替换的信念（如果有），否则返回 None
            
        Raises:
            BeliefGraphError: 合并失败时抛出
        """
        try:
            existing = self.get_beliefs_about(graph_id, new_belief.subject)
            conflicting = []
            
            for belief in existing:
                if self._are_conflicting(
                    new_belief.content,
                    belief.content,
                    [],  # 简单检查
                ) or self._are_negations(new_belief.content, belief.content):
                    conflicting.append(belief)
            
            if not conflicting:
                return None
            
            if strategy == "keep_newer":
                # 移除冲突的旧信念
                for old in conflicting:
                    self.remove_belief(graph_id, old.belief_id)
                return conflicting[0] if conflicting else None
            
            if strategy == "keep_higher_confidence":
                # 比较置信度
                for old in conflicting:
                    if new_belief.confidence > old.confidence:
                        self.remove_belief(graph_id, old.belief_id)
                        return old
                    else:
                        # 不添加新信念
                        return old
            
            # "keep_both" 或其他策略：不做处理
            return None
        except Exception as e:
            raise BeliefGraphError(f"合并信念失败：{e}") from e
        
        if strategy == "keep_newer":
            # 移除冲突的旧信念
            for old in conflicting:
                self.remove_belief(graph_id, old.belief_id)
            return conflicting[0] if conflicting else None
        
        if strategy == "keep_higher_confidence":
            # 比较置信度
            for old in conflicting:
                if new_belief.confidence > old.confidence:
                    self.remove_belief(graph_id, old.belief_id)
                    return old
                else:
                    # 不添加新信念
                    return old
        
        # "keep_both" 或其他策略：不做处理
        return None
