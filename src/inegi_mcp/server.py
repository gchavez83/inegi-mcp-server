"""
Servidor MCP principal para las APIs del INEGI usando FastMCP
"""
import os
import re
import httpx
from mcp.server.fastmcp import FastMCP
from .clients import IndicadoresClient, DENUEClient
from .clients.indicadores_client import IndicadorNoDisponible
from .config import INDICADORES_COMUNES, DENUEConfig
from typing import Optional, List, Dict, Any, Tuple

# Crear el servidor FastMCP
mcp = FastMCP("inegi-mcp")

# Inicializar clientes
indicadores_client = IndicadoresClient()
denue_client = DENUEClient()


# ============================================================================
# UTILIDADES DE SERIES
# ============================================================================
# La API de INEGI entrega las observaciones de la más reciente a la más antigua.
# Todo recorte "últimas N" debe ordenar primero; de lo contrario se descartan
# justamente los datos nuevos (bug corregido en septiembre 2026).

_LIMITE_DEFAULT = 80


def _clave_periodo(periodo: str) -> Tuple[int, int]:
    """
    Convierte un TIME_PERIOD de INEGI en (año, subperiodo) ordenable.
    Formatos vistos: '2025/12' (mes), '2023/01' (trimestre 1), '2021' (año),
    '2025' en catálogos como '2025012' (año+mes sin separador) o '20253' (año+trimestre).
    """
    if periodo is None:
        return (0, 0)
    p = str(periodo).strip()
    m = re.match(r"^(\d{4})\D+(\d{1,2})$", p)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    m = re.match(r"^(\d{4})(\d{1,3})$", p)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    m = re.match(r"^(\d{4})$", p)
    if m:
        return (int(m.group(1)), 0)
    return (0, 0)


