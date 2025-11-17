"""
Cliente para la API de Indicadores del INEGI
"""
import httpx
from typing import Dict, List, Optional, Any
from ..config import (
    INDICADORES_BASE_URL,
    INEGI_INDICADORES_TOKEN,
    IndicadoresConfig,
    TIMEOUT_SECONDS
)


class IndicadoresClient:
    """Cliente para interactuar con la API de Indicadores del INEGI"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or INEGI_INDICADORES_TOKEN
        self.base_url = INDICADORES_BASE_URL
        self.config = IndicadoresConfig()
        
        if not self.token:
            raise ValueError("Se requiere un token del INEGI para indicadores. Configura INEGI_INDICADORES_TOKEN en las variables de entorno.")
    
    def _construir_url(
        self,
        metodo: str,
        indicador_id: str,
        idioma: str = "es",
        area_geo: str = "00",
        ultimo_dato: bool = False,
        fuente: str = "BISE",
        formato: str = "json"
    ) -> str:
        """Construye la URL para la petición a la API"""
        ultimo = "true" if ultimo_dato else "false"
        url = (
            f"{self.base_url}/{metodo}/{indicador_id}/{idioma}/"
            f"{area_geo}/{ultimo}/{fuente}/{self.config.VERSION}/"
            f"{self.token}?type={formato}"
        )
        return url
    
    async def obtener_indicador(
        self,
        indicador_id: str,
        area_geo: str = "00",
        codigo_geo: Optional[str] = None,
        historica: bool = True,
        idioma: str = "es"
    ) -> Dict[str, Any]:
        """
        Obtiene los datos de un indicador específico
        
        Args:
            indicador_id: ID del indicador (ej: "1002000001")
            area_geo: Área geográfica ("00"=nacional, "99"=estatal, "999"=municipal)
            codigo_geo: Código específico de estado/municipio (ej: "31" para Yucatán)
            historica: True para serie completa, False para último dato
            idioma: "es" o "en"
        
        Returns:
            Diccionario con los datos del indicador
        """
        # Si se proporciona código geográfico, ajustar el formato
        if codigo_geo:
            if area_geo == "99":  # Estado
                area_geo = codigo_geo.zfill(2) + "000"
            elif area_geo == "999":  # Municipio
                area_geo = codigo_geo.zfill(5)
        
        url = self._construir_url(
            metodo="INDICATOR",
            indicador_id=indicador_id,
            idioma=idioma,
            area_geo=area_geo,
            ultimo_dato=not historica,
            fuente="BISE"
        )
        
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    async def obtener_catalogo(
        self,
        tipo_catalogo: str,
        id_catalogo: Optional[str] = None,
        idioma: str = "es"
    ) -> Dict[str, Any]:
        """
        Obtiene catálogos de metadatos
        
        Args:
            tipo_catalogo: Tipo de catálogo (ej: "CL_UNIT", "CL_FREQ")
            id_catalogo: ID específico o None para todos
            idioma: "es" o "en"
        
        Returns:
            Diccionario con el catálogo
        """
        id_cat = id_catalogo or "null"
        url = (
            f"{self.base_url}/CL_{tipo_catalogo}/{id_cat}/{idioma}/"
            f"BISE/{self.config.VERSION}/{self.token}?type=json"
        )
        
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    async def obtener_metadatos(
        self,
        indicador_id: str,
        idioma: str = "es"
    ) -> Dict[str, Any]:
        """
        Obtiene los metadatos de un indicador
        
        Args:
            indicador_id: ID del indicador
            idioma: "es" o "en"
        
        Returns:
            Diccionario con los metadatos
        """
        # Los metadatos vienen en la misma respuesta del indicador
        data = await self.obtener_indicador(
            indicador_id=indicador_id,
            area_geo="00",
            historica=False,
            idioma=idioma
        )
        
        # Extraer solo los metadatos relevantes
        if "Series" in data and len(data["Series"]) > 0:
            serie = data["Series"][0]
            return {
                "INDICADOR_ID": serie.get("INDICADOR"),
                "FREQ": serie.get("FREQ"),
                "TOPIC": serie.get("TOPIC"),
                "UNIT": serie.get("UNIT"),
                "UNIT_MULT": serie.get("UNIT_MULT"),
                "NOTE": serie.get("NOTE"),
                "SOURCE": serie.get("SOURCE"),
                "LASTUPDATE": serie.get("LASTUPDATE"),
                "STATUS": serie.get("STATUS")
            }
        
        return {}
    
    async def comparar_por_estados(
        self,
        indicador_id: str,
        codigos_estados: List[str],
        historica: bool = False,
        idioma: str = "es"
    ) -> Dict[str, Any]:
        """
        Obtiene un indicador para múltiples estados
        
        Args:
            indicador_id: ID del indicador
            codigos_estados: Lista de códigos de estados (ej: ["31", "19", "09"])
            historica: True para serie completa
            idioma: "es" o "en"
        
        Returns:
            Diccionario con datos por estado
        """
        resultados = {}
        
        for codigo in codigos_estados:
            try:
                data = await self.obtener_indicador(
                    indicador_id=indicador_id,
                    area_geo="99",
                    codigo_geo=codigo,
                    historica=historica,
                    idioma=idioma
                )
                resultados[codigo] = data
            except Exception as e:
                resultados[codigo] = {"error": str(e)}
        
        return resultados
    
    async def buscar_catalogo_completo(
        self,
        busqueda: str,
        pagina_inicio: int = 0,
        pagina_fin: int = 20,
        area_geo: str = "00",
        tematica: str = "",
        idioma: str = "es"
    ) -> Dict[str, Any]:
        """
        Busca indicadores en el catálogo completo del INEGI usando la API oficial de búsqueda
        
        Args:
            busqueda: Término de búsqueda (ej: "población", "PIB", "delitos")
            pagina_inicio: Página inicial para paginación (default: 0)
            pagina_fin: Página final/límite de resultados (default: 20)
            area_geo: Área geográfica ("00"=nacional, código específico para otros)
            tematica: Código de temática específica (opcional)
            idioma: "es" o "en"
        
        Returns:
            Diccionario con los resultados de la búsqueda
        """
        # Primera petición para obtener cookies de sesión
        session_url = "https://www.inegi.org.mx/app/querybuilder2/default.html"
        search_url = "https://www.inegi.org.mx/app/api/buscadorcore/v1/busquedaBancoIndicadores/"
        
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            # Paso 1: Obtener cookies de sesión
            session_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en,es;q=0.9,es-MX;q=0.8,es-419;q=0.7,en-US;q=0.6",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            # Obtener la página principal para establecer sesión
            session_response = await client.get(session_url, headers=session_headers)
            
            # Paso 2: Hacer la búsqueda con las cookies obtenidas
            # Payload corregido basado en tu captura
            payload = {
                "busqueda": busqueda,
                "busquedaCiencia": "",
                "paginaInicio": pagina_inicio,
                "paginaFin": pagina_fin,
                "areageo": area_geo,  # Cambiado de areaGeo a areageo
                "filtrotema": "null",
                "tematica": tematica if tematica else "6",  # Usar "6" como default
                "filtrobusqueda": "CBUSQUEDA",
                "orderby": "INDICADOR",  # Cambiado de RANKING a INDICADOR
                "orderbyAscDesc": "Desc",
                "metodoBusqueda": 2,  # Cambiado de 1 a 2
                "IndPrincipales": "null",  # Cambiado de indPrincipales
                "idioma": idioma,
                "herramienta": 405  # Cambiado de herramientas
            }
            
            # Headers corregidos basados en tu captura
            search_headers = {
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en,es;q=0.9,es-MX;q=0.8,es-419;q=0.7,en-US;q=0.6,gl;q=0.5",
                "Connection": "keep-alive",
                "Content-Type": "application/json; charset=UTF-8",
                "Origin": "https://www.inegi.org.mx",
                "Referer": "https://www.inegi.org.mx/app/querybuilder2/default.html",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"'
            }
            
            # Realizar la búsqueda usando las cookies de la sesión
            response = await client.post(search_url, json=payload, headers=search_headers)
            response.raise_for_status()
            return response.json()
