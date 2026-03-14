"""Sample QA fixtures for testing.

This module provides pre-built sample data files for QA testing scenarios:
- Edge cases for validation
- Known inconsistencies for detection testing
- Valid data samples for baseline testing
"""

from typing import Any

# ============================================================================
# Valid Sample Data (No Issues)
# ============================================================================

VALID_NOVEL_DATA: dict[str, Any] = {
    "novel_id": "valid_novel_001",
    "title": "完美小说",
    "genre": "scifi",
    "total_chapters": 10,
    "characters": [
        {
            "id": "char_valid_001",
            "name": "李明",
            "role": "protagonist",
            "status": "alive",
            "first_appearance": 1,
        },
        {
            "id": "char_valid_002",
            "name": "王芳",
            "role": "supporting",
            "status": "alive",
            "first_appearance": 1,
        },
    ],
    "chapters": [
        {
            "number": 1,
            "title": "第一章 开始",
            "content": "李明和王芳一起开始了他们的冒险。",
            "characters_present": ["char_valid_001", "char_valid_002"],
        },
        {
            "number": 2,
            "title": "第二章 发展",
            "content": "他们遇到了第一个挑战。李明发挥了他的特长。",
            "characters_present": ["char_valid_001", "char_valid_002"],
        },
    ],
}

VALID_CHARACTER_PROFILE: dict[str, Any] = {
    "id": "char_valid_003",
    "name": "张伟",
    "role": "supporting",
    "status": "alive",
    "age": 30,
    "occupation": "工程师",
    "personality": {
        "traits": ["务实", "可靠"],
        "fears": ["失败"],
        "goals": ["成功完成项目"],
    },
    "first_appearance": 3,
    "last_appearance": None,
}

# ============================================================================
# Invalid Sample Data (With Issues)
# ============================================================================

INVALID_NOVEL_DEAD_CHARACTER: dict[str, Any] = {
    "novel_id": "invalid_novel_001",
    "title": "问题小说",
    "genre": "scifi",
    "total_chapters": 20,
    "characters": [
        {
            "id": "char_invalid_001",
            "name": "刘教授",
            "role": "mentor",
            "status": "deceased",
            "death_chapter": 10,
            "death_cause": "疾病",
            "first_appearance": 1,
        },
    ],
    "chapters": [
        {
            "number": 15,
            "title": "第十五章 重逢",
            "content": "刘教授突然出现了，他并没有死。",
            "characters_present": ["char_invalid_001"],
        },
    ],
    # Issue: char_invalid_001 is deceased but appears in chapter 15
}

INVALID_NOVEL_TIMELINE_ISSUE: dict[str, Any] = {
    "novel_id": "invalid_novel_002",
    "title": "时间线混乱",
    "genre": "fantasy",
    "total_chapters": 5,
    "chapters": [
        {
            "number": 1,
            "timeline": {"day": 5, "month": 3, "year": 2024},
        },
        {
            "number": 2,
            "timeline": {"day": 10, "month": 3, "year": 2024},
        },
        {
            "number": 3,
            # Issue: Day 1 comes after Day 10
            "timeline": {"day": 1, "month": 3, "year": 2024},
        },
    ],
}

INVALID_NOVEL_LOCATION_CONFLICT: dict[str, Any] = {
    "novel_id": "invalid_novel_003",
    "title": "地点矛盾",
    "genre": "history",
    "chapters": [
        {
            "number": 1,
            "location": "北京",
            "content": "主角在北京开始了旅程。",
        },
        {
            "number": 2,
            "location": "上海",
            "content": "主角继续在上海工作。",
            # Issue: Same day, different location without travel explanation
            "timeline": {"same_day_as_previous": True},
        },
    ],
}

# ============================================================================
# Edge Cases
# ============================================================================

EDGE_CASE_EMPTY_CHAPTER: dict[str, Any] = {
    "novel_id": "edge_case_001",
    "chapter_number": 5,
    "content": "",
    "title": "",
    # Issue: Empty content
}

EDGE_CASE_SINGLE_CHARACTER_NOVEL: dict[str, Any] = {
    "novel_id": "edge_case_002",
    "title": "独角戏",
    "genre": "general",
    "characters": [
        {
            "id": "char_only",
            "name": "唯一角色",
            "role": "protagonist",
            "status": "alive",
        }
    ],
    "chapters": [
        {
            "number": i,
            "title": f"第{i}章",
            "content": f"唯一角色在第{i}章的独白。",
            "characters_present": ["char_only"],
        }
        for i in range(1, 11)
    ],
}

EDGE_CASE_RAPID_STATUS_CHANGE: dict[str, Any] = {
    "novel_id": "edge_case_003",
    "title": "快速变化",
    "characters": [
        {
            "id": "char_change",
            "name": "变化角色",
            "role": "supporting",
            "status": "alive",
            "status_history": [
                {"chapter": 1, "status": "alive"},
                {"chapter": 2, "status": "deceased"},
                {"chapter": 3, "status": "alive"},  # Issue: Resurrection?
            ],
        }
    ],
}

