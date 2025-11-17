"""
Herramientas MCP para la API de Indicadores del INEGI
"""
from typing import Any, Dict
from mcp.server import Server
from mcp.types import Tool, TextContent
from ..clients.indicadores_client import IndicadoresClient
from ..config import INDICADORES_COMUNES, DENUEConfig
import json


def register_indicadores_tools(server: Server, client: IndicadoresClient):
    """Registra todas las herramientas de Indicadores en el servidor MCP"""
    
    @server.call_tool()
    async def buscar_indicadores(arguments: Dict[str, Any]) -> list[TextContent]:
        """
        Busca indicadores del INEGI por palabra clave.
        Útil para encontrar el ID de indicadores disponibles.
        """
        query = arguments.get("query", "").lower()
        
        if not query:
            return [TextContent(
                type="text",
                text="Error: Se requiere un término de búsqueda"
            )]
        
        # Buscar en el catálogo de indicadores comunes
        resultados = []
        for indicador_id, nombre in INDICADORES_COMUNES.items():
            if query in nombre.lower():
                resultados.append({
                    "id": indicador_id,
                    "nombre": nombre
                })
        
        if resultados:
            texto = "**Indicadores encontrados:**\n\n"
            for res in resultados:
                texto += f"- **{res['nombre']}** (ID: `{res['id']}`)\n"
            texto += f"\n💡 Usa el ID para obtener los datos con `obtener_serie_temporal`"
        else:
            texto = f"No se encontraron indicadores con el término '{query}'.\n\n"
            texto += "**Indicadores disponibles:**\n"
            for indicador_id, nombre in INDICADORES_COMUNES.items():
                texto += f"- {nombre} (ID: `{indicador_id}`)\n"
        
        return [TextContent(type="text", text=texto)]
    
    @server.call_tool()
    async def obtener_serie_temporal(arguments: Dict[str, Any]) -> list[TextContent]:
        """
        Obtiene datos de un indicador económico o demográfico del INEGI.
        Puede obtener datos a nivel nacional, estatal o municipal.
        """
        indicador_id = arguments.get("indicador_id")
        area_geografica = arguments.get("area_geografica", "00")
        codigo_geo = arguments.get("codigo_geo")
        historica = arguments.get("historica", True)
        idioma = arguments.get("idioma", "es")
        
        if not indicador_id:
            return [TextContent(
                type="text",
                text="Error: Se requiere el ID del indicador"
            )]
        
        try:
            data = await client.obtener_indicador(
                indicador_id=indicador_id,
                area_geo=area_geografica,
                codigo_geo=codigo_geo,
                historica=historica,
                idioma=idioma
            )
            
            # Formatear respuesta
            if "Series" in data and len(data["Series"]) > 0:
                serie = data["Series"][0]
                nombre_indicador = INDICADORES_COMUNES.get(indicador_id, f"Indicador {indicador_id}")
                
                texto = f"## {nombre_indicador}\n\n"
                texto += f"**Unidad:** {serie.get('UNIT', 'N/A')}\n"
                texto += f"**Frecuencia:** {serie.get('FREQ', 'N/A')}\n"
                texto += f"**Última actualización:** {serie.get('LASTUPDATE', 'N/A')}\n\n"
                
                if "OBSERVATIONS" in serie:
                    obs = serie["OBSERVATIONS"]
                    texto += f"**Datos ({len(obs)} observaciones):**\n\n"
                    
                    # Mostrar últimas 10 observaciones
                    ultimas = obs[-10:] if len(obs) > 10 else obs
                    for o in ultimas:
                        periodo = o.get("TIME_PERIOD", "N/A")
                        valor = o.get("OBS_VALUE", "N/A")
                        texto += f"- {periodo}: {valor}\n"
                    
                    if len(obs) > 10:
                        texto += f"\n_(Mostrando las últimas 10 de {len(obs)} observaciones)_"
                
                return [TextContent(type="text", text=texto)]
            else:
                return [TextContent(
                    type="text",
                    text=f"No se encontraron datos para el indicador {indicador_id}"
                )]
                
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error al obtener el indicador: {str(e)}"
            )]
    
    @server.call_tool()
    async def comparar_estados(arguments: Dict[str, Any]) -> list[TextContent]:
        """
        Compara un indicador entre diferentes estados de México.
        Útil para análisis regional.
        """
        indicador_id = arguments.get("indicador_id")
        estados = arguments.get("estados", [])
        historica = arguments.get("historica", False)
        
        if not indicador_id:
            return [TextContent(
                type="text",
                text="Error: Se requiere el ID del indicador"
            )]
        
        if not estados or len(estados) == 0:
            return [TextContent(
                type="text",
                text="Error: Se requiere al menos un código de estado"
            )]
        
        try:
            resultados = await client.comparar_por_estados(
                indicador_id=indicador_id,
                codigos_estados=estados,
                historica=historica
            )
            
            nombre_indicador = INDICADORES_COMUNES.get(indicador_id, f"Indicador {indicador_id}")
            texto = f"## Comparación: {nombre_indicador}\n\n"
            
            for codigo, data in resultados.items():
                estado_nombre = DENUEConfig.ENTIDADES.get(codigo.zfill(2), f"Estado {codigo}")
                texto += f"### {estado_nombre}\n"
                
                if "error" in data:
                    texto += f"❌ Error: {data['error']}\n\n"
                elif "Series" in data and len(data["Series"]) > 0:
                    serie = data["Series"][0]
                    if "OBSERVATIONS" in serie and len(serie["OBSERVATIONS"]) > 0:
                        ultima_obs = serie["OBSERVATIONS"][-1]
                        valor = ultima_obs.get("OBS_VALUE", "N/A")
                        periodo = ultima_obs.get("TIME_PERIOD", "N/A")
                        texto += f"**Último dato:** {valor} ({periodo})\n\n"
                    else:
                        texto += "Sin datos disponibles\n\n"
                else:
                    texto += "Sin datos disponibles\n\n"
            
            return [TextContent(type="text", text=texto)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error al comparar estados: {str(e)}"
            )]
    
    @server.call_tool()
    async def obtener_metadatos(arguments: Dict[str, Any]) -> list[TextContent]:
        """
        Obtiene metadatos detallados de un indicador (descripción, fuente, periodicidad, etc.)
        """
        indicador_id = arguments.get("indicador_id")
        idioma = arguments.get("idioma", "es")
        
        if not indicador_id:
            return [TextContent(
                type="text",
                text="Error: Se requiere el ID del indicador"
            )]
        
        try:
            metadatos = await client.obtener_metadatos(
                indicador_id=indicador_id,
                idioma=idioma
            )
            
            if metadatos:
                nombre_indicador = INDICADORES_COMUNES.get(indicador_id, f"Indicador {indicador_id}")
                texto = f"## Metadatos: {nombre_indicador}\n\n"
                texto += f"**ID:** {indicador_id}\n"
                texto += f"**Frecuencia:** {metadatos.get('FREQ', 'N/A')}\n"
                texto += f"**Tema:** {metadatos.get('TOPIC', 'N/A')}\n"
                texto += f"**Unidad:** {metadatos.get('UNIT', 'N/A')}\n"
                texto += f"**Multiplicador:** {metadatos.get('UNIT_MULT', 'N/A')}\n"
                texto += f"**Fuente:** {metadatos.get('SOURCE', 'N/A')}\n"
                texto += f"**Última actualización:** {metadatos.get('LASTUPDATE', 'N/A')}\n"
                texto += f"**Estado:** {metadatos.get('STATUS', 'N/A')}\n"
                
                if metadatos.get('NOTE'):
                    texto += f"\n**Notas:** {metadatos['NOTE']}\n"
                
                return [TextContent(type="text", text=texto)]
            else:
                return [TextContent(
                    type="text",
                    text=f"No se encontraron metadatos para el indicador {indicador_id}"
                )]
                
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error al obtener metadatos: {str(e)}"
            )]
    
    @server.call_tool()
    async def listar_indicadores_disponibles(arguments: Dict[str, Any]) -> list[TextContent]:
        """
        Lista todos los indicadores disponibles en el catálogo básico.
        """
        texto = "## Indicadores Disponibles\n\n"
        texto += "Estos son algunos indicadores comunes. Usa su ID para consultar datos.\n\n"
        
        for indicador_id, nombre in INDICADORES_COMUNES.items():
            texto += f"- **{nombre}**\n"
            texto += f"  - ID: `{indicador_id}`\n\n"
        
        texto += "\n💡 **Tip:** Usa `obtener_serie_temporal` con el ID para obtener los datos."
        
        return [TextContent(type="text", text=texto)]
    
    # Registrar las herramientas con sus definiciones
    server.list_tools_impl = lambda: [
        Tool(
            name="buscar_indicadores",
            description="Busca indicadores del INEGI por palabra clave",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Término de búsqueda (ej: 'población', 'PIB', 'empleo')"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="obtener_serie_temporal",
            description="Obtiene datos históricos o actuales de un indicador específico",
            inputSchema={
                "type": "object",
                "properties": {
                    "indicador_id": {
                        "type": "string",
                        "description": "ID del indicador (ej: '1002000001' para población)"
                    },
                    "area_geografica": {
                        "type": "string",
                        "description": "Área: '00'=nacional, '99'=estatal, '999'=municipal",
                        "default": "00"
                    },
                    "codigo_geo": {
                        "type": "string",
                        "description": "Código de estado/municipio (ej: '31' para Yucatán)"
                    },
                    "historica": {
                        "type": "boolean",
                        "description": "true para serie completa, false para último dato",
                        "default": True
                    },
                    "idioma": {
                        "type": "string",
                        "description": "Idioma: 'es' o 'en'",
                        "default": "es"
                    }
                },
                "required": ["indicador_id"]
            }
        ),
        Tool(
            name="comparar_estados",
            description="Compara un indicador entre diferentes estados de México",
            inputSchema={
                "type": "object",
                "properties": {
                    "indicador_id": {
                        "type": "string",
                        "description": "ID del indicador a comparar"
                    },
                    "estados": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de códigos de estados (ej: ['31', '19', '09'])"
                    },
                    "historica": {
                        "type": "boolean",
                        "description": "true para serie completa, false para último dato",
                        "default": False
                    }
                },
                "required": ["indicador_id", "estados"]
            }
        ),
        Tool(
            name="obtener_metadatos",
            description="Obtiene metadatos detallados de un indicador",
            inputSchema={
                "type": "object",
                "properties": {
                    "indicador_id": {
                        "type": "string",
                        "description": "ID del indicador"
                    },
                    "idioma": {
                        "type": "string",
                        "description": "Idioma: 'es' o 'en'",
                        "default": "es"
                    }
                },
                "required": ["indicador_id"]
            }
        ),
        Tool(
            name="listar_indicadores_disponibles",
            description="Lista todos los indicadores disponibles en el catálogo",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]
