"""NovelWriter LSP feature handlers."""

from novelwriter_lsp.features.definition import register_goto_definition
from novelwriter_lsp.features.diagnostics import register_diagnostics
from novelwriter_lsp.features.codelens import register_codelens
from novelwriter_lsp.features.hover import register_hover
from novelwriter_lsp.features.completion import register_completion
from novelwriter_lsp.features.rename import register_rename
from novelwriter_lsp.features.symbols import register_document_symbol

__all__ = [
    "register_goto_definition",
    "register_diagnostics",
    "register_codelens",
    "register_hover",
    "register_completion",
    "register_rename",
    "register_document_symbol",
]
