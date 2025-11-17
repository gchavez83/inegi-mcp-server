"""
Herramientas MCP para la API del DENUE
"""
from typing import Any, Dict
from mcp.server import Server
from mcp.types import Tool, TextContent
from ..clients.denue_client import DENUEClient
from ..config import DENUEConfig
import json


def register_denue_tools(server: Server, client: DENUEClient):
    """Registra todas las herramientas del DENUE en el servidor MCP"""
    
    @server.call_tool()
    async def buscar_establecimientos(arguments: Dict[str, Any]) -> list[TextContent]:
        """
        Busca establecimientos en el DENUE por término y opcionalmente por ubicación.
        """
        termino = arguments.get("termino")
        latitud = arguments.get("latitud")
        longitud = arguments.get("longitud")
        radio = arguments.get("radio", 250)
        
        if not termino:
            return [TextContent(
                type="text",
                text="Error: Se requiere un término de búsqueda"
            )]
        
        try:
            resultados = await client.buscar_establecimientos(
                termino=termino,
                latitud=latitud,
                longitud=longitud,
                radio=radio
            )
            
            if isinstance(resultados, list) and len(resultados) > 0:
                texto = f"## Establecimientos encontrados: {termino}\n\n"
                texto += f"**Total:** {len(resultados)} establecimientos\n\n"
                
                # Mostrar primeros 10 resultados
                for i, est in enumerate(resultados[:10], 1):
                    texto += f"### {i}. {est.get('Nombre', 'Sin nombre')}\n"
                    texto += f"**ID:** {est.get('Id', 'N/A')}\n"
                    texto += f"**Actividad:** {est.get('Nombre_act', 'N/A')}\n"
                    texto += f"**Dirección:** {est.get('Calle', '')} {est.get('Numero_Exterior', '')}\n"
                    texto += f"**Colonia:** {est.get('Colonia', 'N/A')}\n"
                    texto += f"**Municipio:** {est.get('Municipio', 'N/A')}\n"
                    texto += f"**Estado:** {est.get('Entidad', 'N/A')}\n"
                    
                    if est.get('Telefono'):
                        texto += f"**Teléfono:** {est['Telefono']}\n"
                    if est.get('Correo_e'):
                        texto += f"**Email:** {est['Correo_e']}\n"
                    
                    texto += "\n"
                
                if len(resultados) > 10:
                    texto += f"\n_(Mostrando 10 de {len(resultados)} resultados)_"
                
                return [TextContent(type="text", text=texto)]
            else:
                return [TextContent(
                    type="text",
                    text=f"No se encontraron establecimientos con el término '{termino}'"
                )]
                
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error al buscar establecimientos: {str(e)}"
            )]
    
    @server.call_tool()
    async def obtener_establecimiento(arguments: Dict[str, Any]) -> list[TextContent]:
        """
        Obtiene la ficha completa de un establecimiento específico.
        """
        id_establecimiento = arguments.get("id_establecimiento")
        
        if not id_establecimiento:
            return [TextContent(
                type="text",
                text="Error: Se requiere el ID del establecimiento"
            )]
        
        try:
            ficha = await client.obtener_ficha_establecimiento(id_establecimiento)
            
            if ficha:
                texto = "## Ficha del Establecimiento\n\n"
                texto += f"**Nombre:** {ficha.get('Nombre', 'N/A')}\n"
                texto += f"**ID:** {ficha.get('Id', 'N/A')}\n\n"
                
                texto += "### Actividad\n"
                texto += f"**Clase:** {ficha.get('Nombre_act', 'N/A')}\n\n"
                
                texto += "### Ubicación\n"
                texto += f"**Calle:** {ficha.get('Calle', '')}\n"
                texto += f"**Colonia:** {ficha.get('Colonia', 'N/A')}\n"
                texto += f"**Municipio:** {ficha.get('Municipio', 'N/A')}\n"
                texto += f"**Estado:** {ficha.get('Entidad', 'N/A')}\n\n"
                
                if ficha.get('Telefono'):
                    texto += f"**Teléfono:** {ficha['Telefono']}\n"
                
                return [TextContent(type="text", text=texto)]
            else:
                return [TextContent(
                    type="text",
                    text=f"No se encontró el establecimiento"
                )]
                
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
