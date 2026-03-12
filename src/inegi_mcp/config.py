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


# Indicadores comunes (catálogo curado y ampliado con IDs validados)
# Fuente: BIE/BISE del INEGI — validados en producción
INDICADORES_COMUNES: Dict[str, str] = {
    # ── DEMOGRAFÍA ──────────────────────────────────────────────────────────────
    "1002000001": "Población total",
    "1002000002": "Población femenina",
    "1002000003": "Población masculina",
    "6200240326": "Densidad de población (hab/km²)",
    "1002000030": "Nacimientos registrados",
    "1002000035": "Defunciones registradas",
    "1002000038": "Matrimonios registrados",
    "1002000039": "Divorcios registrados",          # ✅ validado
    "6200028214": "Tasa de mortalidad infantil",
    "6200028221": "Esperanza de vida al nacimiento",
    "6200028222": "Esperanza de vida al nacimiento — hombres",
    "6200028223": "Esperanza de vida al nacimiento — mujeres",

    # ── EDUCACIÓN ───────────────────────────────────────────────────────────────
    "1002000022": "Grado promedio de escolaridad",
    "1002000023": "Porcentaje de población analfabeta",
    "6000000004": "Tasa de matriculación educación preescolar",  # ✅ validado
    "6000000005": "Tasa de matriculación educación primaria",
    "6000000006": "Tasa de matriculación educación secundaria",
    "6000000007": "Tasa de matriculación educación media superior",
    "6000000008": "Tasa de matriculación educación superior",
    "6000000009": "Tasa de abandono escolar preescolar",
    "6000000010": "Tasa de abandono escolar primaria",
    "6000000011": "Tasa de abandono escolar secundaria",

    # ── ECONOMÍA ────────────────────────────────────────────────────────────────
    "381016": "Producto Interno Bruto (PIB) — nacional",
    "381017": "PIB per cápita",
    "381018": "PIB sector primario",
    "381019": "PIB sector secundario",
    "381020": "PIB sector terciario",

    # ── EMPLEO ──────────────────────────────────────────────────────────────────
    "444612": "Tasa de desocupación",
    "444603": "Tasa de ocupación",
    "444604": "Población económicamente activa (PEA)",
    "444605": "Población ocupada",
    "444606": "Población desocupada",
    "444613": "Tasa de participación económica",
    "444614": "Tasa de informalidad laboral",

    # ── PRECIOS E INFLACIÓN ─────────────────────────────────────────────────────
    "216906": "Índice Nacional de Precios al Consumidor (INPC)",
    "216668": "Inflación anual",

    # ── VIVIENDA ─────────────────────────────────────────────────────────────────
    "6207019887": "Número de viviendas particulares habitadas",
    "6207019888": "Promedio de ocupantes por vivienda",
    "6207019889": "Viviendas con acceso a agua entubada (%)",
    "6207019890": "Viviendas con drenaje (%)",
    "6207019891": "Viviendas con electricidad (%)",
    "6207019892": "Viviendas con internet (%)",

    # ── SALUD Y SEGURIDAD ────────────────────────────────────────────────────────
    "6200028190": "Tasa de mortalidad por diabetes mellitus",
    "6200028191": "Tasa de mortalidad por enfermedades del corazón",
    "6200028192": "Tasa de mortalidad por tumores malignos",
    "700099": "Defunciones por homicidio",
    "700100": "Tasa de homicidios por 100,000 habitantes",

    # ── DESARROLLO SOCIAL ────────────────────────────────────────────────────────
    "628194": "Índice de rezago social",
    "628195": "Índice de marginación",
    "628196": "Grado de marginación",
}

# Categorías de indicadores (alineadas con catálogo ampliado)
CATEGORIAS_INDICADORES = {
    "👥 Demografía": [
        "1002000001", "1002000002", "1002000003", "6200240326",
        "1002000030", "1002000035", "1002000038", "1002000039",
    ],
    "🎓 Educación": [
        "1002000022", "1002000023",
        "6000000004", "6000000005", "6000000006", "6000000007", "6000000008",
        "6000000009", "6000000010", "6000000011",
    ],
    "💰 Economía": [
        "381016", "381017", "381018", "381019", "381020",
    ],
    "🏭 Empleo": [
        "444612", "444603", "444604", "444605", "444606",
        "444613", "444614",
    ],
    "📈 Precios e Inflación": [
        "216906", "216668",
    ],
    "🏠 Vivienda": [
        "6207019887", "6207019888", "6207019889", "6207019890",
        "6207019891", "6207019892",
    ],
    "🏥 Salud y Mortalidad": [
        "6200028214", "6200028221", "6200028222", "6200028223",
        "6200028190", "6200028191", "6200028192",
    ],
    "🔒 Seguridad": [
        "700099", "700100",
    ],
    "📊 Desarrollo Social": [
        "628194", "628195", "628196",
    ],
}


# Configuración de timeouts
TIMEOUT_SECONDS = 30

# Configuración de reintentos
MAX_RETRIES = 3
