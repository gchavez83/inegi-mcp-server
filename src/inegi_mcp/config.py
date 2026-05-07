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
INEGI_TOKEN = os.getenv("INEGI_TOKEN", INEGI_DENUE_TOKEN)

# URLs base de las APIs
INDICADORES_BASE_URL = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml"
DENUE_BASE_URL = "https://www.inegi.org.mx/app/api/denue/v1/consulta"

# Configuración de la API de Indicadores
class IndicadoresConfig:
    IDIOMAS = {"es": "Español", "en": "English"}
    AREAS_GEO = {"00": "Nacional", "99": "Por entidad federativa", "999": "Por municipio"}
    FUENTES = {"BISE": "Banco de Indicadores", "BIE": "Banco de Información Económica"}
    VERSION = "2.0"
    FORMATOS = ["json", "xml", "jsonp"]


# Configuración de la API del DENUE
class DENUEConfig:
    METODOS = {
        "Buscar": "Búsqueda por término, ubicación y radio",
        "Ficha": "Obtener ficha completa de un establecimiento",
        "BuscarEntidad": "Buscar por entidad federativa",
        "BuscarAreaGeo": "Buscar en área geográfica",
        "Nombre": "Buscar por nombre"
    }
    ENTIDADES = {
        "01": "Aguascalientes", "02": "Baja California", "03": "Baja California Sur",
        "04": "Campeche", "05": "Coahuila", "06": "Colima", "07": "Chiapas",
        "08": "Chihuahua", "09": "Ciudad de México", "10": "Durango",
        "11": "Guanajuato", "12": "Guerrero", "13": "Hidalgo", "14": "Jalisco",
        "15": "México", "16": "Michoacán", "17": "Morelos", "18": "Nayarit",
        "19": "Nuevo León", "20": "Oaxaca", "21": "Puebla", "22": "Querétaro",
        "23": "Quintana Roo", "24": "San Luis Potosí", "25": "Sinaloa",
        "26": "Sonora", "27": "Tabasco", "28": "Tamaulipas", "29": "Tlaxcala",
        "30": "Veracruz", "31": "Yucatán", "32": "Zacatecas"
    }


# =============================================================================
# INDICADORES COMUNES — catálogo curado con IDs validados en producción
# Actualizado con IDs reales obtenidos del endpoint busquedaBancoIndicadores
# =============================================================================
INDICADORES_COMUNES: Dict[str, str] = {

    # ── DEMOGRAFÍA ──────────────────────────────────────────────────────────────
    "1002000001": "Población total",
    "1002000002": "Población femenina",
    "1002000003": "Población masculina",
    "6200240326": "Densidad de población (hab/km²)",
    "1002000030": "Nacimientos registrados",
    "1002000035": "Defunciones registradas",
    "1002000038": "Matrimonios registrados",
    "1002000039": "Divorcios registrados",
    "6200028214": "Tasa de mortalidad infantil",
    "6200028221": "Esperanza de vida al nacimiento",
    "6200028222": "Esperanza de vida al nacimiento — hombres",
    "6200028223": "Esperanza de vida al nacimiento — mujeres",

    # ── EDUCACIÓN ───────────────────────────────────────────────────────────────
    "1002000022": "Grado promedio de escolaridad",
    "1002000023": "Porcentaje de población analfabeta",
    "6000000004": "Tasa de matriculación educación preescolar",
    "6000000005": "Tasa de matriculación educación primaria",
    "6000000006": "Tasa de matriculación educación secundaria",
    "6000000007": "Tasa de matriculación educación media superior",
    "6000000008": "Tasa de matriculación educación superior",
    "6000000009": "Tasa de abandono escolar preescolar",
    "6000000010": "Tasa de abandono escolar primaria",
    "6000000011": "Tasa de abandono escolar secundaria",

    # ── PIB Y CUENTAS NACIONALES — IDs validados via busquedaBancoIndicadores ──
    "524388":  "PIB a precios básicos (nacional)",
    "527794":  "PIB de la economía nacional a precios de mercado",
    "527799":  "PIB de la economía nacional a precios de mercado (variación)",
    "510104":  "Producto interno bruto — total nacional",
    "510108":  "Producto interno bruto — total nacional (índice)",
    "524277":  "Producto interno neto ajustado ambientalmente (PINAA)",
    "524452":  "Producción a precios de mercado",

    # ── IGAE — Indicador Global de la Actividad Económica ───────────────────────
    "491656":  "IGAE — Variación anual",
    "491659":  "IGAE — Con petróleo",
    "491660":  "IGAE — Sin petróleo",

    # ── PRECIOS AL CONSUMIDOR / INPC ────────────────────────────────────────────
    # Búsqueda con "precios consumidor" o "indice precios"
    "539260":  "Indicadores económicos de coyuntura — Precios al consumidor (1)",
    "539261":  "Indicadores económicos de coyuntura — Precios al consumidor (2)",
    "539262":  "Indicadores económicos de coyuntura — Precios al consumidor (3)",

    # ── EMPLEO ──────────────────────────────────────────────────────────────────
    "444612":  "Tasa de desocupación",
    "444603":  "Tasa de ocupación",
    "444604":  "Población económicamente activa (PEA)",
    "444605":  "Población ocupada",
    "444606":  "Población desocupada",
    "444613":  "Tasa de participación económica",
    "444614":  "Tasa de informalidad laboral",

    # ── COMERCIO EXTERIOR ────────────────────────────────────────────────────────
    "6204198565": "Balanza Comercial de Mercancías de México",
    "6204198569": "Balanza Comercial — Exportaciones",
    "6204198570": "Balanza Comercial — Importaciones",
    "6207095692": "Exportaciones trimestrales por entidad federativa",
    "6207095719": "Exportaciones anuales por entidad federativa",

    # ── ACTIVIDAD ECONÓMICA ESTATAL (ITAEE) ──────────────────────────────────────
    "6207061369": "ITAEE — Actividades económicas por entidad federativa (1)",
    "6207061373": "ITAEE — Actividades económicas por entidad federativa (2)",
    "6207061377": "ITAEE — Actividades económicas por entidad federativa (3)",

    # ── VIVIENDA ─────────────────────────────────────────────────────────────────
    "6207019887": "Número de viviendas particulares habitadas",
    "6207019888": "Promedio de ocupantes por vivienda",
    "6207019889": "Viviendas con acceso a agua entubada (%)",
    "6207019890": "Viviendas con drenaje (%)",
    "6207019891": "Viviendas con electricidad (%)",
    "6207019892": "Viviendas con internet (%)",

    # ── SALUD ────────────────────────────────────────────────────────────────────
    "6200028190": "Tasa de mortalidad por diabetes mellitus",
    "6200028191": "Tasa de mortalidad por enfermedades del corazón",
    "6200028192": "Tasa de mortalidad por tumores malignos",
    "700099":     "Defunciones por homicidio",
    "700100":     "Tasa de homicidios por 100,000 habitantes",

    # ── DESARROLLO SOCIAL ────────────────────────────────────────────────────────
    "628194": "Índice de rezago social",
    "628195": "Índice de marginación",
    "628196": "Grado de marginación",
}


