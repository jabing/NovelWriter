"""角色管理 REST API"""
import uuid
from datetime import datetime
from typing import Any, Dict, Tuple
from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.database import db
from app.models import Character, PerspectiveBias
from app.models.db_models import CharacterDB
from app.models.enums import ThinkingStyle, NarrativeVoice, EntityType
from app.schemas import CharacterCreate, CharacterUpdate, CharacterResponse

characters_bp = Blueprint('characters', __name__)


def _error_response(message: str, status_code: int = 400) -> Tuple[Any, int]:
    """统一错误响应格式"""
    return jsonify({
        "error": {
            "message": message,
            "type": "validation_error"
        }
    }), status_code


def _character_db_to_dict(character: CharacterDB) -> Dict[str, Any]:
    """Convert CharacterDB model to dictionary for JSON response"""
    result = {
        "id": character.id,
        "entity_id": character.entity_id,
        "entity_type": character.entity_type,
        "name": character.name,
        "description": character.description,
        "properties": character.properties,
        "created_at": character.created_at,
        "updated_at": character.updated_at,
        "age": character.age,
        "gender": character.gender,
        "occupation": character.occupation,
        "mbti": character.mbti,
        "personality_traits": character.personality_traits,
        "core_values": character.core_values,
        "thinking_style": character.thinking_style,
        "emotional_tone": character.emotional_tone,
        "narrative_voice": character.narrative_voice,
        "perspective_bias": character.perspective_bias,
        "belief_graph_id": character.belief_graph_id,
        "character_layer": character.character_layer,
        "has_pov": character.has_pov,
        "activity_level": character.activity_level,
        "influence_weight": character.influence_weight,
        "bio": character.bio,
        "detailed_persona": character.detailed_persona,
        "background_story": character.background_story,
        "motivations": character.motivations,
        "fears": character.fears,
        "goals": character.goals,
        "friend_ids": character.friend_ids,
        "enemy_ids": character.enemy_ids,
        "family_ids": character.family_ids,
        "source_entity_uuid": character.source_entity_uuid,
        "source_entity_type": character.source_entity_type,
    }
    
    return result


def _validate_character_data(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, str]:
    """Validate character request data"""
    if not data:
        return False, "Request body is required"
    
    if not is_update and "name" not in data:
        return False, "name is required"
    
    return True, ""


@characters_bp.route('/api/v1/characters', methods=['POST'])
def create_character():
    """创建角色"""
    data = request.get_json()
    
    if not data:
        return _error_response("Request body is required", 400)
    
    try:
        validated_data = CharacterCreate(**data)
    except ValidationError as e:
        errors = e.errors()
        error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in errors]
        return _error_response("; ".join(error_messages), 422)
    
    entity_id = str(uuid.uuid4())
    
    existing = CharacterDB.query.filter_by(entity_id=entity_id).first()
    if existing:
        return _error_response("Character with this entity_id already exists", 409)
    
    try:
        perspective_bias = None
        if validated_data.perspective_bias:
            pb_data = validated_data.perspective_bias
            perspective_bias = PerspectiveBias(
                gender_bias=pb_data.gender_bias,
                mbti_bias=pb_data.mbti_bias,
                cognitive_bias=pb_data.cognitive_bias,
            )
        
        character = Character(
            entity_id=entity_id,
            entity_type=EntityType(validated_data.entity_type.value),
            name=validated_data.name,
            description=validated_data.description or "",
            properties=validated_data.properties or {},
            age=validated_data.age,
            gender=validated_data.gender,
            occupation=validated_data.occupation,
            mbti=validated_data.mbti,
            personality_traits=validated_data.personality_traits,
            core_values=validated_data.core_values,
            thinking_style=ThinkingStyle(validated_data.thinking_style.value) if validated_data.thinking_style else None,
            emotional_tone=validated_data.emotional_tone,
            narrative_voice=NarrativeVoice(validated_data.narrative_voice.value) if validated_data.narrative_voice else None,
            perspective_bias=perspective_bias,
            belief_graph_id=validated_data.belief_graph_id,
            character_layer=validated_data.character_layer,
            has_pov=validated_data.has_pov,
            activity_level=validated_data.activity_level,
            influence_weight=validated_data.influence_weight,
            bio=validated_data.bio,
            detailed_persona=validated_data.detailed_persona,
            background_story=validated_data.background_story,
            motivations=validated_data.motivations,
            fears=validated_data.fears,
            goals=validated_data.goals,
            friend_ids=validated_data.friend_ids,
            enemy_ids=validated_data.enemy_ids,
            family_ids=validated_data.family_ids,
            source_entity_uuid=validated_data.source_entity_uuid,
            source_entity_type=validated_data.source_entity_type,
        )
        
        character_db = CharacterDB.from_dataclass(character)
        
        db.session.add(character_db)
        db.session.commit()
        
        return jsonify(_character_db_to_dict(character_db)), 201
    
    except Exception as e:
        db.session.rollback()
        return _error_response(f"Failed to create character: {str(e)}", 500)


@characters_bp.route('/api/v1/characters/<character_id>', methods=['GET'])
def get_character(character_id: str):
    """获取角色"""
    character = CharacterDB.query.filter_by(entity_id=character_id).first()
    
    if not character:
        return _error_response("Character not found", 404)
    
    return jsonify(_character_db_to_dict(character)), 200


@characters_bp.route('/api/v1/characters/<character_id>', methods=['PUT'])
def update_character(character_id: str):
    """更新角色"""
    character = CharacterDB.query.filter_by(entity_id=character_id).first()
    
    if not character:
        return _error_response("Character not found", 404)
    
    data = request.get_json()
    
    if not data:
        return _error_response("Request body is required", 400)
    
    try:
        validated_data = CharacterUpdate(**data)
    except ValidationError as e:
        errors = e.errors()
        error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in errors]
        return _error_response("; ".join(error_messages), 422)
    
    try:
        update_fields = validated_data.model_dump(exclude_unset=True)
        
        for field, value in update_fields.items():
            if field == "perspective_bias" and value is not None:
                character.perspective_bias = value
            elif field == "thinking_style" and value is not None:
                character.thinking_style = value
            elif field == "narrative_voice" and value is not None:
                character.narrative_voice = value
            elif field == "entity_type" and value is not None:
                character.entity_type = value
            elif value is not None:
                setattr(character, field, value)
        
        character.updated_at = datetime.now().isoformat()
        
        db.session.commit()
        
        return jsonify(_character_db_to_dict(character)), 200
    
    except Exception as e:
        db.session.rollback()
        return _error_response(f"Failed to update character: {str(e)}", 500)


@characters_bp.route('/api/v1/characters/<character_id>', methods=['DELETE'])
def delete_character(character_id: str):
    """删除角色"""
    character = CharacterDB.query.filter_by(entity_id=character_id).first()
    
    if not character:
        return _error_response("Character not found", 404)
    
    try:
        db.session.delete(character)
        db.session.commit()
        
        return jsonify({"message": "Character deleted successfully"}), 200
    
    except Exception as e:
        db.session.rollback()
        return _error_response(f"Failed to delete character: {str(e)}", 500)


@characters_bp.route('/api/v1/characters', methods=['GET'])
def list_characters():
    """列出角色"""
    # Support pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Query with pagination
    pagination = CharacterDB.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    characters_list = [_character_db_to_dict(char) for char in pagination.items]
    
    return jsonify({
        "characters": characters_list,
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages
    }), 200
