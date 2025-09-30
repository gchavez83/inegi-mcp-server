"""
Herramientas MCP para el INEGI
"""
from .indicadores_tools import register_indicadores_tools
from .denue_tools import register_denue_tools

__all__ = ["register_indicadores_tools", "register_denue_tools"]
