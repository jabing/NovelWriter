"""模拟控制 API

提供故事世界模拟的 REST API 接口。
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from flask import Blueprint, jsonify, request

from app.models import Character
from app.simulation.story_world_simulator import ChapterConfig, StoryWorldSimulator
from app.utils.error_handler import error_response, ErrorCode

logger = logging.getLogger(__name__)

simulation_bp = Blueprint('simulation', __name__)

# 内存存储模拟状态
_simulations: dict[str, dict[str, Any]] = {}


@simulation_bp.route('/api/v1/simulation/start', methods=['POST'])
def start_simulation():
    """开始模拟
    
    Request JSON:
        {
            "chapter_id": "ch1",
            "graph_id": "story_1",
            "outline": "章节大纲...",
            "characters": [
                {
                    "entity_id": "char_1",
                    "name": "Alice",
                    ...
                }
            ],
            "target_events": 3,
            "context": {}
        }
    
    Returns:
        {
            "simulation_id": "sim_xxx",
            "status": "running",
            "message": "Simulation started"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response(ErrorCode.INVALID_REQUEST, message="Request body is required")
        
        # 验证必需字段
        required_fields = ['chapter_id', 'graph_id', 'outline', 'characters']
        for field in required_fields:
            if field not in data:
                return error_response(ErrorCode.VALIDATION_ERROR, message=f"Missing required field: {field}")
        
        # 创建角色对象
        characters = []
        for char_data in data['characters']:
            try:
                # 从字典创建 Character 对象
                char = Character(
                    entity_id=char_data.get('entity_id', str(uuid.uuid4())),
                    name=char_data.get('name', 'Unknown'),
                    age=char_data.get('age'),
                    gender=char_data.get('gender'),
                    occupation=char_data.get('occupation'),
                    mbti=char_data.get('mbti'),
                    personality_traits=char_data.get('personality_traits', []),
                    core_values=char_data.get('core_values', []),
                    motivations=char_data.get('motivations', []),
                    fears=char_data.get('fears', []),
                    goals=char_data.get('goals', []),
                    character_layer=char_data.get('character_layer', 1),
                    bio=char_data.get('bio', ''),
                )
                characters.append(char)
            except Exception as e:
                logger.warning("Failed to create character: %s", e)
                continue
        
        if not characters:
            return error_response(ErrorCode.VALIDATION_ERROR, message="No valid characters provided")
        
        # 创建章节配置
        config = ChapterConfig(
            chapter_id=data['chapter_id'],
            graph_id=data['graph_id'],
            characters=characters,
            outline=data['outline'],
            target_events=data.get('target_events', 3),
            context=data.get('context', {}),
        )
        
        # 生成模拟 ID
        sim_id = f"sim_{uuid.uuid4().hex[:8]}"
        
        # 存储模拟状态
        _simulations[sim_id] = {
            "status": "running",
            "config": {
                "chapter_id": config.chapter_id,
                "graph_id": config.graph_id,
                "outline": config.outline,
                "target_events": config.target_events,
            },
            "result": None,
            "error": None,
        }
        
        # 创建模拟器并运行模拟
        try:
            simulator = StoryWorldSimulator()
            result = simulator.simulate_chapter(config)
            
            # 更新状态
            _simulations[sim_id]["status"] = "completed"
            _simulations[sim_id]["result"] = {
                "chapter_id": result.chapter_id,
                "events": [
                    {
                        "entity_id": e.entity_id,
                        "title": e.title,
                        "description": e.description,
                        "event_type": e.event_type,
                        "participants": e.participants,
                        "witnesses": e.witnesses,
                        "impact_level": e.impact_level,
                        "is_milestone": e.is_milestone,
                        "is_public": e.is_public,
                        "who_knows": e.who_knows,
                    }
                    for e in result.events
                ],
                "reactions_count": len(result.reactions),
                "graph_updates": result.graph_updates,
                "metadata": result.metadata,
            }
            
            logger.info("Simulation %s completed successfully", sim_id)
            
        except Exception as e:
            logger.error("Simulation %s failed: %s", sim_id, e)
            _simulations[sim_id]["status"] = "failed"
            _simulations[sim_id]["error"] = str(e)
        
        return jsonify({
            "simulation_id": sim_id,
            "status": _simulations[sim_id]["status"],
            "message": "Simulation started"
        }), 201
        
    except Exception as e:
        logger.exception("Failed to start simulation")
        return error_response(ErrorCode.INTERNAL_ERROR, message=f"Failed to start simulation: {str(e)}")


@simulation_bp.route('/api/v1/simulation/status/<sim_id>', methods=['GET'])
def get_status(sim_id: str):
    """查询模拟状态
    
    Args:
        sim_id: 模拟 ID
    
    Returns:
        {
            "simulation_id": "sim_xxx",
            "status": "running" | "completed" | "failed" | "not_found",
            "config": {...},
            "result": {...},
            "error": "..."
        }
    """
    if sim_id not in _simulations:
        return error_response(
            ErrorCode.RESOURCE_NOT_FOUND,
            message="Simulation not found",
            details={"identifier": sim_id}
        )
    
    sim_data = _simulations[sim_id]
    
    response = {
        "simulation_id": sim_id,
        "status": sim_data["status"],
        "config": sim_data.get("config"),
    }
    
    if sim_data["status"] == "completed" and sim_data.get("result"):
        response["result"] = sim_data["result"]
    
    if sim_data["status"] == "failed" and sim_data.get("error"):
        response["error"] = sim_data["error"]
    
    return jsonify(response), 200


@simulation_bp.route('/api/v1/simulation/stop/<sim_id>', methods=['POST'])
def stop_simulation(sim_id: str):
    """停止模拟
    
    Args:
        sim_id: 模拟 ID
    
    Returns:
        {
            "simulation_id": "sim_xxx",
            "status": "stopped",
            "message": "Simulation stopped"
        }
    """
    if sim_id not in _simulations:
        return error_response(
            ErrorCode.RESOURCE_NOT_FOUND,
            message="Simulation not found",
            details={"identifier": sim_id}
        )
    
    sim_data = _simulations[sim_id]
    
    # 如果模拟正在运行，标记为已停止
    # 注意：当前实现是同步的，此操作主要用于清理状态
    if sim_data["status"] == "running":
        sim_data["status"] = "stopped"
        logger.info("Simulation %s stopped by user", sim_id)
    
    return jsonify({
        "simulation_id": sim_id,
        "status": sim_data["status"],
        "message": "Simulation stopped"
    }), 200


@simulation_bp.route('/api/v1/simulation/list', methods=['GET'])
def list_simulations():
    """列出所有模拟
    
    Returns:
        {
            "simulations": [
                {
                    "simulation_id": "sim_xxx",
                    "status": "...",
                    "chapter_id": "..."
                }
            ]
        }
    """
    simulations = [
        {
            "simulation_id": sim_id,
            "status": data["status"],
            "chapter_id": data.get("config", {}).get("chapter_id"),
        }
        for sim_id, data in _simulations.items()
    ]
    
    return jsonify({"simulations": simulations}), 200
