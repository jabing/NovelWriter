"""叙事生成 REST API"""
import logging
import uuid
from typing import Any, Dict, Tuple
from flask import Blueprint, jsonify, request
from pydantic import ValidationError as PydanticValidationError

from app.models import Character, PerspectiveBias, StoryEvent
from app.models.enums import ThinkingStyle, NarrativeVoice
from app.narrative.narrative_generator import NarrativeGenerator, MultiNarrativeResult
from app.narrative.perspective_agent import NarrativeResult
from app.schemas import CharacterCreate, EventCreate
from app.utils.error_handler import error_response, ErrorCode

logger = logging.getLogger(__name__)

narratives_bp = Blueprint('narratives', __name__)


# 内存存储 (实际应用中应使用数据库)
_narratives: Dict[str, Dict[str, Any]] = {}


def _narrative_result_to_dict(result: NarrativeResult) -> Dict[str, Any]:
    """Convert NarrativeResult dataclass to dictionary for JSON response"""
    return {
        "character_id": result.character_id,
        "chapter_id": result.chapter_id,
        "content": result.content,
        "perspective_bias": {
            "gender_bias": result.perspective_bias.gender_bias,
            "mbti_bias": result.perspective_bias.mbti_bias,
            "cognitive_bias": result.perspective_bias.cognitive_bias,
        } if result.perspective_bias else None,
        "filtered_events": result.filtered_events,
        "metadata": result.metadata,
    }


def _multi_narrative_result_to_dict(result: MultiNarrativeResult) -> Dict[str, Any]:
    """Convert MultiNarrativeResult dataclass to dictionary for JSON response"""
    return {
        "chapter_id": result.chapter_id,
        "narratives": [_narrative_result_to_dict(n) for n in result.narratives],
        "total_characters": result.total_characters,
        "metadata": result.metadata,
    }


def _parse_character(data: Dict[str, Any]) -> Character:
    """Parse character data from request"""
    # Create perspective bias if provided
    perspective_bias = None
    if "perspective_bias" in data:
        pb_data = data["perspective_bias"]
        perspective_bias = PerspectiveBias(
            gender_bias=pb_data.get("gender_bias", {}),
            mbti_bias=pb_data.get("mbti_bias", {}),
            cognitive_bias=pb_data.get("cognitive_bias", {}),
        )
    
    return Character(
        entity_id=data.get("entity_id", str(uuid.uuid4())),
        name=data.get("name", ""),
        description=data.get("description", ""),
        age=data.get("age"),
        gender=data.get("gender"),
        occupation=data.get("occupation"),
        mbti=data.get("mbti"),
        personality_traits=data.get("personality_traits", []),
        core_values=data.get("core_values", []),
        thinking_style=ThinkingStyle(data["thinking_style"]) if data.get("thinking_style") else None,
        emotional_tone=data.get("emotional_tone"),
        narrative_voice=NarrativeVoice(data["narrative_voice"]) if data.get("narrative_voice") else None,
        perspective_bias=perspective_bias,
        belief_graph_id=data.get("belief_graph_id"),
        character_layer=data.get("character_layer", 1),
        has_pov=data.get("has_pov", False),
        activity_level=data.get("activity_level", 0.5),
        influence_weight=data.get("influence_weight", 1.0),
        bio=data.get("bio", ""),
        detailed_persona=data.get("detailed_persona", ""),
        background_story=data.get("background_story", ""),
        motivations=data.get("motivations", []),
        fears=data.get("fears", []),
        goals=data.get("goals", []),
        friend_ids=data.get("friend_ids", []),
        enemy_ids=data.get("enemy_ids", []),
        family_ids=data.get("family_ids", []),
        source_entity_uuid=data.get("source_entity_uuid"),
        source_entity_type=data.get("source_entity_type"),
    )


