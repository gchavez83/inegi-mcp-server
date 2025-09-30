"""
Configuración y constantes para el servidor MCP del INEGI
"""
import os
from typing import Dict
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Tokens de autenticación del INEGI
INEGI_INDICADORES_TOKEN = os.getenv("INEGI_INDICADORES_TOKEN", "")
INEGI_DENUE_TOKEN = os.getenv("INEGI_DENUE_TOKEN", "")

# Token genérico para compatibilidad hacia atrás
INEGI_TOKEN = os.getenv("INEGI_TOKEN", INEGI_DENUE_TOKEN)  # Por defecto usa el token del DENUE

# URLs base de las APIs
INDICADORES_BASE_URL = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml"
DENUE_BASE_URL = "https://www.inegi.org.mx/app/api/denue/v1/consulta"

# Configuración de la API de Indicadores
class IndicadoresConfig:
    """Configuración para la API de Indicadores"""
    
    # Idiomas disponibles
    IDIOMAS = {
        "es": "Español",
        "en": "English"
    }
    
    # Áreas geográficas
    AREAS_GEO = {
        "00": "Nacional",
        "99": "Por entidad federativa",
        "999": "Por municipio"
    }
    
    # Fuentes de datos
    FUENTES = {
        "BISE": "Banco de Indicadores",
        "BIE": "Banco de Información Económica"
    }
    
    # Versión de la API
    VERSION = "2.0"
    
    # Formatos de salida
    FORMATOS = ["json", "xml", "jsonp"]


# Configuración de la API del DENUE
class DENUEConfig:
    """Configuración para la API del DENUE"""
    
    # Métodos disponibles
    METODOS = {
        "Buscar": "Búsqueda por término, ubicación y radio",
        "Ficha": "Obtener ficha completa de un establecimiento",
        "BuscarEntidad": "Buscar por entidad federativa",
        "BuscarAreaGeo": "Buscar en área geográfica",
        "Nombre": "Buscar por nombre"
    }
    
    # Códigos de entidades federativas
    ENTIDADES = {
        "01": "Aguascalientes",
        "02": "Baja California",
        "03": "Baja California Sur",
        "04": "Campeche",
        "05": "Coahuila",
        "06": "Colima",
        "07": "Chiapas",
        "08": "Chihuahua",
        "09": "Ciudad de México",
        "10": "Durango",
        "11": "Guanajuato",
        "12": "Guerrero",
        "13": "Hidalgo",
        "14": "Jalisco",
        "15": "México",
        "16": "Michoacán",
        "17": "Morelos",
        "18": "Nayarit",
        "19": "Nuevo León",
        "20": "Oaxaca",
        "21": "Puebla",
        "22": "Querétaro",
        "23": "Quintana Roo",
        "24": "San Luis Potosí",
        "25": "Sinaloa",
        "26": "Sonora",
        "27": "Tabasco",
        "28": "Tamaulipas",
        "29": "Tlaxcala",
        "30": "Veracruz",
        "31": "Yucatán",
        "32": "Zacatecas"
    }


# Indicadores comunes (catálogo ampliado)
INDICADORES_COMUNES: Dict[str, str] = {
    # Demográficos
    "1002000001": "Población total",
    "1002000002": "Población femenina",
    "1002000003": "Población masculina",
    "6200240326": "Densidad de población",
    
    # Económicos generales
    "381016": "Producto Interno Bruto (PIB)",
    "381017": "PIB per cápita",
    
    # Empleo
    "444612": "Tasa de desempleo",
    "444603": "Tasa de ocupación",
    "444604": "Población económicamente activa",
    "444605": "Población ocupada",
    "444606": "Población desocupada",
    
    # Precios e inflación
    "216906": "Índice Nacional de Precios al Consumidor (INPC)",
    "216668": "Inflación anual",
    "628194": "Inflación mensual",
    
    # Vivienda
    "6207019887": "Número de viviendas particulares habitadas",
    "6207019888": "Promedio de ocupantes por vivienda",
    
    # Educación  
    "1002000022": "Grado promedio de escolaridad",
    "1002000023": "Porcentaje de población analfabeta",
    
    # Salud
    "6200028214": "Tasa de mortalidad infantil",
    "6200028221": "Esperanza de vida al nacimiento",
    
    # Pobreza y desarrollo
    "628194": "Índice de rezago social",
    "628195": "Índice de marginación",
}

# Categorías de indicadores
CATEGORIAS_INDICADORES = {
    "Demografía": ["1002000001", "1002000002", "1002000003", "6200240326"],
    "Economía": ["381016", "381017"],
    "Empleo": ["444612", "444603", "444604", "444605", "444606"],
    "Precios": ["216906", "216668", "628194"],
    "Vivienda": ["6207019887", "6207019888"],
    "Educación": ["1002000022", "1002000023"],
    "Salud": ["6200028214", "6200028221"],
    "Desarrollo Social": ["628194", "628195"]
}


# Configuración de timeouts
TIMEOUT_SECONDS = 30

# Configuración de reintentos
MAX_RETRIES = 3