# =============================================================================
# SINÓNIMOS PARA buscar_banco_indicadores
# El endpoint BIE no reconoce ciertos términos comunes en español.
# Este mapa traduce la consulta del usuario al término que sí funciona.
# Validado via diagnostico_bie2.py el 2026-05-06.
# =============================================================================
SINONIMOS_BIE: Dict[str, str] = {
    # Inflación / precios
    "inflacion":            "precios consumidor",
    "inflación":            "precios consumidor",
    "inpc":                 "indice precios",
    "INPC":                 "indice precios",
    "índice de precios":    "indice precios",
    "indice de precios":    "indice precios",
    "precios al consumidor":"precios consumidor",
    "ipc":                  "precios consumidor",
    # PIB / cuentas nacionales
    "producto interno bruto": "PIB",
    "pib nacional":           "PIB",
    "pib estatal":            "producto interno",
    "cuentas nacionales":     "producto interno",
    # Empleo
    "desempleo":              "desocupacion",
    "desocupación":           "ocupacion",
    "desocupacion":           "ocupacion",
    "empleo":                 "ocupacion",
    # Tipo de cambio
    "dolar":                  "tipo de cambio",
    "peso dolar":             "tipo de cambio",
    # Actividad económica estatal
    "pib yucatan":            "actividad economica",
    "pib estatal yucatan":    "actividad economica",
    "itaee":                  "actividad economica",
}


# Categorías de indicadores
CATEGORIAS_INDICADORES = {
    "👥 Demografía":        ["1002000001","1002000002","1002000003","6200240326",
                             "1002000030","1002000035","1002000038","1002000039"],
    "🎓 Educación":         ["1002000022","1002000023","6000000004","6000000005",
                             "6000000006","6000000007","6000000008","6000000009",
                             "6000000010","6000000011"],
    "💰 PIB y Cuentas":     ["524388","527794","527799","510104","510108",
                             "524277","491656","491659","491660"],
    "📈 Precios/INPC":      ["539260","539261","539262"],
    "🏭 Empleo":            ["444612","444603","444604","444605","444606",
                             "444613","444614"],
    "🌎 Comercio Exterior": ["6204198565","6204198569","6204198570",
                             "6207095692","6207095719"],
    "🏠 Vivienda":          ["6207019887","6207019888","6207019889",
                             "6207019890","6207019891","6207019892"],
    "🏥 Salud":             ["6200028214","6200028221","6200028222","6200028223",
                             "6200028190","6200028191","6200028192"],
    "🔒 Seguridad":         ["700099","700100"],
    "📊 Desarrollo Social": ["628194","628195","628196"],
}

# Configuración de timeouts
TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
