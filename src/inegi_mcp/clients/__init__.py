"""
Clientes para las APIs del INEGI
"""
from .indicadores_client import IndicadoresClient
from .denue_client import DENUEClient

__all__ = ["IndicadoresClient", "DENUEClient"]
