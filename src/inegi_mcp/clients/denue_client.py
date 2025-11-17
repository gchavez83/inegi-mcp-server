"""
Cliente para la API del DENUE (Directorio Nacional de Unidades Económicas)
"""
import httpx
from typing import Dict, List, Optional, Any
from ..config import (
    DENUE_BASE_URL,
    INEGI_DENUE_TOKEN,
    DENUEConfig,
    TIMEOUT_SECONDS
)


class DENUEClient:
    """Cliente para interactuar con la API del DENUE"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or INEGI_DENUE_TOKEN
        self.base_url = DENUE_BASE_URL
        self.config = DENUEConfig()
        
        if not self.token:
            raise ValueError("Se requiere un token del INEGI para DENUE. Configura INEGI_DENUE_TOKEN en las variables de entorno.")
    
    async def buscar_establecimientos(
        self,
        termino: str,
        latitud: Optional[float] = None,
        longitud: Optional[float] = None,
        radio: int = 250
    ) -> Dict[str, Any]:
        """
        Busca establecimientos por término y ubicación
        
        Args:
            termino: Palabra(s) a buscar (nombre, actividad, ubicación)
            latitud: Latitud del centro de búsqueda (opcional)
            longitud: Longitud del centro de búsqueda (opcional)
            radio: Radio de búsqueda en metros (default: 250)
        
        Returns:
            Diccionario con los establecimientos encontrados
        """
        if latitud and longitud:
            url = f"{self.base_url}/Buscar/{termino}/{latitud},{longitud}/{radio}/{self.token}"
        else:
            url = f"{self.base_url}/Buscar/{termino}/{self.token}"
        
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    async def buscar_en_municipio(
        self,
        termino: str,
        latitud: float,
        longitud: float,
        radio: int = 50000  # 50km por defecto para cubrir un municipio
    ) -> Dict[str, Any]:
        """
        Busca todos los establecimientos en un municipio usando coordenadas centrales
        
        Args:
            termino: Término de búsqueda (usa "todos" para obtener todos)
            latitud: Latitud del centro del municipio
            longitud: Longitud del centro del municipio
            radio: Radio de búsqueda en metros
        
        Returns:
            Diccionario con los establecimientos encontrados
        """
        url = f"{self.base_url}/Buscar/{termino}/{latitud},{longitud}/{radio}/{self.token}"
        
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    async def obtener_ficha_establecimiento(
        self,
        id_establecimiento: str
    ) -> Dict[str, Any]:
        """
        Obtiene la ficha completa de un establecimiento
        
        Args:
            id_establecimiento: ID del establecimiento
        
        Returns:
            Diccionario con los detalles del establecimiento
        """
        url = f"{self.base_url}/Ficha/{id_establecimiento}/{self.token}"
        
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    async def buscar_por_entidad(
        self,
        termino: str,
        codigo_entidad: str
    ) -> Dict[str, Any]:
        """
        Busca establecimientos en una entidad federativa específica
        
        Args:
            termino: Palabra(s) a buscar
            codigo_entidad: Código de la entidad (ej: "31" para Yucatán)
        
        Returns:
            Diccionario con los establecimientos encontrados
        """
        url = f"{self.base_url}/BuscarEntidad/{termino}/{codigo_entidad}/{self.token}"
        
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    async def buscar_por_area(
        self,
        latitud: float,
        longitud: float,
        radio: int = 250
    ) -> Dict[str, Any]:
        """
        Busca todos los establecimientos en un área geográfica
        
        Args:
            latitud: Latitud del centro
            longitud: Longitud del centro
            radio: Radio de búsqueda en metros
        
        Returns:
            Diccionario con los establecimientos en el área
        """
        url = f"{self.base_url}/BuscarAreaGeo/{latitud},{longitud}/{radio}/{self.token}"
        
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    async def buscar_por_nombre(
        self,
        nombre: str
    ) -> Dict[str, Any]:
        """
        Busca establecimientos por coincidencia en el nombre
        
        Args:
            nombre: Nombre o parte del nombre del establecimiento
        
        Returns:
            Diccionario con los establecimientos encontrados
        """
        url = f"{self.base_url}/Nombre/{nombre}/{self.token}"
        
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    async def buscar_area_act(
        self,
        entidad: str = "0",
        municipio: str = "0",
        localidad: str = "0",
        ageb: str = "0",
        manzana: str = "0",
        sector: str = "0",
        subsector: str = "0",
        rama: str = "0",
        clase: str = "0",
        nombre: str = "0",
        registro_inicial: int = 1,
        registro_final: int = 10,
        id_establecimiento: str = "0"
    ) -> Dict[str, Any]:
        """
        Busca establecimientos con opción de filtrar por área geográfica y actividad económica.
        Incluye campos adicionales como AGEB, Manzana y clasificación económica detallada.
        
        Args:
            entidad: Código de entidad federativa (00=todas, ej: "31" para Yucatán)
            municipio: Código de municipio (0=todos, ej: "001")
            localidad: Código de localidad (0=todas, ej: "0001")
            ageb: Código AGEB (0=todas, ej: "2000")
            manzana: Código de manzana (0=todas, ej: "043")
            sector: Código de sector económico (0=todos, ej: "46")
            subsector: Código de subsector (0=todos, ej: "464")
            rama: Código de rama (0=todas, ej: "4641")
            clase: Código de clase (0=todas, ej: "464112")
            nombre: Nombre del establecimiento (0=todos)
            registro_inicial: Número de registro inicial (default: 1)
            registro_final: Número de registro final (default: 10, máx: 1000)
            id_establecimiento: ID específico del establecimiento (0=todos)
        
        Returns:
            Lista de establecimientos con campos extendidos incluyendo:
            - AGEB, Manzana, Edificio
            - Clasificación económica completa (sector, subsector, rama)
            - Coordenadas, dirección completa
            
        Nota: Este método devuelve más campos que buscar_establecimientos(),
        incluyendo AGEB y Manzana que son útiles para análisis geográfico detallado.
        """
        # Construir URL según la documentación del INEGI
        url = (
            f"{self.base_url}/BuscarAreaAct/"
            f"{entidad}/{municipio}/{localidad}/{ageb}/{manzana}/"
            f"{sector}/{subsector}/{rama}/{clase}/"
            f"{nombre}/"
            f"{registro_inicial}/{registro_final}/"
            f"{id_establecimiento}/"
            f"{self.token}"
        )
        
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    async def cuantificar(
        self,
        actividad_economica: str = "0",
        area_geografica: str = "0",
        estrato: str = "0"
    ) -> Dict[str, Any]:
        """
        Realiza un conteo de establecimientos por área geográfica, actividad económica y estrato.
        
        Args:
            actividad_economica: Clave de actividad económica (0=todas)
                - 2 dígitos: sector (ej: "46")
                - 3 dígitos: subsector (ej: "464")
                - 4 dígitos: rama (ej: "4641")
                - 5 dígitos: subrama (ej: "46411")
                - 6 dígitos: clase (ej: "464111")
                - Múltiples separadas por coma (ej: "111,112")
            area_geografica: Clave de área geográfica (0=todo el país)
                - 2 dígitos: estatal (ej: "31")
                - 5 dígitos: municipal (ej: "31050")
                - 9 dígitos: localidad (ej: "310500001")
                - Múltiples separadas por coma (ej: "01001,01005")
            estrato: Clave de estrato por personal ocupado (0=todos)
                - 1: 0 a 5 personas
                - 2: 6 a 10 personas
                - 3: 11 a 30 personas
                - 4: 31 a 50 personas
                - 5: 51 a 100 personas
                - 6: 101 a 250 personas
                - 7: 251 y más personas
        
        Returns:
            Lista con conteos por actividad económica y área geográfica
            Cada elemento tiene: AE (actividad), AG (área geográfica), Total
        """
        url = f"{self.base_url}/Cuantificar/{actividad_economica}/{area_geografica}/{estrato}/{self.token}"
        
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    async def obtener_estadisticas(
        self,
        termino: str,
        codigo_entidad: Optional[str] = None,
        latitud: Optional[float] = None,
        longitud: Optional[float] = None,
        radio: int = 50000
    ) -> Dict[str, Any]:
        """
        Genera estadísticas básicas de establecimientos
        
        Args:
            termino: Término de búsqueda o actividad
            codigo_entidad: Código de entidad (opcional)
            latitud: Latitud para búsqueda por área
            longitud: Longitud para búsqueda por área
            radio: Radio de búsqueda en metros
        
        Returns:
            Diccionario con estadísticas
        """
        if latitud and longitud:
            resultados = await self.buscar_en_municipio(termino, latitud, longitud, radio)
        elif codigo_entidad:
            resultados = await self.buscar_por_entidad(termino, codigo_entidad)
        else:
            resultados = await self.buscar_establecimientos(termino)
        
        # Extraer estadísticas básicas
        if isinstance(resultados, list):
            total = len(resultados)
            
            # Contar por tipo de actividad si está disponible
            actividades = {}
            for est in resultados:
                actividad = est.get("Nombre_act", "No especificada")
                actividades[actividad] = actividades.get(actividad, 0) + 1
            
            return {
                "total_establecimientos": total,
                "distribucion_actividades": actividades,
                "muestra": resultados[:5] if total > 5 else resultados
            }
        
        return {"error": "No se pudieron obtener estadísticas", "respuesta": resultados}
