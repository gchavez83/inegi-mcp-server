"""
Servidor MCP principal para las APIs del INEGI usando FastMCP
"""
import os
import httpx
from mcp.server.fastmcp import FastMCP
from .clients import IndicadoresClient, DENUEClient
from .config import INDICADORES_COMUNES, DENUEConfig
from typing import Optional

# Crear el servidor FastMCP
mcp = FastMCP("inegi-mcp")

# Inicializar clientes
indicadores_client = IndicadoresClient()
denue_client = DENUEClient()


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
    idioma: str = "es"
) -> str:
    """
    Obtiene datos de un indicador económico o demográfico del INEGI.

    Args:
        indicador_id: ID del indicador (ej: '1002000001' para población)
        area_geografica: Área: '00'=nacional, '99'=estatal, '999'=municipal
        codigo_geo: Código de estado/municipio (ej: '31' para Yucatán)
        historica: true para serie completa, false para último dato
        idioma: Idioma: 'es' o 'en'
    """
    try:
        data = await indicadores_client.obtener_indicador(
            indicador_id=indicador_id, area_geo=area_geografica,
            codigo_geo=codigo_geo, historica=historica, idioma=idioma
        )

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
                LIMITE = 80
                ultimas = obs[-LIMITE:] if len(obs) > LIMITE else obs
                for o in ultimas:
                    texto += f"- {o.get('TIME_PERIOD', 'N/A')}: {o.get('OBS_VALUE', 'N/A')}\n"
                if len(obs) > LIMITE:
                    texto += f"\n_(Mostrando las últimas {LIMITE} de {len(obs)} observaciones)_"
            return texto
        else:
            return f"No se encontraron datos para el indicador {indicador_id}"

    except Exception as e:
        return f"Error al obtener el indicador: {str(e)}"


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
                obs = serie.get("OBSERVATIONS", [])
                if obs:
                    ultima = obs[-1]
                    texto += f"**Último dato:** {ultima.get('OBS_VALUE', 'N/A')} ({ultima.get('TIME_PERIOD', 'N/A')})\n\n"
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
    area_geo: str = "00", tematica: str = ""
) -> str:
    """
    Busca indicadores en el catálogo COMPLETO del INEGI (miles de indicadores).

    Args:
        busqueda: Término de búsqueda (ej: 'PIB', 'IGAE', 'exportaciones', 'matrimonios')
        limite: Número máximo de resultados (default: 20, máx: 100)
        pagina: Página de resultados para paginación (default: 0)
        area_geo: Área geográfica ("00"=nacional)
        tematica: Código de temática específica (opcional)
    """
    try:
        data = await indicadores_client.buscar_catalogo_completo(
            busqueda=busqueda, pagina_inicio=pagina * limite,
            pagina_fin=(pagina * limite) + limite, area_geo=area_geo, tematica=tematica
        )

        if not data or not isinstance(data, list) or len(data) == 0:
            return f"No se encontraron indicadores con el término '{busqueda}'"

        total = len(data)
        texto = f"## Catálogo Completo: '{busqueda}'\n\n"
        texto += f"**Total encontrados:** {total} | **Mostrando:** {min(total, limite)}\n\n"

        for i, item in enumerate(data[:limite], 1):
            titulo = item.get("TITULO", "Sin título")
            codigo = item.get("INDICADOR", "N/A")
            tematica_desc = item.get("TEMATICA", "").replace("Banco de Indicadores > ", "")
            partes = tematica_desc.split(" > ")
            cat = " > ".join(partes[:3]) + ("..." if len(partes) > 3 else "")
            unidad = item.get("UNIDAD_MEDIDA", "")
            frecuencia = item.get("FRECUENCIA_DESCRIPCION", "")
            periodos = item.get("PERIODOS", "")
            fuente = item.get("FUENTE_DESCRIPCION", "")

            texto += f"### {i}. {titulo}\n"
            texto += f"**ID:** `{codigo}`\n"
            if cat:
                texto += f"**Categoría:** {cat}\n"
            if unidad:
                texto += f"**Unidad:** {unidad}\n"
            if frecuencia:
                texto += f"**Frecuencia:** {frecuencia}\n"
            if periodos:
                pl = periodos.split(", ")
                texto += f"**Períodos:** {', '.join(pl[:5])}{'...' if len(pl) > 5 else ''}\n"
            if fuente and len(fuente) < 100:
                texto += f"**Fuente:** {fuente}\n"
            texto += f"💡 `obtener_indicador_inteligente(indicador_id='{codigo}')`\n\n"

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
    Busca indicadores en el Banco de Indicadores del INEGI (BIE).
    Usa búsqueda semántica por ranking — el mismo endpoint que el portal web del INEGI.

    Términos que funcionan (validados): PIB, IGAE, exportaciones, balanza,
    precios consumidor, indice precios, ocupacion, salario, industria, crecimiento.

    Términos que NO funcionan directamente: 'inflacion', 'INPC' — en ese caso
    usar 'precios consumidor' o 'indice precios'.

    Args:
        busqueda: Término de búsqueda exacto en español
        area_geo: Área geográfica ('null'=todas, '31'=Yucatán)
        pagina: Página de resultados (default: 0)
        limite: Resultados por página (default: 20)
    """
    url = "https://www.inegi.org.mx/app/api/buscadorcore/v1/busquedaBancoIndicadores/"

    payload = {
        "busqueda": busqueda,
        "busquedaCiencia": "",
        "paginaInicio": pagina * limite,
        "paginaFin": (pagina * limite) + limite,
        "areageo": area_geo,
        "filtrobusqueda": "CBUSQUEDA",
        "filtrotema": "null",
        "herramienta": 405,
        "idioma": "es",
        "metodoBusqueda": 1,
        "orderby": "RANKING",
        "orderbyAscDesc": "Desc",
        "tematica": "6",
        "IndPrincipales": "null",
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "es-MX,es;q=0.9",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        if not data:
            return (
                f"Sin resultados para '{busqueda}'.\n\n"
                f"**Términos validados que sí funcionan:**\n"
                f"- Económicos: `PIB`, `IGAE`, `exportaciones`, `balanza`, `crecimiento`\n"
                f"- Precios: `precios consumidor`, `indice precios`\n"
                f"- Empleo: `ocupacion`, `salario`\n"
                f"- Sector: `industria`, `agricultura`, `comercio`\n"
            )

        total = data[0].get("TOTAL", len(data)) if data else 0
        pagina_actual = pagina + 1
        paginas_total = -(-total // limite)

        lines = [
            f"## Banco de Indicadores INEGI: '{busqueda}'",
            f"**Total:** {total} | **Página:** {pagina_actual}/{paginas_total}",
            "",
        ]

        for item in data:
            ind_id     = item.get("INDICADOR", "")
            titulo     = item.get("TITULO", "")
            tematica   = item.get("TEMATICA", "")
            unidad     = item.get("UNIDAD_MEDIDA", "")
            frecuencia = item.get("FRECUENCIA_DESCRIPCION", "")
            periodos   = item.get("PERIODOS", "")
            desglose   = int(item.get("MAXIMODESGLOSEGEOGRAFICO", 1))
            fuente     = item.get("FUENTE_DESCRIPCION", "")

            nivel_geo = {1: "Nacional", 2: "Estatal", 3: "Municipal"}.get(desglose, "Nacional")

            if periodos:
                pl = [p.strip() for p in periodos.split(",")]
                rango = f"{pl[-1]} - {pl[0]}" if len(pl) > 1 else pl[0]
            else:
                rango = "N/D"

            if tematica:
                partes = tematica.split(">")
                categoria = " > ".join(p.strip() for p in partes[-3:])
            else:
                categoria = ""

            lines.append(f"### {titulo}")
            lines.append(f"**ID:** `{ind_id}`")
            if categoria:
                lines.append(f"**Categoría:** {categoria}")
            lines.append(f"**Unidad:** {unidad} | **Frecuencia:** {frecuencia} | **Cobertura:** {nivel_geo}")
            lines.append(f"**Períodos:** {rango}")
            if fuente:
                lines.append(f"**Fuente:** {fuente}")
            lines.append(f"💡 `obtener_indicador_inteligente(indicador_id='{ind_id}')`")
            lines.append("")

        if total > (pagina + 1) * limite:
            lines.append(f"_Más resultados disponibles. Usa `pagina={pagina + 1}`._")

        return "\n".join(lines)

    except httpx.HTTPStatusError as e:
        return f"Error HTTP {e.response.status_code}: {e}"
    except Exception as e:
        return f"Error inesperado: {e}"


@mcp.tool()
async def obtener_indicador_inteligente(
    indicador_id: str,
    codigo_geo: str = "31",
    historica: bool = True,
) -> str:
    """
    Versión inteligente de obtener_serie_temporal.
    Detecta automáticamente el nivel geográfico del indicador y hace fallback
    a nacional si el nivel estatal no está disponible.

    Args:
        indicador_id: ID del indicador (obtenido de buscar_banco_indicadores)
        codigo_geo: Código de estado (default: '31'=Yucatán)
        historica: True=serie completa, False=último dato
    """
    token = os.getenv("INEGI_INDICADORES_TOKEN", "")
    if not token:
        return "Error: INEGI_INDICADORES_TOKEN no encontrado en variables de entorno."

    meta_url = "https://www.inegi.org.mx/app/api/buscadorcore/v1/busquedaBancoIndicadores/"
    payload = {
        "busqueda": indicador_id, "busquedaCiencia": "", "paginaInicio": 0, "paginaFin": 5,
        "areageo": "null", "filtrobusqueda": "CBUSQUEDA", "filtrotema": "null",
        "herramienta": 405, "idioma": "es", "metodoBusqueda": 1,
        "orderby": "RANKING", "orderbyAscDesc": "Desc", "tematica": "6", "IndPrincipales": "null",
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "es-MX,es;q=0.9",
    }

    titulo = indicador_id
    unidad = frecuencia = tematica = periodos = ""
    desglose = 1

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            meta_resp = await client.post(meta_url, json=payload, headers=headers)
            meta_resp.raise_for_status()
            meta_data = meta_resp.json()

        meta = next(
            (item for item in meta_data if str(item.get("INDICADOR", "")) == str(indicador_id)),
            meta_data[0] if meta_data else None,
        )
        if meta:
            titulo     = meta.get("TITULO", indicador_id)
            unidad     = meta.get("UNIDAD_MEDIDA", "")
            frecuencia = meta.get("FRECUENCIA_DESCRIPCION", "")
            tematica   = meta.get("TEMATICA", "")
            periodos   = meta.get("PERIODOS", "")
            desglose   = int(meta.get("MAXIMODESGLOSEGEOGRAFICO", 1))
    except Exception:
        titulo = f"Indicador {indicador_id}"

    nivel_geo_desc = {1: "Nacional", 2: "Estatal", 3: "Municipal"}
    usar_estatal = desglose >= 2
    geo_part = codigo_geo if usar_estatal else "00"
    nivel_usado = f"Estatal ({codigo_geo})" if usar_estatal else "Nacional (único nivel disponible)"

    historica_api = "false" if historica else "true"
    base_api = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR"

    def build_url(geo):
        return f"{base_api}/{indicador_id}/es/{geo}/{historica_api}/BIE-BISE/2.0/{token}?type=json"

    fallback_aplicado = False
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(build_url(geo_part))

        if resp.status_code == 400 and usar_estatal:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(build_url("00"))
            nivel_usado = "Nacional (fallback — datos estatales no disponibles)"
            fallback_aplicado = True

        resp.raise_for_status()
        data_json = resp.json()

    except httpx.HTTPStatusError as e:
        return (
            f"## {titulo} — `{indicador_id}`\n\n"
            f"Error HTTP {e.response.status_code}\n"
            f"**Nivel intentado:** {nivel_usado}\n"
            f"**Desglose declarado:** {nivel_geo_desc.get(desglose, str(desglose))}"
        )
    except Exception as e:
        return f"Error de conexión: {e}"

    try:
        series = data_json.get("Series", [])
        if not series:
            return f"## {titulo}\n\nLa API respondió pero no contiene series de datos."

        obs_list = series[0].get("OBSERVATIONS", [])
        if not historica:
            obs_list = obs_list[:1]

        if periodos:
            p = [x.strip() for x in periodos.split(",")]
            rango_periodos = f"{p[-1]} - {p[0]}"
        else:
            rango_periodos = "N/D"

        if tematica:
            partes = tematica.split(">")
            categoria = " > ".join(p.strip() for p in partes[-3:])
        else:
            categoria = ""

        lines = [f"## {titulo}", f"**ID:** `{indicador_id}`"]
        if categoria:
            lines.append(f"**Categoría:** {categoria}")
        lines += [
            f"**Unidad:** {unidad} | **Frecuencia:** {frecuencia}",
            f"**Nivel geográfico:** {nivel_usado}",
            f"**Períodos publicados:** {rango_periodos}",
            f"**Observaciones recuperadas:** {len(obs_list)}",
        ]
        if fallback_aplicado:
            lines.append("\n> ⚠️ Se solicitaron datos estatales pero la API solo sirve nivel nacional.")

        lines += ["", "| Período | Valor |", "|---------|-------|"]
        for obs in obs_list:
            periodo = obs.get("TIME_PERIOD", "")
            valor = obs.get("OBS_VALUE", "")
            try:
                valor_fmt = f"{float(valor):,.4f}".rstrip("0").rstrip(".")
            except (ValueError, TypeError):
                valor_fmt = valor or "N/D"
            lines.append(f"| {periodo} | {valor_fmt} |")

        return "\n".join(lines)

    except Exception as e:
        return f"## {titulo}\nError al parsear respuesta: {e}"


def main():
    """Punto de entrada para el servidor"""
    mcp.run()


if __name__ == "__main__":
    main()