def _ordenar_obs(obs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Orden cronológico ascendente por TIME_PERIOD."""
    return sorted(obs, key=lambda o: _clave_periodo(o.get("TIME_PERIOD")))


def _filtrar_periodo(obs: List[Dict[str, Any]], desde: Optional[str], hasta: Optional[str]):
    """
    Filtra por periodo. 'desde'/'hasta' aceptan '2018', '2018/01' o '2018-01'.
    Un año solo se interpreta como inicio de año (desde) o fin de año (hasta).
    """
    def limite(v: Optional[str], es_fin: bool):
        if not v:
            return None
        k = _clave_periodo(str(v).replace("-", "/"))
        if k == (0, 0):
            return None
        if k[1] == 0:
            return (k[0], 99 if es_fin else 0)
        return k

    lo = limite(desde, False)
    hi = limite(hasta, True)
    out = obs
    if lo:
        out = [o for o in out if _clave_periodo(o.get("TIME_PERIOD")) >= lo]
    if hi:
        out = [o for o in out if _clave_periodo(o.get("TIME_PERIOD")) <= hi]
    return out


def _fmt_valor(valor: Any) -> str:
    try:
        return f"{float(valor):,.4f}".rstrip("0").rstrip(".")
    except (ValueError, TypeError):
        return str(valor) if valor not in (None, "") else "N/D"


def _aviso_base_cerrada(unidad_desc: str, ultimo_periodo: str) -> str:
    """
    Marca series con base de referencia antigua (2008, 2013) cuyo último periodo es
    anterior a 2024: INEGI las dejó de actualizar al cambiar de año base y existe
    una versión base 2018 con otro ID.
    """
    anio = _clave_periodo(ultimo_periodo)[0]
    base_vieja = re.search(r"\b(2003|2008|2013)\b", unidad_desc or "")
    if base_vieja and anio and anio < 2024:
        return (f"\n> ⚠️ Serie con base {base_vieja.group(1)} y último dato en {ultimo_periodo}. "
                f"INEGI ya no la actualiza; busca la versión base 2018 del mismo indicador (ID distinto).")
    return ""


async def _describir_serie(serie: Dict[str, Any]) -> Tuple[str, str]:
    """Devuelve (unidad legible, frecuencia legible) a partir de los códigos UNIT/FREQ."""
    unidad = await indicadores_client.describir_codigo("UNIT", serie.get("UNIT"))
    frecuencia = await indicadores_client.describir_codigo("FREQ", serie.get("FREQ"))
    return unidad, frecuencia


def _render_observaciones(obs: List[Dict[str, Any]], limite: int, desde: Optional[str],
                          hasta: Optional[str], tabla: bool = False) -> str:
    """Ordena, filtra y recorta a las últimas `limite` observaciones; indica el rango real."""
    total = len(obs)
    ordenadas = _filtrar_periodo(_ordenar_obs(obs), desde, hasta)
    filtradas = len(ordenadas)
    recorte = ordenadas[-limite:] if limite and len(ordenadas) > limite else ordenadas

    if not recorte:
        return "\n_Sin observaciones en el rango solicitado._\n"

    rango_total = f"{ordenadas[0].get('TIME_PERIOD')} → {ordenadas[-1].get('TIME_PERIOD')}"
    partes = [f"**Observaciones:** {total} publicadas"]
    if desde or hasta:
        partes.append(f"{filtradas} en el rango pedido")
    partes.append(f"mostrando {len(recorte)} ({recorte[0].get('TIME_PERIOD')} → {recorte[-1].get('TIME_PERIOD')})")
    texto = f"**Periodo disponible:** {rango_total}\n" + " · ".join(partes) + "\n\n"

    if tabla:
        texto += "| Período | Valor |\n|---------|-------|\n"
        for o in recorte:
            texto += f"| {o.get('TIME_PERIOD', 'N/A')} | {_fmt_valor(o.get('OBS_VALUE'))} |\n"
    else:
        for o in recorte:
            texto += f"- {o.get('TIME_PERIOD', 'N/A')}: {_fmt_valor(o.get('OBS_VALUE'))}\n"

    if len(ordenadas) > len(recorte):
        texto += (f"\n_Se omitieron {len(ordenadas) - len(recorte)} observaciones anteriores. "
                  f"Usa `desde`/`hasta` o sube `limite` para verlas._")
    return texto


# ============================================================================
# HERRAMIENTAS DE INDICADORES
# ============================================================================

@mcp.tool()
async def buscar_indicadores(query: str) -> str:
    """
    Busca indicadores del INEGI por palabra clave.

    Estrategia de 3 niveles (rápido → completo):
    1. Catálogo local curado (~50 indicadores validados con sus IDs).
    2. CL_INDICATOR BISE — catálogo oficial de indicadores sociodemográficos.
    3. CL_INDICATOR BIE  — catálogo oficial de indicadores económicos.

    Siempre devuelve el ID listo para usar en obtener_serie_temporal.

    Args:
        query: Término en español (ej: 'divorcios', 'fecundidad', 'pobreza', 'homicidios')
    """
    query_lower = query.lower()

    resultados_locales = [
        (iid, nombre)
        for iid, nombre in INDICADORES_COMUNES.items()
        if query_lower in nombre.lower()
    ]
    if resultados_locales:
        texto = "## Indicadores para '{}' (catálogo local)\n\n".format(query)
        for iid, nombre in resultados_locales:
            texto += "- **{}**  ->  ID: `{}`\n".format(nombre, iid)
        texto += "\n💡 Usa el ID en `obtener_serie_temporal`."
        return texto

    resultados_api = []
    errores = []

    for banco in ("BISE", "BIE"):
        try:
            res = await indicadores_client.buscar_por_cl_indicator(query=query, banco=banco)
            resultados_api.extend(res)
        except Exception as e:
            errores.append("{}: {}".format(banco, str(e)[:60]))

    if resultados_api:
        texto = "## Indicadores para '{}' (catálogo INEGI)\n\n".format(query)
        texto += "Se encontraron **{}** coincidencias:\n\n".format(len(resultados_api))
        for r in resultados_api[:30]:
            texto += "- **{}** [{}]  ->  ID: `{}`\n".format(r["nombre"], r["banco"], r["id"])
        if len(resultados_api) > 30:
            texto += "\n_...y {} más. Usa `buscar_catalogo_cl` con más detalle._\n".format(len(resultados_api) - 30)
        texto += "\n💡 Copia el ID y úsalo en `obtener_serie_temporal`."
        return texto

    texto = "No se encontraron indicadores para '{}'.\n\n".format(query)
    if errores:
        texto += "_(Errores en API: {})_\n\n".format(", ".join(errores))
    texto += "**Sugerencias:**\n"
    texto += "- Prueba sinónimos (ej: 'nupcialidad' en lugar de 'matrimonios')\n"
    texto += "- Usa `buscar_catalogo_cl` para búsqueda avanzada por banco\n"
    texto += "- Consulta https://www.inegi.org.mx/app/indicadores/ y copia el ID\n"
    return texto


@mcp.tool()
async def obtener_serie_temporal(
    indicador_id: str,
    area_geografica: str = "00",
    codigo_geo: Optional[str] = None,
    historica: bool = True,
    idioma: str = "es",
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    limite: int = _LIMITE_DEFAULT,
) -> str:
    """
    Obtiene datos de un indicador económico o demográfico del INEGI.

    Las observaciones se devuelven en orden cronológico y, si hay más de `limite`,
    se muestran las MÁS RECIENTES. Usa `desde`/`hasta` para pedir un tramo concreto.

    Args:
        indicador_id: ID del indicador (ej: '1002000001' para población)
        area_geografica: Área: '00'=nacional, '99'=estatal, '999'=municipal
        codigo_geo: Código de estado/municipio (ej: '31' para Yucatán)
        historica: true para serie completa, false para último dato
        idioma: Idioma: 'es' o 'en'
        desde: Periodo inicial, ej. '2018' o '2018/01' (opcional)
        hasta: Periodo final, ej. '2025' o '2025/12' (opcional)
        limite: Máximo de observaciones a mostrar (default 80; 0 = sin límite)
    """
    try:
        data = await indicadores_client.obtener_indicador(
            indicador_id=indicador_id, area_geo=area_geografica,
            codigo_geo=codigo_geo, historica=historica, idioma=idioma
        )
    except IndicadorNoDisponible as e:
        return f"No se encontraron datos para el indicador {indicador_id}.\n\n{e}"
    except Exception as e:
        return f"Error al obtener el indicador: {str(e)}"

    serie = data["Series"][0]
    nombre_indicador = INDICADORES_COMUNES.get(indicador_id, f"Indicador {indicador_id}")
    unidad, frecuencia = await _describir_serie(serie)
    geo = data.get("_geo", area_geografica)
    geo_desc = "Nacional" if geo == "00" else DENUEConfig.ENTIDADES.get(str(geo).zfill(2), f"Área {geo}")

    texto = f"## {nombre_indicador}\n\n"
    texto += f"**ID:** `{indicador_id}` · **Banco:** {data.get('_banco', 'N/D')} · **Ámbito:** {geo_desc}\n"
    texto += f"**Unidad:** {unidad}\n"
    texto += f"**Frecuencia:** {frecuencia}\n"
    texto += f"**Última actualización INEGI:** {serie.get('LASTUPDATE', 'N/A')}\n"

    obs = serie.get("OBSERVATIONS", []) or []
    if not obs:
        return texto + "\n_La serie no trae observaciones._"

    ultimo = _ordenar_obs(obs)[-1].get("TIME_PERIOD", "")
    texto += _aviso_base_cerrada(unidad, ultimo)
    texto += "\n" + _render_observaciones(obs, limite, desde, hasta)
    return texto


@mcp.tool()
async def buscar_catalogo_cl(query: str, banco: str = "BISE", limite: int = 30) -> str:
    """
    Búsqueda directa en el catálogo oficial CL_INDICATOR del INEGI.

    Args:
        query: Término de búsqueda (ej: 'fecundidad', 'exportaciones', 'pobreza')
        banco: "BISE" = indicadores sociodemográficos | "BIE" = indicadores económicos
        limite: Máximo de resultados a mostrar (default: 30, máx recomendado: 100)
    """
    try:
        resultados = await indicadores_client.buscar_por_cl_indicator(query=query, banco=banco)

        if not resultados:
            otro_banco = "BIE" if banco == "BISE" else "BISE"
            resultados_alt = await indicadores_client.buscar_por_cl_indicator(query=query, banco=otro_banco)
            if resultados_alt:
                texto = "No se encontró en **{}**, pero hay {} resultados en **{}**:\n\n".format(
                    banco, len(resultados_alt), otro_banco)
                banco = otro_banco
                resultados = resultados_alt
            else:
                return "No se encontraron indicadores para '{}' en ningún banco.".format(query)
        else:
            texto = ""

        total = len(resultados)
        texto += "## Catálogo CL_INDICATOR — '{}' en {}\n\n".format(query, banco)
        texto += "**Total:** {}  |  **Mostrando:** {}\n\n".format(total, min(total, limite))
        for r in resultados[:limite]:
            texto += "- **{}**  ->  `{}`\n".format(r["nombre"], r["id"])
        if total > limite:
            texto += "\n_...y {} más._\n".format(total - limite)
        texto += "\n💡 Usa el ID en `obtener_serie_temporal`."
        return texto

    except Exception as e:
        return "Error al consultar CL_INDICATOR: {}".format(str(e))


@mcp.tool()
async def listar_indicadores_disponibles() -> str:
    """Lista todos los indicadores disponibles en el catálogo básico."""
    texto = "## Indicadores Disponibles\n\n"
    for indicador_id, nombre in INDICADORES_COMUNES.items():
        texto += f"- **{nombre}**\n  - ID: `{indicador_id}`\n\n"
    texto += "\n💡 **Tip:** Usa `obtener_serie_temporal` con el ID para obtener los datos."
    return texto


@mcp.tool()
async def comparar_estados(indicador_id: str, estados: list[str], historica: bool = False) -> str:
    """
    Compara un indicador entre diferentes estados de México.

    Args:
        indicador_id: ID del indicador a comparar
        estados: Lista de códigos de estados (ej: ['31', '19', '09'])
        historica: true para serie completa, false para último dato
    """
    try:
        resultados = await indicadores_client.comparar_por_estados(
            indicador_id=indicador_id, codigos_estados=estados, historica=historica)

        nombre_indicador = INDICADORES_COMUNES.get(indicador_id, f"Indicador {indicador_id}")
        texto = f"## Comparación: {nombre_indicador}\n\n"

        for codigo, data in resultados.items():
            estado_nombre = DENUEConfig.ENTIDADES.get(codigo.zfill(2), f"Estado {codigo}")
            texto += f"### {estado_nombre}\n"
            if "error" in data:
                texto += f"❌ Error: {data['error']}\n\n"
            elif "Series" in data and data["Series"]:
                serie = data["Series"][0]
                obs = _ordenar_obs(serie.get("OBSERVATIONS", []) or [])
                if obs:
                    ultima = obs[-1]  # ya ordenado: el más reciente
                    texto += f"**Último dato:** {_fmt_valor(ultima.get('OBS_VALUE'))} ({ultima.get('TIME_PERIOD', 'N/A')})\n\n"
                else:
                    texto += "Sin datos disponibles\n\n"
            else:
                texto += "Sin datos disponibles\n\n"

        return texto

    except Exception as e:
        return f"Error al comparar estados: {str(e)}"


@mcp.tool()
async def buscar_catalogo_completo(
    busqueda: str, limite: int = 20, pagina: int = 0,
    area_geo: str = "null", tematica: str = ""
) -> str:
    """
    Busca indicadores en el catálogo COMPLETO del INEGI (miles de indicadores).

    Nota: el buscador de INEGI solo responde con area_geo="null". Si se pasa otro
    valor y no hay resultados, se reintenta sin filtro y se avisa. Para saber si un
    indicador tiene desglose estatal, revisa la "Cobertura" de cada resultado.

    Args:
        busqueda: Término de búsqueda (ej: 'PIB', 'IGAE', 'exportaciones', 'matrimonios')
        limite: Número máximo de resultados (default: 20, máx: 100)
        pagina: Página de resultados para paginación (default: 0)
        area_geo: Dejar en "null" (ver nota)
        tematica: Código de temática específica (opcional)
    """
    try:
        data, aviso = await _buscar_con_fallback_geo(
            busqueda, pagina * limite, (pagina * limite) + limite, area_geo, tematica)

        if not data:
            return (f"No se encontraron indicadores con el término '{busqueda}'.\n\n"
                    f"Sugerencias: prueba una sola palabra clave (ej. 'hoteles', 'turismo', "
                    f"'alojamiento temporal') o usa `buscar_banco_indicadores`.")

        total = data[0].get("TOTAL", len(data)) if isinstance(data[0], dict) else len(data)
        texto = f"## Catálogo Completo: '{busqueda}'\n\n"
        texto += f"**Total encontrados:** {total} | **Mostrando:** {min(len(data), limite)}\n"
        if aviso:
            texto += aviso + "\n"
        texto += "\n"

        for i, item in enumerate(data[:limite], 1):
            texto += _render_item_catalogo(item, numero=i)

        return texto

    except Exception as e:
        return f"Error al buscar en el catálogo completo: {str(e)}"


# ============================================================================
# HERRAMIENTAS DEL DENUE
# ============================================================================

@mcp.tool()
async def buscar_establecimientos(
    termino: str, latitud: Optional[float] = None,
    longitud: Optional[float] = None, radio: int = 250
) -> str:
    """
    Busca establecimientos en el DENUE por término y opcionalmente por ubicación.

    Args:
        termino: Palabra(s) a buscar (nombre, actividad, ubicación)
        latitud: Latitud del centro de búsqueda (opcional)
        longitud: Longitud del centro de búsqueda (opcional)
        radio: Radio de búsqueda en metros (default: 250)
    """
    try:
        resultados = await denue_client.buscar_establecimientos(
            termino=termino, latitud=latitud, longitud=longitud, radio=radio)

        if isinstance(resultados, list) and resultados:
            texto = f"## Establecimientos: {termino}\n\n**Total:** {len(resultados)}\n\n"
            for i, est in enumerate(resultados[:10], 1):
                nombre = est.get('Nombre') or est.get('Razon_social') or 'Sin nombre'
                texto += f"### {i}. {nombre}\n"
                texto += f"**Actividad:** {est.get('Clase_actividad', 'N/A')}\n"
                texto += f"**Dirección:** {est.get('Calle', '')} {est.get('Num_Exterior', '')}\n"
                texto += f"**Colonia:** {est.get('Colonia', 'N/A')} | **CP:** {est.get('CP', 'N/A')}\n"
                lat_e, lon_e = est.get('Latitud', 'N/A'), est.get('Longitud', 'N/A')
                if lat_e != 'N/A' and lon_e != 'N/A':
                    texto += f"**Coordenadas:** {lat_e}, {lon_e}\n"
                if est.get('Telefono'):
                    texto += f"**Teléfono:** {est['Telefono']}\n"
                texto += "\n"
            if len(resultados) > 10:
                texto += f"_(Mostrando 10 de {len(resultados)})_"
            return texto
        return f"No se encontraron establecimientos con el término '{termino}'"

    except Exception as e:
        return f"Error al buscar establecimientos: {str(e)}"


@mcp.tool()
async def obtener_coordenadas_establecimientos(
    termino: str, limite: int = 5, latitud: Optional[float] = None,
    longitud: Optional[float] = None, radio: int = 250
) -> str:
    """
    Obtiene las coordenadas geográficas de establecimientos.

    Args:
        termino: Nombre o tipo de establecimiento a buscar
        limite: Número máximo de resultados (default: 5)
        latitud: Latitud del centro de búsqueda (opcional)
        longitud: Longitud del centro de búsqueda (opcional)
        radio: Radio de búsqueda en metros (default: 250)
    """
    try:
        resultados = await denue_client.buscar_establecimientos(
            termino=termino, latitud=latitud, longitud=longitud, radio=radio)

        if isinstance(resultados, list) and resultados:
            texto = f"## Coordenadas: {termino}\n\n"
            if latitud and longitud:
                texto += f"**Centro:** {latitud}, {longitud} (radio: {radio}m)\n\n"
            texto += f"**Total:** {len(resultados)} | **Mostrando:** {min(limite, len(resultados))}\n\n"

            for i, est in enumerate(resultados[:limite], 1):
                nombre = est.get('Nombre') or est.get('Razon_social') or 'Sin nombre'
                lat, lon = est.get('Latitud', 'N/A'), est.get('Longitud', 'N/A')
                calle = f"{est.get('Calle', '')} {est.get('Num_Exterior', '')}".strip()
                if est.get('Colonia'):
                    calle += f", {est['Colonia']}"
                texto += f"### {i}. {nombre}\n"
                if calle:
                    texto += f"   **Dirección:** {calle}\n"
                texto += f"   **Coordenadas:** `{lat},{lon}`\n\n"

            if len(resultados) > limite:
                texto += f"_(Hay {len(resultados) - limite} más)_"
            return texto
        return f"No se encontraron establecimientos con '{termino}'"

    except Exception as e:
        return f"Error al obtener coordenadas: {str(e)}"


@mcp.tool()
async def buscar_area_act(
    entidad: str = "31", municipio: str = "0", nombre: str = "0",
    clase: str = "0", registro_inicial: int = 1, registro_final: int = 10
) -> str:
    """
    Búsqueda avanzada de establecimientos con AGEB, Manzana y clasificación económica.

    Args:
        entidad: Código de entidad (ej: "31"=Yucatán, "0"=todas)
        municipio: Código de municipio (ej: "050"=Mérida, "0"=todos)
        nombre: Nombre del establecimiento (ej: "OXXO", "0"=todos)
        clase: Código de clase económica (ej: "462112"=minisupers, "0"=todas)
        registro_inicial: Primer registro (default: 1)
        registro_final: Último registro (default: 10, máx: 1000)
    """
    try:
        resultados = await denue_client.buscar_area_act(
            entidad=entidad, municipio=municipio, nombre=nombre,
            clase=clase, registro_inicial=registro_inicial, registro_final=registro_final)

        if isinstance(resultados, list) and resultados:
            texto = "## Búsqueda Detallada DENUE\n\n"
            if entidad != "0":
                texto += f"**Entidad:** {DENUEConfig.ENTIDADES.get(entidad, entidad)}\n"
            if municipio != "0":
                texto += f"**Municipio:** {municipio}\n"
            if nombre != "0":
                texto += f"**Nombre:** {nombre}\n"
            if clase != "0":
                texto += f"**Clase:** {clase}\n"
            texto += f"**Total:** {len(resultados)}\n\n---\n\n"

            for i, est in enumerate(resultados[:registro_final], 1):
                nombre_est = est.get('Nombre') or est.get('Razon_social') or 'Sin nombre'
                texto += f"### {i}. {nombre_est}\n"
                texto += f"**Actividad:** {est.get('Clase_actividad', 'N/A')}\n"
                texto += f"**Dirección:** {est.get('Calle', '')} {est.get('Num_Exterior', '')}\n"
                texto += f"**Colonia:** {est.get('Colonia', 'N/A')} | **CP:** {est.get('CP', 'N/A')}\n"
                ageb, manzana = est.get('AGEB', 'N/A'), est.get('Manzana', 'N/A')
                if ageb != 'N/A' or manzana != 'N/A':
                    texto += f"**AGEB:** {ageb} | **Manzana:** {manzana}\n"
                lat, lon = est.get('Latitud', 'N/A'), est.get('Longitud', 'N/A')
                if lat != 'N/A' and lon != 'N/A':
                    texto += f"**Coordenadas:** {lat}, {lon}\n"
                if est.get('Telefono'):
                    texto += f"**Teléfono:** {est['Telefono']}\n"
                texto += "\n"
            return texto
        return "No se encontraron establecimientos con los criterios especificados."

    except Exception as e:
        return f"Error al buscar establecimientos: {str(e)}"


@mcp.tool()
async def cuantificar_establecimientos(
    actividad_economica: str = "0", area_geografica: str = "0", estrato: str = "0"
) -> str:
    """
    Cuantifica establecimientos por actividad económica, área geográfica y tamaño.

    Args:
        actividad_economica: Código de actividad (0=todas, ej: '46'=comercio al por menor)
        area_geografica: Código de área (0=México, '31'=Yucatán, '31050'=Mérida)
        estrato: Tamaño por empleados (0=todos, 1=0-5, 2=6-10, 3=11-30...)
    """
    try:
        resultados = await denue_client.cuantificar(
            actividad_economica=actividad_economica,
            area_geografica=area_geografica, estrato=estrato)

        if isinstance(resultados, list) and resultados:
            texto = "## Cuantificación de Establecimientos\n\n"
            texto += f"**Actividad:** {actividad_economica if actividad_economica != '0' else 'Todas'}\n"
            area_n = DENUEConfig.ENTIDADES.get(area_geografica, f"Área {area_geografica}")
            texto += f"**Área:** {area_n if area_geografica != '0' else 'Todo México'}\n\n"
            total_g = sum(int(r.get('Total', 0)) for r in resultados)
            texto += f"**Total:** {total_g:,} establecimientos\n\n"
            if len(resultados) > 1:
                texto += "### Desglose:\n\n"
                for r in resultados[:20]:
                    ag = r.get('AG', 'N/A')
                    nombre_area = DENUEConfig.ENTIDADES.get(ag, f"Área {ag}")
                    texto += f"- **{nombre_area}**: {int(r.get('Total', 0)):,}\n"
            return texto
        return "No se encontraron establecimientos con los criterios especificados."

    except Exception as e:
        return f"Error al cuantificar establecimientos: {str(e)}"


# ============================================================================
# NUEVAS HERRAMIENTAS — BANCO DE INDICADORES BIE (búsqueda semántica directa)
# ============================================================================

@mcp.tool()
async def buscar_banco_indicadores(
    busqueda: str,
    area_geo: str = "null",
    pagina: int = 0,
    limite: int = 20,
) -> str:
    """
    Busca indicadores en el Banco de Indicadores del INEGI (BIE + BISE).
    Usa búsqueda semántica por ranking — el mismo endpoint que el portal web del INEGI.

    Consejos:
    - Funciona mejor con una o dos palabras ('turismo', 'hoteles', 'alojamiento temporal',
      'visitantes internacionales', 'PIB', 'IGAE', 'precios consumidor').
    - Los acentos no afectan la búsqueda.
    - El filtro geográfico del buscador de INEGI vacía los resultados; se ignora y la
      cobertura real (Nacional/Estatal/Municipal) se muestra en cada resultado.
    - Un mismo título puede aparecer varias veces con IDs distintos: son valoraciones
      diferentes (precios corrientes, precios 2013, índice). Distínguelos por Unidad y Categoría.

    Args:
        busqueda: Término de búsqueda en español
        area_geo: Dejar en 'null' (ver consejos)
        pagina: Página de resultados (default: 0)
        limite: Resultados por página (default: 20)
    """
    try:
        data, aviso = await _buscar_con_fallback_geo(
            busqueda, pagina * limite, (pagina * limite) + limite, area_geo, "")

        if not data:
            return (
                f"Sin resultados para '{busqueda}' en el Banco de Indicadores de INEGI.\n\n"
                f"Puede que INEGI no publique ese indicador (por ejemplo, la ocupación hotelera "
                f"la publica SECTUR/DataTur, no INEGI). Prueba con una sola palabra clave o un "
                f"sinónimo: 'hoteles', 'alojamiento temporal', 'turismo', 'visitantes internacionales'."
            )

        total = data[0].get("TOTAL", len(data)) if data else 0
        pagina_actual = pagina + 1
        paginas_total = max(1, -(-total // limite))

        lines = [
            f"## Banco de Indicadores INEGI: '{busqueda}'",
            f"**Total:** {total} | **Página:** {pagina_actual}/{paginas_total}",
        ]
        if aviso:
            lines.append(aviso)
        lines.append("")

        for item in data:
            lines.append(_render_item_catalogo(item))

        if total > (pagina + 1) * limite:
            lines.append(f"_Más resultados disponibles. Usa `pagina={pagina + 1}`._")

        return "\n".join(lines)

    except httpx.HTTPStatusError as e:
        return f"Error HTTP {e.response.status_code}: {e}"
    except Exception as e:
        return f"Error inesperado: {e}"


async def _buscar_con_fallback_geo(busqueda: str, inicio: int, fin: int, area_geo: str,
                                   tematica: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Llama al buscador de INEGI. Si se pidió un filtro geográfico distinto de 'null' y
    no hubo resultados, reintenta sin filtro (el buscador vacía la respuesta con
    cualquier área) y devuelve un aviso para el usuario.
    """
    data = await indicadores_client.buscar_catalogo_completo(
        busqueda=busqueda, pagina_inicio=inicio, pagina_fin=fin,
        area_geo=area_geo or "null", tematica=tematica)
    aviso = ""
    if (not data or not isinstance(data, list)) and (area_geo or "null") != "null":
        data = await indicadores_client.buscar_catalogo_completo(
            busqueda=busqueda, pagina_inicio=inicio, pagina_fin=fin,
            area_geo="null", tematica=tematica)
        if data:
            aviso = (f"_El filtro geográfico '{area_geo}' no devuelve resultados en el buscador de INEGI; "
                     f"se muestran todos. Revisa la Cobertura de cada indicador._")
    if not isinstance(data, list):
        data = []
    return data, aviso


def _render_item_catalogo(item: Dict[str, Any], numero: Optional[int] = None) -> str:
    """Formato común para resultados del buscador, con ruta temática completa y aviso de base cerrada."""
    ind_id     = item.get("INDICADOR", "")
    titulo     = item.get("TITULO", "Sin título")
    tematica   = (item.get("TEMATICA", "") or "").replace("Banco de Indicadores > ", "")
    unidad     = item.get("UNIDAD_MEDIDA", "") or ""
    frecuencia = item.get("FRECUENCIA_DESCRIPCION", "") or ""
    periodos   = item.get("PERIODOS", "") or ""
    fuente     = item.get("FUENTE_DESCRIPCION", "") or ""
    try:
        desglose = int(item.get("MAXIMODESGLOSEGEOGRAFICO", 1))
    except (TypeError, ValueError):
        desglose = 1
    nivel_geo = {1: "Nacional", 2: "Estatal", 3: "Municipal"}.get(desglose, "Nacional")

    ultimo = ""
    if periodos:
        pl = sorted((p.strip() for p in periodos.split(",") if p.strip()), key=_clave_periodo)
        rango = f"{pl[0]} - {pl[-1]}" if len(pl) > 1 else pl[0]
        ultimo = pl[-1]
    else:
        rango = "N/D"

    encabezado = f"### {numero}. {titulo}" if numero else f"### {titulo}"
    lines = [encabezado, f"**ID:** `{ind_id}`"]
    if tematica:
        lines.append(f"**Categoría:** {' > '.join(p.strip() for p in tematica.split('>'))}")
    lines.append(f"**Unidad:** {unidad or 'N/D'} | **Frecuencia:** {frecuencia or 'N/D'} | **Cobertura:** {nivel_geo}")
    lines.append(f"**Períodos:** {rango}")
    if fuente:
        lines.append(f"**Fuente:** {fuente}")
    aviso = _aviso_base_cerrada(unidad + " " + fuente, ultimo)
    if aviso:
        lines.append(aviso.strip())
    geo_hint = "codigo_geo='31'" if desglose >= 2 else "codigo_geo='00'"
    lines.append(f"💡 `obtener_indicador_inteligente(indicador_id='{ind_id}', {geo_hint})`")
    lines.append("")
    return "\n".join(lines)


@mcp.tool()
async def obtener_indicador_inteligente(
    indicador_id: str,
    codigo_geo: str = "31",
    historica: bool = True,
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    limite: int = _LIMITE_DEFAULT,
) -> str:
    """
    Versión inteligente de obtener_serie_temporal.
    Detecta el nivel geográfico del indicador (metadatos del Banco de Indicadores),
    consulta la serie probando los tres bancos (BIE, BISE, BIE-BISE) y hace fallback
    a nacional si el nivel estatal no está disponible. Unidades y frecuencias se
    devuelven decodificadas; las observaciones, en orden cronológico y priorizando
    las más recientes.

    Args:
        indicador_id: ID del indicador (obtenido de buscar_banco_indicadores)
        codigo_geo: Código de estado (default: '31'=Yucatán; '00'=nacional)
        historica: True=serie completa, False=último dato
        desde: Periodo inicial, ej. '2018' o '2018/01' (opcional)
        hasta: Periodo final, ej. '2025' o '2025/12' (opcional)
        limite: Máximo de observaciones a mostrar (default 80; 0 = sin límite)
    """
    if not (indicadores_client.token or os.getenv("INEGI_INDICADORES_TOKEN", "")):
        return "Error: INEGI_INDICADORES_TOKEN no encontrado en variables de entorno."

    # 1) Metadatos del Banco de Indicadores. Solo se aceptan si el INDICADOR coincide
    #    con el ID pedido; antes se tomaba el primer resultado y se mezclaban títulos.
    meta: Dict[str, Any] = {}
    try:
        candidatos = await indicadores_client.buscar_catalogo_completo(
            busqueda=str(indicador_id), pagina_inicio=0, pagina_fin=5, area_geo="null")
        if isinstance(candidatos, list):
            meta = next((c for c in candidatos
                         if str(c.get("INDICADOR", "")).strip() == str(indicador_id).strip()), {}) or {}
    except Exception:
        meta = {}

    titulo = meta.get("TITULO") or INDICADORES_COMUNES.get(indicador_id, f"Indicador {indicador_id}")
    tematica = (meta.get("TEMATICA", "") or "").replace("Banco de Indicadores > ", "")
    fuente = meta.get("FUENTE_DESCRIPCION", "") or ""
    try:
        desglose = int(meta.get("MAXIMODESGLOSEGEOGRAFICO", 1))
    except (TypeError, ValueError):
        desglose = 1
    nivel_geo_desc = {1: "Nacional", 2: "Estatal", 3: "Municipal"}

    # 2) Nivel geográfico a intentar
    codigo_geo = (codigo_geo or "00").zfill(2)
    pedir_estatal = codigo_geo != "00" and (desglose >= 2 or not meta)
    geo_inicial = codigo_geo if pedir_estatal else "00"

    # 3) Serie con reintento de bancos y fallback estatal → nacional
    data = None
    fallback_aplicado = False
    errores: List[str] = []
    for geo in ([geo_inicial, "00"] if geo_inicial != "00" else ["00"]):
        try:
            data = await indicadores_client.obtener_indicador(
                indicador_id=indicador_id, area_geo=geo, historica=historica)
            if geo != geo_inicial:
                fallback_aplicado = True
            break
        except IndicadorNoDisponible as e:
            errores.append(str(e))
        except Exception as e:
            errores.append(f"Error de conexión: {e}")

    if data is None:
        intentados = "Estatal y nacional" if geo_inicial != "00" else "Nacional"
        return (f"## {titulo} — `{indicador_id}`\n\n"
                f"No fue posible obtener la serie.\n"
                f"**Niveles intentados:** {intentados}"
                f" · **Desglose declarado en catálogo:** {nivel_geo_desc.get(desglose, 'N/D') if meta else 'sin metadatos'}\n"
                + "\n".join(f"- {e}" for e in errores)
                + "\n\nVerifica el ID con `buscar_banco_indicadores`.")

    serie = data["Series"][0]
    unidad, frecuencia = await _describir_serie(serie)
    geo_usado = data.get("_geo", geo_inicial)
    if geo_usado == "00":
        nivel_usado = "Nacional" + (" (fallback: sin datos estatales)" if fallback_aplicado
                                    else "" if pedir_estatal else " (único nivel disponible)")
    else:
        nivel_usado = f"Estatal · {DENUEConfig.ENTIDADES.get(geo_usado, geo_usado)} ({geo_usado})"

    obs = serie.get("OBSERVATIONS", []) or []
    lines = [f"## {titulo}", f"**ID:** `{indicador_id}` · **Banco:** {data.get('_banco', 'N/D')}"]
    if tematica:
        lines.append(f"**Categoría:** {' > '.join(p.strip() for p in tematica.split('>'))}")
    lines.append(f"**Unidad:** {unidad} | **Frecuencia:** {frecuencia}")
    if meta.get("UNIDAD_MEDIDA") and meta["UNIDAD_MEDIDA"].strip().lower() != unidad.strip().lower():
        lines.append(f"> ℹ️ El catálogo describe la unidad como «{meta['UNIDAD_MEDIDA']}», "
                     f"pero la serie reporta «{unidad}». Prevalece la serie.")
    lines.append(f"**Nivel geográfico:** {nivel_usado}")
    if fuente:
        lines.append(f"**Fuente:** {fuente}")
    lines.append(f"**Última actualización INEGI:** {serie.get('LASTUPDATE', 'N/A')}")
    if fallback_aplicado:
        lines.append("\n> ⚠️ Se solicitaron datos estatales pero la API solo sirve nivel nacional.")

    if not obs:
        lines.append("\n_La API respondió pero la serie no trae observaciones._")
        return "\n".join(lines)

    ultimo = _ordenar_obs(obs)[-1].get("TIME_PERIOD", "")
    aviso = _aviso_base_cerrada(unidad + " " + fuente, ultimo)
    if aviso:
        lines.append(aviso.strip())
    lines.append("")
    lines.append(_render_observaciones(obs, limite, desde, hasta, tabla=True))
    return "\n".join(lines)


def main():
    """Punto de entrada para el servidor"""
    mcp.run()


if __name__ == "__main__":
    main()
