# src/studio/i18n.py
"""Internationalization support for Writer Studio.

Provides translation strings for UI messages in multiple languages.

Usage:
    from src.studio.i18n import t, get_ui_language

    msg = t("no_projects", get_ui_language())
"""

from enum import Enum


class Language(str, Enum):
    """Supported UI languages."""
    EN = "en"
    ZH = "zh"


# Translation strings organized by language
STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # Project management
        "project_management": "Project Management",
        "no_projects": "No projects found",
        "project_created": "Project created successfully",
        "project_switched": "Switched to project",

        # Generation
        "creating_chapter": "Generating chapter...",
        "creating_outline": "Generating outline...",
        "creating_character": "Creating character...",
        "creating_cover": "Generating cover...",
        "creating_plan": "Creating project plan...",
        "collaborating": "Collaborating on content...",
        "illustrating": "Generating illustration...",
        "processing": "Processing...",

        # Time estimates
        "time_chapter": "Estimated 1-2 minutes",
        "time_outline": "Estimated 1-3 minutes",
        "time_character": "Estimated 30-60 seconds",
        "time_cover": "Estimated 30-60 seconds",
        "time_plan": "Estimated 1-2 minutes",
        "time_collaborate": "Estimated 2-3 minutes",
        "time_illustrate": "Estimated 30-60 seconds",

        # Settings
        "settings_updated": "Settings updated",
        "language_changed": "Language changed to",
        "invalid_language": "Invalid language. Use 'en' or 'zh'",

        # Errors
        "error_no_project": "No project selected",
        "error_not_found": "Not found",
        "error_llm_config": "LLM not configured",

        # Status
        "status": "Status",
        "progress": "Progress",
        "words": "words",
        "chapters": "chapters",

        # Help
        "help_available_commands": "Available commands",
        "help_type_help": "Type /help for available commands",
    },
    "zh": {
        # 项目管理
        "project_management": "项目管理",
        "no_projects": "没有找到项目",
        "project_created": "项目创建成功",
        "project_switched": "已切换到项目",

        # 生成
        "creating_chapter": "正在生成章节...",
        "creating_outline": "正在生成大纲...",
        "creating_character": "正在创建角色...",
        "creating_cover": "正在生成封面...",
        "creating_plan": "正在制定项目计划...",
        "collaborating": "正在协作生成内容...",
        "illustrating": "正在生成场景插图...",
        "processing": "正在处理...",

        # 时间估计
        "time_chapter": "预计需要 1-2 分钟",
        "time_outline": "预计需要 1-3 分钟",
        "time_character": "预计需要 30-60 秒",
        "time_cover": "预计需要 30-60 秒",
        "time_plan": "预计需要 1-2 分钟",
        "time_collaborate": "预计需要 2-3 分钟",
        "time_illustrate": "预计需要 30-60 秒",

        # 设置
        "settings_updated": "设置已更新",
        "language_changed": "语言已切换为",
        "invalid_language": "无效的语言。请使用 'en' 或 'zh'",

        # 错误
        "error_no_project": "没有选中的项目",
        "error_not_found": "未找到",
        "error_llm_config": "LLM 未配置",

        # 状态
        "status": "状态",
        "progress": "进度",
        "words": "字",
        "chapters": "章",

        # 帮助
        "help_available_commands": "可用命令",
        "help_type_help": "输入 /help 查看可用命令",
    },
}


def t(key: str, lang: str = "en") -> str:
    """Get translated string for a key.

    Args:
        key: Translation key (e.g., "no_projects")
        lang: Language code ("en" or "zh")

    Returns:
        Translated string, or the key itself if not found
    """
    lang_strings = STRINGS.get(lang, STRINGS.get("en", {}))
    return lang_strings.get(key, key)


def get_ui_language() -> str:
    """Get current UI language from settings.

    Returns:
        Current language code ("en" or "zh")
    """
    try:
        from src.studio.core.settings import get_settings
        return get_settings().ui_language
    except Exception:
        return "en"


def set_ui_language(lang: str) -> bool:
    """Set UI language in settings.

    Args:
        lang: Language code ("en" or "zh")

    Returns:
        True if successful, False if invalid language
    """
    if lang not in ("en", "zh"):
        return False

    try:
        from src.studio.core.settings import get_settings_manager
        manager = get_settings_manager()
        manager.update_settings(ui_language=lang)
        return True
    except Exception:
        return False


def get_available_languages() -> list[str]:
    """Get list of available language codes.

    Returns:
        List of language codes
    """
    return ["en", "zh"]