# ============================================================================
# Complex Test Scenarios
# ============================================================================

SCENARIO_ROMANCE_NOVEL: dict[str, Any] = {
    "novel_id": "scenario_romance_001",
    "title": "浪漫邂逅",
    "genre": "romance",
    "total_chapters": 30,
    "characters": [
        {
            "id": "char_romance_001",
            "name": "林晓",
            "role": "protagonist",
            "gender": "female",
            "status": "alive",
        },
        {
            "id": "char_romance_002",
            "name": "陈昊",
            "role": "protagonist",
            "gender": "male",
            "status": "alive",
        },
        {
            "id": "char_romance_003",
            "name": "前男友",
            "role": "supporting",
            "gender": "male",
            "status": "alive",
        },
    ],
    "plot_structure": {
        "type": "romance_arc",
        "meet_cute": 1,
        "first_kiss": 10,
        "conflict": 15,
        "resolution": 25,
        "happy_ending": 30,
    },
}

SCENARIO_MILITARY_NOVEL: dict[str, Any] = {
    "novel_id": "scenario_military_001",
    "title": "战场英豪",
    "genre": "military",
    "total_chapters": 50,
    "characters": [
        {
            "id": "char_military_001",
            "name": "张指挥官",
            "role": "protagonist",
            "rank": "上校",
            "status": "alive",
        },
        {
            "id": "char_military_002",
            "name": "李狙击手",
            "role": "supporting",
            "rank": "中士",
            "status": "alive",
        },
    ],
    "battles": [
        {"chapter": 5, "name": "首战", "outcome": "victory"},
        {"chapter": 15, "name": "遭遇战", "outcome": "retreat"},
        {"chapter": 30, "name": "决战", "outcome": "victory"},
    ],
}

# ============================================================================
# QA Check Expected Results
# ============================================================================

EXPECTED_QA_RESULTS: dict[str, dict[str, Any]] = {
    "valid_novel_001": {
        "valid": True,
        "issues": [],
        "warnings": [],
        "score": 1.0,
    },
    "invalid_novel_001": {
        "valid": False,
        "issues": [
            {
                "type": "deceased_character_appears",
                "character_id": "char_invalid_001",
                "character_name": "刘教授",
                "death_chapter": 10,
                "appearance_chapter": 15,
                "severity": "error",
            }
        ],
        "warnings": [],
        "score": 0.0,
    },
    "invalid_novel_002": {
        "valid": False,
        "issues": [
            {
                "type": "timeline_inconsistency",
                "chapter": 3,
                "expected_after": "第2章 (10日)",
                "actual": "1日",
                "severity": "error",
            }
        ],
        "warnings": [],
        "score": 0.5,
    },
}

# ============================================================================
# Sample Knowledge Graph Data
# ============================================================================

SAMPLE_KG_DATA: dict[str, Any] = {
    "nodes": [
        {
            "node_id": "kg_sample_char_001",
            "node_type": "character",
            "properties": {
                "name": "示例角色A",
                "status": "alive",
                "role": "protagonist",
            },
        },
        {
            "node_id": "kg_sample_char_002",
            "node_type": "character",
            "properties": {
                "name": "示例角色B",
                "status": "alive",
                "role": "supporting",
            },
        },
        {
            "node_id": "kg_sample_loc_001",
            "node_type": "location",
            "properties": {
                "name": "示例城市",
                "type": "city",
            },
        },
    ],
    "edges": [
        {
            "edge_id": "kg_sample_edge_001",
            "source_id": "kg_sample_char_001",
            "target_id": "kg_sample_char_002",
            "relationship_type": "friend",
            "weight": 0.9,
        },
        {
            "edge_id": "kg_sample_edge_002",
            "source_id": "kg_sample_char_001",
            "target_id": "kg_sample_loc_001",
            "relationship_type": "lives_at",
            "weight": 1.0,
        },
    ],
}

# ============================================================================
# All Fixtures Combined
# ============================================================================

ALL_QA_FIXTURES: dict[str, dict[str, Any]] = {
    "valid": {
        "valid_novel": VALID_NOVEL_DATA,
        "valid_character": VALID_CHARACTER_PROFILE,
    },
    "invalid": {
        "dead_character": INVALID_NOVEL_DEAD_CHARACTER,
        "timeline_issue": INVALID_NOVEL_TIMELINE_ISSUE,
        "location_conflict": INVALID_NOVEL_LOCATION_CONFLICT,
    },
    "edge_cases": {
        "empty_chapter": EDGE_CASE_EMPTY_CHAPTER,
        "single_character": EDGE_CASE_SINGLE_CHARACTER_NOVEL,
        "rapid_status_change": EDGE_CASE_RAPID_STATUS_CHANGE,
    },
    "scenarios": {
        "romance": SCENARIO_ROMANCE_NOVEL,
        "military": SCENARIO_MILITARY_NOVEL,
    },
    "expected_results": EXPECTED_QA_RESULTS,
    "knowledge_graph": SAMPLE_KG_DATA,
}
