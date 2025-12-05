"""
Servidor MCP principal para las APIs del INEGI usando FastMCP
"""
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
    Útil para encontrar el ID de indicadores disponibles.
    
    Args:
        query: Término de búsqueda (ej: 'población', 'PIB', 'empleo')
    """
    query_lower = query.lower()
    resultados = []
    
    for indicador_id, nombre in INDICADORES_COMUNES.items():
        if query_lower in nombre.lower():
            resultados.append(f"- **{nombre}** (ID: `{indicador_id}`)")
    
    if resultados:
        texto = "## Indicadores encontrados:\n\n"
        texto += "\n".join(resultados)
        texto += "\n\n💡 Usa el ID para obtener los datos con `obtener_serie_temporal`"
        return texto
    else:
        texto = f"No se encontraron indicadores con el término '{query}'.\n\n"
        texto += "**Indicadores disponibles:**\n"
        for indicador_id, nombre in INDICADORES_COMUNES.items():
            texto += f"- {nombre} (ID: `{indicador_id}`)\n"
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
    Puede obtener datos a nivel nacional, estatal o municipal.
    
    Args:
        indicador_id: ID del indicador (ej: '1002000001' para población)
        area_geografica: Área: '00'=nacional, '99'=estatal, '999'=municipal
        codigo_geo: Código de estado/municipio (ej: '31' para Yucatán)
        historica: true para serie completa, false para último dato
        idioma: Idioma: 'es' o 'en'
    """
    try:
        data = await indicadores_client.obtener_indicador(
            indicador_id=indicador_id,
            area_geo=area_geografica,
            codigo_geo=codigo_geo,
            historica=historica,
            idioma=idioma
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
                    periodo = o.get("TIME_PERIOD", "N/A")
                    valor = o.get("OBS_VALUE", "N/A")
                    texto += f"- {periodo}: {valor}\n"
                
                if len(obs) > LIMITE:
                    texto += f"\n_(Mostrando las últimas {LIMITE} de {len(obs)} observaciones)_"
            
            return texto
        else:
            return f"No se encontraron datos para el indicador {indicador_id}"
            
    except Exception as e:
        return f"Error al obtener el indicador: {str(e)}"


@mcp.tool()
async def listar_indicadores_disponibles() -> str:
    """
    Lista todos los indicadores disponibles en el catálogo básico.
    """
    texto = "## Indicadores Disponibles\n\n"
    texto += "Estos son algunos indicadores comunes. Usa su ID para consultar datos.\n\n"
    
    for indicador_id, nombre in INDICADORES_COMUNES.items():
        texto += f"- **{nombre}**\n"
        texto += f"  - ID: `{indicador_id}`\n\n"
    
    texto += "\n💡 **Tip:** Usa `obtener_serie_temporal` con el ID para obtener los datos."
    
    return texto


@mcp.tool()
async def comparar_estados(
    indicador_id: str,
    estados: list[str],
    historica: bool = False
) -> str:
    """
    Compara un indicador entre diferentes estados de México.
    Útil para análisis regional.
    
    Args:
        indicador_id: ID del indicador a comparar
        estados: Lista de códigos de estados (ej: ['31', '19', '09'])
        historica: true para serie completa, false para último dato
    """
    try:
        resultados = await indicadores_client.comparar_por_estados(
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
        
        return texto
        
    except Exception as e:
        return f"Error al comparar estados: {str(e)}"


@mcp.tool()
async def buscar_catalogo_completo(
    busqueda: str,
    limite: int = 20,
    pagina: int = 0,
    area_geo: str = "00",
    tematica: str = ""
) -> str:
    """
    Busca indicadores en el catálogo COMPLETO del INEGI (miles de indicadores).
    Mucho más amplio que buscar_indicadores() que solo busca en ~30 indicadores básicos.
    
    Args:
        busqueda: Término de búsqueda (ej: 'delitos', 'comercio exterior', 'mortalidad')
        limite: Número máximo de resultados (default: 20, máx: 100)
        pagina: Página de resultados para paginación (default: 0)
        area_geo: Área geográfica ("00"=nacional, código específico para otros)
        tematica: Código de temática específica (opcional)
    """
    try:
        # Calcular paginación
        pagina_inicio = pagina * limite
        pagina_fin = pagina_inicio + limite
        
        # Llamar al cliente con los parámetros correctos
        data = await indicadores_client.buscar_catalogo_completo(
            busqueda=busqueda,
            pagina_inicio=pagina_inicio,
            pagina_fin=pagina_fin,
            area_geo=area_geo,
            tematica=tematica
        )
        
        # La respuesta es directamente una lista de indicadores
        if not data or not isinstance(data, list) or len(data) == 0:
            return f"No se encontraron indicadores con el término '{busqueda}'"
        
        resultados = data
        total = len(resultados)
        
        texto = f"## Búsqueda en Catálogo Completo: '{busqueda}'\n\n"
        texto += f"**Total encontrados:** {total} indicadores\n"
        texto += f"**Mostrando:** {len(resultados)} resultados\n\n"
        
        for i, indicador in enumerate(resultados[:limite], 1):
            titulo = indicador.get("TITULO", "Sin título")
            codigo = indicador.get("INDICADOR", "N/A")
            tematica_desc = indicador.get("TEMATICA", "")
            unidad = indicador.get("UNIDAD_MEDIDA", "")
            frecuencia_desc = indicador.get("FRECUENCIA_DESCRIPCION", "")
            periodos = indicador.get("PERIODOS", "")
            fuente = indicador.get("FUENTE_DESCRIPCION", "")
            
            # Limpiar la temática para que sea más legible
            if tematica_desc:
                # Quitar "Banco de Indicadores >" del inicio
                tematica_limpia = tematica_desc.replace("Banco de Indicadores > ", "")
                # Tomar solo las primeras categorías para no hacer muy largo
                partes_tematica = tematica_limpia.split(" > ")
                if len(partes_tematica) > 3:
                    tematica_limpia = " > ".join(partes_tematica[:3]) + "..."
                else:
                    tematica_limpia = " > ".join(partes_tematica)
            else:
                tematica_limpia = "N/A"
            
            texto += f"### {i}. {titulo}\n"
            texto += f"**ID:** `{codigo}`\n"
            texto += f"**Categoría:** {tematica_limpia}\n"
            if unidad:
                texto += f"**Unidad:** {unidad}\n"
            if frecuencia_desc:
                texto += f"**Frecuencia:** {frecuencia_desc}\n"
            if periodos:
                # Mostrar solo algunos períodos si son muchos
                periodos_lista = periodos.split(", ")
                if len(periodos_lista) > 5:
                    periodos_mostrar = ", ".join(periodos_lista[:5]) + "..."
                else:
                    periodos_mostrar = periodos
                texto += f"**Períodos:** {periodos_mostrar}\n"
            if fuente and len(fuente) < 100:  # Solo mostrar fuente si no es muy larga
                texto += f"**Fuente:** {fuente}\n"
            texto += f"💡 *Usa `obtener_serie_temporal` con ID `{codigo}` para obtener los datos*\n\n"
        
        return texto
        
    except Exception as e:
        return f"Error al buscar en el catálogo completo: {str(e)}"


# ============================================================================
# HERRAMIENTAS DEL DENUE
# ============================================================================

@mcp.tool()
async def buscar_establecimientos(
    termino: str,
    latitud: Optional[float] = None,
    longitud: Optional[float] = None,
    radio: int = 250
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
            termino=termino,
            latitud=latitud,
            longitud=longitud,
            radio=radio
        )
        
        if isinstance(resultados, list) and len(resultados) > 0:
            texto = f"## Establecimientos encontrados: {termino}\n\n"
            texto += f"**Total:** {len(resultados)} establecimientos\n\n"
            
            for i, est in enumerate(resultados[:10], 1):
                nombre = est.get('Nombre', 'Sin nombre')
                razon_social = est.get('Razon_social', '')
                nombre_mostrar = nombre if nombre and nombre != 'Sin nombre' else razon_social if razon_social else 'Sin nombre'
                
                texto += f"### {i}. {nombre_mostrar}\n"
                texto += f"**Actividad:** {est.get('Clase_actividad', 'N/A')}\n"
                texto += f"**Dirección:** {est.get('Calle', '')} {est.get('Num_Exterior', '')}\n"
                texto += f"**Colonia:** {est.get('Colonia', 'N/A')}\n"
                texto += f"**Ubicación:** {est.get('Ubicacion', 'N/A')}\n"
                texto += f"**CP:** {est.get('CP', 'N/A')}\n"
                
                # Agregar coordenadas
                latitud_est = est.get('Latitud', 'N/A')
                longitud_est = est.get('Longitud', 'N/A')
                if latitud_est != 'N/A' and longitud_est != 'N/A':
                    texto += f"**Coordenadas:** {latitud_est}, {longitud_est}\n"
                
                if est.get('Telefono'):
                    texto += f"**Teléfono:** {est.get('Telefono')}\n"
                texto += "\n"
            
            if len(resultados) > 10:
                texto += f"\n_(Mostrando 10 de {len(resultados)} resultados)_"
            
            return texto
        else:
            return f"No se encontraron establecimientos con el término '{termino}'"
            
    except Exception as e:
        return f"Error al buscar establecimientos: {str(e)}"


@mcp.tool()
async def obtener_coordenadas_establecimientos(
    termino: str,
    limite: int = 5,
    latitud: Optional[float] = None,
    longitud: Optional[float] = None,
    radio: int = 250
) -> str:
    """
    Obtiene las coordenadas geográficas de establecimientos.
    Útil cuando necesitas ubicaciones exactas para mapas o análisis espacial.
    
    Args:
        termino: Nombre o tipo de establecimiento a buscar
        limite: Número máximo de resultados (default: 5)
        latitud: Latitud del centro de búsqueda (opcional)
        longitud: Longitud del centro de búsqueda (opcional)
        radio: Radio de búsqueda en metros (default: 250)
    """
    try:
        resultados = await denue_client.buscar_establecimientos(
            termino=termino,
            latitud=latitud,
            longitud=longitud,
            radio=radio
        )
        
        if isinstance(resultados, list) and len(resultados) > 0:
            texto = f"## Coordenadas de establecimientos: {termino}\n\n"
            
            if latitud and longitud:
                texto += f"**Búsqueda centrada en:** {latitud}, {longitud} (radio: {radio}m)\n\n"
            
            texto += f"**Total encontrados:** {len(resultados)}\n"
            texto += f"**Mostrando:** {min(limite, len(resultados))}\n\n"
            
            for i, est in enumerate(resultados[:limite], 1):
                nombre = est.get('Nombre', est.get('Razon_social', 'Sin nombre'))
                lat = est.get('Latitud', 'N/A')
                lon = est.get('Longitud', 'N/A')
                calle = est.get('Calle', '')
                num_ext = est.get('Num_Exterior', '')
                colonia = est.get('Colonia', '')
                
                direccion_completa = f"{calle} {num_ext}".strip()
                if colonia:
                    direccion_completa += f", {colonia}"
                
                texto += f"### {i}. {nombre}\n"
                if direccion_completa:
                    texto += f"   **Dirección:** {direccion_completa}\n"
                texto += f"   **Latitud:** {lat}\n"
                texto += f"   **Longitud:** {lon}\n"
                if lat != 'N/A' and lon != 'N/A':
                    texto += f"   **Coordenadas:** `{lat},{lon}`\n"
                texto += "\n"
            
            if len(resultados) > limite:
                texto += f"\n_(Hay {len(resultados) - limite} establecimientos más. Ajusta el parámetro 'limite' para ver más)_"
            
            return texto
        else:
            return f"No se encontraron establecimientos con el término '{termino}'"
            
    except Exception as e:
        return f"Error al obtener coordenadas: {str(e)}"


@mcp.tool()
async def buscar_area_act(
    entidad: str = "31",
    municipio: str = "0",
    nombre: str = "0",
    clase: str = "0",
    registro_inicial: int = 1,
    registro_final: int = 10
) -> str:
    """
    Búsqueda avanzada de establecimientos con información detallada incluyendo AGEB y Manzana.
    Este método proporciona más campos que buscar_establecimientos(), ideal para análisis geográfico detallado.
    
    Args:
        entidad: Código de entidad federativa (ej: "31" para Yucatán, "0" para todas)
        municipio: Código de municipio (ej: "050" para Mérida, "0" para todos)
        nombre: Nombre del establecimiento (ej: "OXXO", "0" para todos)
        clase: Código de clase de actividad económica (ej: "462112" para minisupers, "0" para todas)
        registro_inicial: Número de registro inicial (default: 1)
        registro_final: Número de registro final (default: 10, máx: 1000)
    
    Campos adicionales que incluye:
        - AGEB (Área Geoestadística Básica)
        - Manzana
        - Edificio
        - Clasificación económica completa (Sector, Subsector, Rama, Subrama)
        - Tipo de asentamiento
        - Fecha de alta
    
    Ejemplos:
        - Todos los OXXO en Yucatán: entidad="31", nombre="OXXO"
        - Restaurantes en Mérida: entidad="31", municipio="050", clase="722"
        - Minisupers en Yucatán: entidad="31", clase="462112"
    """
    try:
        resultados = await denue_client.buscar_area_act(
            entidad=entidad,
            municipio=municipio,
            nombre=nombre,
            clase=clase,
            registro_inicial=registro_inicial,
            registro_final=registro_final
        )
        
        if isinstance(resultados, list) and len(resultados) > 0:
            texto = f"## Búsqueda Detallada de Establecimientos\n\n"
            
            # Configuración de búsqueda
            if entidad != "0":
                estado_nombre = DENUEConfig.ENTIDADES.get(entidad, f"Entidad {entidad}")
                texto += f"**Entidad:** {estado_nombre}\n"
            if municipio != "0":
                texto += f"**Municipio:** {municipio}\n"
            if nombre != "0":
                texto += f"**Nombre:** {nombre}\n"
            if clase != "0":
                texto += f"**Clase económica:** {clase}\n"
            
            texto += f"**Total encontrados:** {len(resultados)}\n\n"
            texto += "---\n\n"
            
            # Mostrar establecimientos con información detallada
            for i, est in enumerate(resultados[:registro_final], 1):
                nombre_est = est.get('Nombre', est.get('Razon_social', 'Sin nombre'))
                
                texto += f"### {i}. {nombre_est}\n"
                texto += f"**Actividad:** {est.get('Clase_actividad', 'N/A')}\n"
                texto += f"**Dirección:** {est.get('Calle', '')} {est.get('Num_Exterior', '')} {est.get('Num_Interior', '')}\n"
                texto += f"**Colonia:** {est.get('Colonia', 'N/A')}\n"
                texto += f"**CP:** {est.get('CP', 'N/A')}\n"
                
                # Información geográfica detallada
                ageb = est.get('AGEB', 'N/A')
                manzana = est.get('Manzana', 'N/A')
                if ageb != 'N/A' or manzana != 'N/A':
                    texto += f"\n**Información Geográfica:**\n"
                    if ageb != 'N/A':
                        texto += f"  - AGEB: {ageb}\n"
                    if manzana != 'N/A':
                        texto += f"  - Manzana: {manzana}\n"
                
                # Coordenadas
                lat = est.get('Latitud', 'N/A')
                lon = est.get('Longitud', 'N/A')
                if lat != 'N/A' and lon != 'N/A':
                    texto += f"**Coordenadas:** {lat}, {lon}\n"
                
                # Clasificación económica
                sector = est.get('SECTOR_ACTIVIDAD_ID', 'N/A')
                subsector = est.get('SUBSECTOR_ACTIVIDAD_ID', 'N/A')
                rama = est.get('RAMA_ACTIVIDAD_ID', 'N/A')
                if sector != 'N/A' or subsector != 'N/A' or rama != 'N/A':
                    texto += f"\n**Clasificación Económica:**\n"
                    if sector != 'N/A':
                        texto += f"  - Sector: {sector}\n"
                    if subsector != 'N/A':
                        texto += f"  - Subsector: {subsector}\n"
                    if rama != 'N/A':
                        texto += f"  - Rama: {rama}\n"
                
                # Información adicional
                if est.get('Telefono'):
                    texto += f"**Teléfono:** {est.get('Telefono')}\n"
                if est.get('Correo_e'):
                    texto += f"**Email:** {est.get('Correo_e')}\n"
                if est.get('Sitio_internet'):
                    texto += f"**Sitio web:** {est.get('Sitio_internet')}\n"
                
                texto += "\n"
            
            if len(resultados) > registro_final:
                texto += f"\n_(Mostrando {registro_final} de {len(resultados)} resultados. Ajusta 'registro_final' para ver más)_"
            
            return texto
        else:
            return "No se encontraron establecimientos con los criterios especificados."
            
    except Exception as e:
        return f"Error al buscar establecimientos: {str(e)}"


@mcp.tool()
async def cuantificar_establecimientos(
    actividad_economica: str = "0",
    area_geografica: str = "0",
    estrato: str = "0"
) -> str:
    """
    Cuantifica establecimientos por actividad económica, área geográfica y tamaño (estrato).
    Útil para análisis estadísticos y comparativos sin recuperar datos individuales.
    
    Args:
        actividad_economica: Código de actividad económica (0=todas)
            - "46": Sector comercio al por menor
            - "464": Subsector comercio al por menor de abarrotes
            - "4641": Rama específica
            - "111,112": Múltiples códigos separados por coma
        area_geografica: Código de área (0=todo el país)
            - "31": Estado de Yucatán
            - "31050": Municipio de Mérida
            - "310500001": Localidad específica
            - "01001,01005": Múltiples áreas separadas por coma
        estrato: Tamaño por personal ocupado (0=todos)
            - "1": 0-5 personas
            - "2": 6-10 personas
            - "3": 11-30 personas
            - "4": 31-50 personas
            - "5": 51-100 personas
            - "6": 101-250 personas
            - "7": 251+ personas
    
    Ejemplos:
        - Todos los comercios en Yucatán: actividad="46", area="31"
        - OXXO en Mérida pequeños: actividad="462112", area="31050", estrato="1"
        - Restaurantes en todo México: actividad="722", area="0"
    """
    try:
        resultados = await denue_client.cuantificar(
            actividad_economica=actividad_economica,
            area_geografica=area_geografica,
            estrato=estrato
        )
        
        if isinstance(resultados, list) and len(resultados) > 0:
            # Crear diccionario para nombres de actividades comunes
            nombres_actividad = {
                "46": "Comercio al por menor",
                "462": "Comercio al por menor en tiendas de abarrotes",
                "464": "Comercio al por menor de alimentos",
                "722": "Servicios de preparación de alimentos",
                "111": "Agricultura",
                "112": "Ganadería"
            }
            
            texto = "## Cuantificación de Establecimientos\n\n"
            
            # Configuración de búsqueda
            if actividad_economica != "0":
                act_nombre = nombres_actividad.get(actividad_economica, f"Actividad {actividad_economica}")
                texto += f"**Actividad:** {act_nombre} ({actividad_economica})\n"
            else:
                texto += "**Actividad:** Todas\n"
            
            if area_geografica != "0":
                area_len = len(area_geografica.replace(",", ""))
                if area_len == 2:
                    estado_nombre = DENUEConfig.ENTIDADES.get(area_geografica, f"Estado {area_geografica}")
                    texto += f"**Área:** {estado_nombre}\n"
                else:
                    texto += f"**Área:** {area_geografica}\n"
            else:
                texto += "**Área:** Todo México\n"
            
            if estrato != "0":
                estratos = {
                    "1": "0-5 empleados",
                    "2": "6-10 empleados",
                    "3": "11-30 empleados",
                    "4": "31-50 empleados",
                    "5": "51-100 empleados",
                    "6": "101-250 empleados",
                    "7": "251+ empleados"
                }
                texto += f"**Estrato:** {estratos.get(estrato, estrato)}\n"
            else:
                texto += "**Estrato:** Todos los tamaños\n"
            
            texto += "\n---\n\n"
            
            # Calcular total
            total_general = sum(int(r.get('Total', 0)) for r in resultados)
            texto += f"**Total de establecimientos:** {total_general:,}\n\n"
            
            # Desglose por resultado
            if len(resultados) > 1:
                texto += "### Desglose:\n\n"
                for r in resultados[:20]:  # Limitar a 20 resultados
                    ae = r.get('AE', 'N/A')
                    ag = r.get('AG', 'N/A')
                    total = r.get('Total', 0)
                    
                    # Intentar obtener nombre del área
                    if len(ag) == 2:
                        area_nombre = DENUEConfig.ENTIDADES.get(ag, f"Área {ag}")
                    else:
                        area_nombre = f"Área {ag}"
                    
                    texto += f"- **{area_nombre}** (Act: {ae}): {int(total):,} establecimientos\n"
                
                if len(resultados) > 20:
                    texto += f"\n_(Mostrando 20 de {len(resultados)} resultados)_\n"
            
            return texto
        else:
            return "No se encontraron establecimientos con los criterios especificados."
            
    except Exception as e:
        return f"Error al cuantificar establecimientos: {str(e)}"


def main():
    """Punto de entrada para el servidor"""
    mcp.run()


if __name__ == "__main__":
    main()
