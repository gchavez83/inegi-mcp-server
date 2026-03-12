"""
Cliente para la API de Indicadores del INEGI
Versión definitiva — todos los fixes consolidados:
  1. Bug geo: area_geo se pasa directamente ("31"), sin sufijo "000"
  2. Reintento automático BISE → BIE si el primer banco falla
  3. comparar_por_estados: código directo sin sufijos
  4. buscar_por_cl_indicator: URL correcta sin parámetros extra
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
        # No hacer raise aquí — el token puede llegar como env var del proceso
        # cuando Claude Desktop lanza el MCP. Se validará en cada llamada.

    def _construir_url(self, metodo, indicador_id, idioma="es", area_geo="00",
                       ultimo_dato=False, fuente="BISE", formato="json"):
        """Construye la URL para peticiones al endpoint INDICATOR."""
        ultimo = "true" if ultimo_dato else "false"
        return (
            f"{self.base_url}/{metodo}/{indicador_id}/{idioma}/"
            f"{area_geo}/{ultimo}/{fuente}/{self.config.VERSION}/"
            f"{self.token}?type={formato}"
        )

    async def obtener_indicador(self, indicador_id: str, area_geo: str = "00",
                                 codigo_geo: Optional[str] = None,
                                 historica: bool = True, idioma: str = "es") -> Dict[str, Any]:
        """
        Obtiene datos de un indicador. FIX: area_geo directo sin sufijo "000".
        Reintenta automáticamente BISE → BIE si el primer banco falla.
        """
        # FIX geo: determinar código final sin sufijos
        if area_geo in ("99", "999") and codigo_geo:
            geo_final = codigo_geo.zfill(2)
        elif codigo_geo and area_geo == "00":
            geo_final = codigo_geo.zfill(2)
        else:
            geo_final = area_geo  # ya es correcto: "31", "00", "04"

        # Reintento BISE → BIE
        last_error = None
        for fuente in ("BISE", "BIE"):
            url = self._construir_url(
                metodo="INDICATOR", indicador_id=indicador_id,
                idioma=idioma, area_geo=geo_final,
                ultimo_dato=not historica, fuente=fuente
            )
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.json()
                    data["_banco"] = fuente
                    return data
            except httpx.HTTPStatusError as e:
                last_error = e
                continue
        raise last_error

    async def obtener_catalogo(self, tipo_catalogo: str,
                                id_catalogo: Optional[str] = None,
                                idioma: str = "es") -> Dict[str, Any]:
        """Obtiene catálogos de metadatos (CL_UNIT, CL_FREQ, etc.)"""
        id_cat = id_catalogo or "null"
        url = (
            f"{self.base_url}/CL_{tipo_catalogo}/{id_cat}/{idioma}/"
            f"BISE/{self.config.VERSION}/{self.token}?type=json"
        )
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def obtener_metadatos(self, indicador_id: str, idioma: str = "es") -> Dict[str, Any]:
        """Obtiene los metadatos de un indicador."""
        data = await self.obtener_indicador(indicador_id=indicador_id,
                                             area_geo="00", historica=False, idioma=idioma)
        if "Series" in data and len(data["Series"]) > 0:
            serie = data["Series"][0]
            return {k: serie.get(k) for k in
                    ["INDICADOR", "FREQ", "TOPIC", "UNIT", "UNIT_MULT", "NOTE", "SOURCE", "LASTUPDATE", "STATUS"]}
        return {}

    async def comparar_por_estados(self, indicador_id: str, codigos_estados: List[str],
                                    historica: bool = False, idioma: str = "es") -> Dict[str, Any]:
        """
        Obtiene un indicador para múltiples estados.
        FIX: pasa código directo como area_geo, no el comodín "99".
        """
        resultados = {}
        for codigo in codigos_estados:
            try:
                data = await self.obtener_indicador(
                    indicador_id=indicador_id,
                    area_geo=codigo.zfill(2),  # FIX: directo
                    historica=historica, idioma=idioma
                )
                resultados[codigo] = data
            except Exception as e:
                resultados[codigo] = {"error": str(e)}
        return resultados

    async def buscar_por_cl_indicator(self, query: str, banco: str = "BISE",
                                       idioma: str = "es") -> List[Dict[str, Any]]:
        """
        Busca indicadores en el catálogo oficial CL_INDICATOR del INEGI.

        URL correcta (SIN geo ni ultimo_dato — diferente al endpoint INDICATOR):
          /CL_INDICATOR/null/{idioma}/{banco}/{version}/{token}?type=json

        Respuesta: {"CODE": [{"Value": "id", "Description": "nombre"}, ...]}
        El filtrado por query se hace en Python sobre la lista completa.
        """
        url = (
            f"{self.base_url}/CL_INDICATOR/null/{idioma}/"
            f"{banco}/{self.config.VERSION}/{self.token}?type=json"
        )
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        # Manejar estructura: {"CODE": [...]} o lista directa
        codigos = data.get("CODE", [])
        if not codigos and isinstance(data, list):
            codigos = data

        query_lower = query.lower()
        return [
            {"id": item.get("Value", item.get("value", "")),
             "nombre": item.get("Description", item.get("description", "")),
             "banco": banco}
            for item in codigos
            if query_lower in item.get("Description", item.get("description", "")).lower()
        ]

    async def buscar_catalogo_completo(self, busqueda: str, pagina_inicio: int = 0,
                                        pagina_fin: int = 20, area_geo: str = "00",
                                        tematica: str = "", idioma: str = "es") -> Dict[str, Any]:
        """Búsqueda en catálogo completo vía API web del INEGI (requiere cookies de sesión)."""
        session_url = "https://www.inegi.org.mx/app/querybuilder2/default.html"
        search_url  = "https://www.inegi.org.mx/app/api/buscadorcore/v1/busquedaBancoIndicadores/"

        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            await client.get(session_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "es-MX,es;q=0.9",
            })
            payload = {
                "busqueda": busqueda, "busquedaCiencia": "",
                "paginaInicio": pagina_inicio, "paginaFin": pagina_fin,
                "areageo": area_geo, "filtrotema": "null",
                "tematica": tematica if tematica else "6",
                "filtrobusqueda": "CBUSQUEDA", "orderby": "INDICADOR",
                "orderbyAscDesc": "Desc", "metodoBusqueda": 2,
                "IndPrincipales": "null", "idioma": idioma, "herramienta": 405
            }
            response = await client.post(search_url, json=payload, headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/json; charset=UTF-8",
                "Origin": "https://www.inegi.org.mx",
                "Referer": "https://www.inegi.org.mx/app/querybuilder2/default.html",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            })
            response.raise_for_status()
            return response.json()