def _parse_event(data: Dict[str, Any]) -> StoryEvent:
    """Parse event data from request"""
    return StoryEvent(
        entity_id=data.get("entity_id", str(uuid.uuid4())),
        name=data.get("name", ""),
        event_type=data.get("event_type", ""),
        title=data.get("title", ""),
        description=data.get("description", ""),
        participants=data.get("participants", []),
        witnesses=data.get("witnesses", []),
        location_id=data.get("location_id"),
        occurred_at=data.get("occurred_at", ""),
        duration=data.get("duration"),
        timeline_position=data.get("timeline_position"),
        impact_level=data.get("impact_level", 1),
        is_milestone=data.get("is_milestone", False),
        is_public=data.get("is_public", False),
        who_knows=data.get("who_knows", []),
        public_knowledge=data.get("public_knowledge", False),
        consequences=data.get("consequences", []),
        causes=data.get("causes", []),
    )


def _validate_generate_request(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate narrative generation request data"""
    if not data:
        return False, "Request body is required"
    
    if "characters" not in data:
        return False, "characters is required"
    
    if not isinstance(data["characters"], list):
        return False, "characters must be a list"
    
    if "events" not in data:
        return False, "events is required"
    
    if not isinstance(data["events"], list):
        return False, "events must be a list"
    
    if "chapter_id" not in data:
        return False, "chapter_id is required"
    
    return True, ""


@narratives_bp.route('/api/v1/narratives/generate', methods=['POST'])
def generate_narrative():
    """生成叙事"""
    data = request.get_json()
    
    if not data:
        return error_response(ErrorCode.INVALID_REQUEST, message="Request body is required")
    
    try:
        chapter_id = data.get("chapter_id")
        if not chapter_id:
            return error_response(ErrorCode.VALIDATION_ERROR, message="chapter_id is required")
        
        characters_data = data.get("characters", [])
        if not isinstance(characters_data, list):
            return error_response(ErrorCode.VALIDATION_ERROR, message="characters must be a list")
        
        events_data = data.get("events", [])
        if not isinstance(events_data, list):
            return error_response(ErrorCode.VALIDATION_ERROR, message="events must be a list")
        
        validated_characters = []
        for i, char_data in enumerate(characters_data):
            try:
                validated = CharacterCreate(**char_data)
                validated_characters.append(validated)
            except PydanticValidationError as e:
                errors = e.errors()  # type: ignore[attr-defined]
                return error_response(
                    ErrorCode.VALIDATION_ERROR,
                    message=f"Character {i}: {errors[0]['msg']}",
                    details={"fields": [{"field": errors[0]["loc"], "message": errors[0]["msg"]}]}
                )
        
        validated_events = []
        for i, event_data in enumerate(events_data):
            try:
                validated = EventCreate(**event_data)
                validated_events.append(validated)
            except PydanticValidationError as e:
                errors = e.errors()  # type: ignore[attr-defined]
                return error_response(
                    ErrorCode.VALIDATION_ERROR,
                    message=f"Event {i}: {errors[0]['msg']}",
                    details={"fields": [{"field": errors[0]["loc"], "message": errors[0]["msg"]}]}
                )
        
        context = data.get("context", "")
        temperature = data.get("temperature", 0.8)
        max_concurrent = data.get("max_concurrent", 5)
        
        generator = NarrativeGenerator()
        result = generator.generate(
            events=validated_events,
            characters=validated_characters,
            chapter_id=chapter_id,
            context=context,
            temperature=temperature,
            max_concurrent=max_concurrent,
        )
        
        narrative_id = str(uuid.uuid4())
        _narratives[narrative_id] = _multi_narrative_result_to_dict(result)
        _narratives[narrative_id]["id"] = narrative_id
        
        return jsonify(_narratives[narrative_id]), 201
    
    except Exception as e:
        logger.exception("Narrative generation failed")
        return error_response(ErrorCode.INTERNAL_ERROR, message=f"Narrative generation failed: {str(e)}")


@narratives_bp.route('/api/v1/narratives/<narrative_id>', methods=['GET'])
def get_narrative(narrative_id: str):
    """获取叙事"""
    narrative = _narratives.get(narrative_id)
    
    if not narrative:
        return error_response(ErrorCode.RESOURCE_NOT_FOUND, message="Narrative not found", details={"identifier": narrative_id})
    
    return jsonify(narrative), 200


@narratives_bp.route('/api/v1/narratives', methods=['GET'])
def list_narratives():
    """列出所有叙事"""
    narratives_list = list(_narratives.values())
    
    return jsonify({
        "narratives": narratives_list,
        "total": len(narratives_list)
    }), 200
