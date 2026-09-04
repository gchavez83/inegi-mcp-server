# 🇲🇽 INEGI MCP Server

**Servidor MCP (Model Context Protocol) completo para acceder a las APIs del INEGI desde Claude Desktop**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![INEGI](https://img.shields.io/badge/INEGI-APIs-red.svg)](https://www.inegi.org.mx/)

---

## 📋 Tabla de Contenidos

- [🎯 Descripción](#-descripción)
- [🏗️ Arquitectura del MCP](#%EF%B8%8F-arquitectura-del-mcp)
- [✨ Funcionalidades](#-funcionalidades)
- [📊 APIs Disponibles](#-apis-disponibles)
- [⚡ Instalación Rápida](#-instalación-rápida)
- [🔧 Configuración](#-configuración)
- [🚀 Uso](#-uso)
- [📖 Ejemplos Prácticos](#-ejemplos-prácticos)
- [🔍 Referencia de Funciones](#-referencia-de-funciones)
- [☁️ Deployment en Azure](#%EF%B8%8F-deployment-en-azure)
- [🤝 Contribuir](#-contribuir)

---

## 🎯 Descripción

Este servidor MCP proporciona acceso completo y optimizado a las APIs oficiales del INEGI (Instituto Nacional de Estadística y Geografía de México), permitiendo a Claude Desktop consultar datos estadísticos, económicos, demográficos y de establecimientos comerciales de México.

### 🌟 Características Principales

- ✅ **Acceso completo al catálogo INEGI** - Miles de indicadores económicos y demográficos
- ✅ **Búsqueda semántica en el Banco de Indicadores (BIE)** - Mismo endpoint que el portal web del INEGI
- ✅ **Detección automática de nivel geográfico** - Nacional, estatal o municipal según disponibilidad
- ✅ **Base de datos DENUE** - Más de 5 millones de establecimientos económicos
- ✅ **Búsquedas geográficas avanzadas** - Por coordenadas, estados, municipios
- ✅ **Análisis comparativos** - Entre estados y regiones
- ✅ **Datos históricos** - Series temporales completas
- ✅ **Optimizado para IA** - Respuestas estructuradas para procesamiento por LLMs

---

## 🏗️ Arquitectura del MCP

### Esquema de Funcionamiento

```
┌─────────────────┐    ┌───────────────────┐    ┌──────────────────────┐
│                 │    │                   │    │                      │
│  Claude Desktop │◄──►│   MCP Server      │◄──►│   APIs INEGI         │
│                 │    │   (inegi_mcp)     │    │                      │
└─────────────────┘    └───────────────────┘    └──────────────────────┘
         ▲                         │                         │
         │                         ▼                         ▼
    ┌─────────┐            ┌──────────────┐      ┌───────────────────────┐
    │  User   │            │   Tools      │      │ • Indicadores (BISE)  │
    │ Request │            │ & Clients    │      │ • BIE (buscadorcore)  │
    └─────────┘            └──────────────┘      │ • DENUE               │
                                   │              └───────────────────────┘
                                   ▼
                           ┌──────────────┐
                           │ Structured   │
                           │ Response     │
                           └──────────────┘
```

### Componentes Principales

#### 🔧 **Clients** (`src/inegi_mcp/clients/`)
- **`indicadores_client.py`** - Cliente para API de Indicadores Económicos y búsqueda BIE
- **`denue_client.py`** - Cliente para API del DENUE

#### ⚙️ **Server** (`src/inegi_mcp/server.py`)
- Coordinador principal que registra todas las herramientas
- Interfaz MCP estándar para comunicación con Claude Desktop

---

## ✨ Funcionalidades

### 📊 **Indicadores Económicos y Demográficos**
- Búsqueda en catálogo básico (~60 indicadores principales validados)
- **Búsqueda en catálogo completo** - Miles de indicadores disponibles
- **🆕 Búsqueda semántica en el Banco de Indicadores (BIE)** - PIB, IGAE, exportaciones, etc.
- **🆕 Obtención inteligente de indicadores** - Detecta nivel geográfico automáticamente y hace fallback nacional
- Series temporales históricas completas
- Comparaciones entre estados de México
- Datos a nivel nacional, estatal y municipal

### 🏪 **Directorio de Establecimientos (DENUE)**
- **Base de datos completa** - Más de 5 millones de establecimientos
- Búsqueda por nombre, giro o actividad económica
- **Búsquedas geográficas avanzadas** - Por coordenadas y radio
- **Clasificación detallada** - AGEB, Manzana, Sector económico
- **Análisis cuantitativo** - Estadísticas por sector y región
- **Metadatos completos** - Direcciones, contactos, coordenadas

---

## 📊 APIs Disponibles

### 🎯 API de Indicadores
**Base:** `https://www.inegi.org.mx/app/api/indicadores/`
- **Cobertura:** Nacional, Estatal, Municipal
- **Datos:** PIB, población, empleo, inflación, etc.
- **Periodicidad:** Anual, trimestral, mensual

### 🔍 API Buscador BIE
**Base:** `https://www.inegi.org.mx/app/api/buscadorcore/v1/busquedaBancoIndicadores/`
- **Tipo:** POST con búsqueda semántica por ranking
- **Cobertura:** Banco de Indicadores Económicos completo (BIE)
- **Retorna:** ID, título, unidad, frecuencia, períodos disponibles y nivel geográfico

### 🏢 API DENUE
**Base:** `https://www.inegi.org.mx/app/api/denue/`
- **Cobertura:** Todo México
- **Registros:** 5+ millones de establecimientos
- **Clasificación:** SCIAN (Sistema de Clasificación Industrial)

---

## ⚡ Instalación Rápida

### 1. **Clonar el Repositorio**
```bash
git clone https://github.com/gchavez83/inegi-mcp-server.git
cd inegi-mcp-server
```

### 2. **Instalar Dependencias**
```bash
pip install -e .
```

### 3. **Configurar Tokens**
```bash
# Copiar plantilla de configuración
cp .env.example .env

# Editar y agregar tus tokens del INEGI
# INEGI_INDICADORES_TOKEN=tu-token-indicadores-aqui
# INEGI_DENUE_TOKEN=tu-token-denue-aqui
```

### 4. **Obtener Tokens del INEGI**
Visita: [https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify](https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify)

---

## 🔧 Configuración

### Claude Desktop Configuration

#### **Windows**
```bash
%APPDATA%\Claude\claude_desktop_config.json
```

#### **macOS/Linux**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Archivo de Configuración
```json
{
  "mcpServers": {
    "inegi": {
      "command": "python",
      "args": ["-m", "inegi_mcp.server"],
      "env": {
        "INEGI_INDICADORES_TOKEN": "tu-token-indicadores-aqui",
        "INEGI_DENUE_TOKEN": "tu-token-denue-aqui"
      }
    }
  }
}
```

---

## 🚀 Uso

Una vez configurado, puedes hacer consultas directas a Claude Desktop:

### 💬 Ejemplos de Consultas
```
"Claude, ¿cuál es el PIB actual de México?"

"Busca indicadores del IGAE en el Banco de Indicadores"

"Compara la población entre Yucatán, Nuevo León y CDMX"

"Busca todos los OXXO en Mérida con sus coordenadas"

"¿Cuántos restaurantes hay en el centro de Mérida?"

"Dame la serie histórica de exportaciones en México"

"Obtén los datos del indicador 510104 para Yucatán"
```

---

## 📖 Ejemplos Prácticos

### 📊 **Análisis Económico — Flujo recomendado con BIE**
```python
# 1. Buscar indicadores de PIB en el Banco de Indicadores
buscar_banco_indicadores(busqueda="PIB")
# → Retorna lista con IDs reales: 510104, 524388, 527794, etc.

# 2. Obtener la serie del indicador encontrado (con detección geográfica automática)
obtener_indicador_inteligente(indicador_id="510104", codigo_geo="31")
# → Detecta nivel nacional (desglose=1), retorna serie completa

# 3. Para indicadores con cobertura estatal, intenta Yucatán automáticamente
obtener_indicador_inteligente(indicador_id="6207061373", codigo_geo="31")
# → Si hay datos estatales los trae; si no, hace fallback a nacional
#   (6207061373 = ITAEE actividades terciarias; 6207061369 es actividades primarias)

# 4. Pedir un tramo concreto de la serie (las observaciones salen en orden cronológico
#    y, si hay más de `limite`, se muestran las MÁS RECIENTES)
obtener_indicador_inteligente(indicador_id="6207123163", codigo_geo="00", desde="2024", hasta="2025/12")
obtener_serie_temporal(indicador_id="716074", desde="2025", limite=0)   # limite=0 = sin recorte
```

### 🧭 **Series de turismo validadas (septiembre 2026)**
| Serie | ID | Cobertura | Último dato | Nota |
|---|---|---|---|---|
| Ingresos hoteles 7211 (EMS) | `716074` | Nacional | 2026/06 | Índice base 2018=100 |
| Personal ocupado hoteles 7211 (EMS) | `716218` | Nacional | 2026/06 | Índice base 2018=100 |
| Ingresos sector 72 Yucatán (EMS) | `717592` | Estatal (31) | 2024/02 | Índice base 2018=100 |
| Personal ocupado sector 72 Yucatán (EMS) | `717768` | Estatal (31) | 2024/02 | Índice base 2018=100 |
| Turistas de internación vía aérea (EVI) | `6207123163` | Nacional | 2025/12 | Entradas |
| Gasto turistas de internación vía aérea (EVI) | `6207123170` | Nacional | 2025/12 | Dólares |
| Consumo turístico receptivo / interno (CSTM 2018) | `6207135895` / `6207135900` | Nacional | 2024 | Porcentaje |
| ITAT índice / variación | `497685` / `497689` | Nacional | 2023/T1 | ⚠️ base 2013, serie cerrada |
| PIBE sector 72 Yucatán | `489207` | Estatal | 2021 | ⚠️ base 2013, serie cerrada |
| ITAEE terciarias Yucatán | `6207061373` | Estatal | 2023/T1 | ⚠️ base 2013, serie cerrada |

Las series marcadas ⚠️ existen con base 2018 bajo otro ID que el buscador de la API no
localiza; hay que tomarlo del Banco de Información Económica en el portal de INEGI.

### 🛠️ **Correcciones de septiembre 2026**
- `obtener_indicador_inteligente` ya no construye la URL a mano con el banco fijo `BIE-BISE`
  (causa de los HTTP 400 en series económicas): usa el cliente y reintenta BIE → BISE → BIE-BISE.
- Las observaciones se ordenan cronológicamente antes de recortar. Antes `obs[-80:]` tomaba
  las 80 **más antiguas** porque INEGI entrega la serie de nueva a vieja.
- Nuevos parámetros `desde`, `hasta` y `limite` en `obtener_serie_temporal` y
  `obtener_indicador_inteligente`.
- Unidades y frecuencias decodificadas con CL_UNIT / CL_FREQ (con caché) en lugar de códigos
  numéricos (1051 → «Índice base 2018=100», 8 → «Mensual»).
- Los metadatos del catálogo solo se usan si el INDICADOR coincide con el ID pedido.
- Los buscadores usan `area_geo="null"` por defecto (cualquier otro valor vacía la respuesta) y
  reintentan sin filtro cuando se pidió uno. Muestran la ruta temática completa y avisan cuando
  una serie tiene base 2013 y su último dato es anterior a 2024.
- `comparar_estados` toma el último dato real (ordenado), no el último de la lista.

### 📈 **Búsqueda de indicadores de precios / INPC**
```python
# El BIE no reconoce 'inflacion' directamente — usar el término correcto
buscar_banco_indicadores(busqueda="precios consumidor")
# → Retorna UMA Diario/Mensual/Anual base INPC (IDs 539260-539262)

buscar_banco_indicadores(busqueda="indice precios")
# → Mismos resultados
```

### 📊 **Análisis Económico — Catálogo básico**
```python
# Obtener PIB de México (serie temporal con IDs del catálogo básico)
obtener_serie_temporal(indicador_id="510104", historica=True)

# Comparar tasa de desocupación entre estados
comparar_estados(indicador_id="444612", estados=["31", "19", "09"])
```

### 🏪 **Análisis de Mercado**
```python
# Buscar establecimientos por ubicación
buscar_area_act(entidad="31", municipio="050", nombre="OXXO")

# Cuantificar establecimientos por sector
cuantificar_establecimientos(actividad_economica="462112", area_geografica="31")
```

### 🌎 **Análisis Geográfico**
```python
# Coordenadas de establecimientos
obtener_coordenadas_establecimientos(termino="restaurantes", limite=10)
```

---

## 🔍 Referencia de Funciones

### 📈 **Herramientas de Indicadores**

| Función | Descripción | Casos de Uso |
|---------|-------------|--------------|
| `buscar_indicadores` | Busca en catálogo local curado (~60 IDs) | Indicadores comunes validados |
| `buscar_catalogo_cl` | Búsqueda en CL_INDICATOR oficial (BISE/BIE) | Exploración por banco de datos |
| `buscar_catalogo_completo` | Busca en catálogo completo vía buscadorcore | Análisis detallados, investigación |
| `buscar_banco_indicadores` | 🆕 Búsqueda semántica directa en BIE (mismo endpoint que el portal INEGI) | **PIB, IGAE, exportaciones, balanza** |
| `obtener_serie_temporal` | Obtiene datos históricos por ID | Análisis de tendencias, proyecciones |
| `obtener_indicador_inteligente` | 🆕 Obtención con detección automática de nivel geográfico y fallback | **Uso general recomendado** |
| `comparar_estados` | Compara un indicador entre varios estados | Estudios regionales, benchmarking |
| `listar_indicadores_disponibles` | Lista el catálogo básico completo | Exploración inicial, referencia rápida |

> **💡 Flujo recomendado:** `buscar_banco_indicadores` → obtener ID → `obtener_indicador_inteligente`

### 🏢 **Herramientas de Establecimientos**

| Función | Descripción | Casos de Uso |
|---------|-------------|--------------|
| `buscar_establecimientos` | Búsqueda básica por término y radio | Consultas generales |
| `buscar_area_act` | Búsqueda avanzada con AGEB y Manzana | Análisis detallados, estudios de mercado |
| `cuantificar_establecimientos` | Estadísticas por sector/región | Análisis cuantitativos, estudios sectoriales |
| `obtener_coordenadas_establecimientos` | Ubicaciones geográficas precisas | Mapeo, análisis espacial |

---

## 🗺️ Términos Validados en el BIE

El endpoint de búsqueda del Banco de Indicadores (BIE) usa indexación por título exacto. Los siguientes términos han sido validados y devuelven resultados:

| Categoría | Términos que funcionan | Términos que NO funcionan |
|-----------|----------------------|--------------------------|
| PIB | `PIB`, `producto interno`, `interno bruto` | ~~`pib nacional`~~ |
| Actividad | `IGAE`, `igae`, `actividad economica`, `crecimiento` | — |
| Precios | `precios consumidor`, `indice precios` | ~~`inflacion`~~, ~~`INPC`~~ |
| Comercio | `exportaciones`, `balanza`, `industria` | — |
| Empleo | `ocupacion`, `salario` | ~~`desempleo`~~ |

---

## 🔑 Indicadores Clave Validados

| Indicador | ID | Descripción |
|-----------|----|-----------| 
| PIB total nacional | `510104` | Millones de pesos corrientes, trimestral 1993-2023 |
| PIB a precios básicos | `524388` | Cuentas nacionales |
| IGAE — Variación anual | `491656` | Indicador Global Actividad Económica |
| IGAE — Con petróleo | `491659` | Serie mensual |
| IGAE — Sin petróleo | `491660` | Serie mensual |
| UMA Diario (base INPC) | `539260` | Anual 2015-2026 |
| UMA Mensual (base INPC) | `539261` | Anual 2015-2026 |
| Tasa de desocupación | `444612` | Mensual, nacional |
| Exportaciones anuales | `6207095719` | Por entidad federativa |
| Balanza Comercial | `6204198565` | Mercancías de México |
| ITAEE Yucatán | `6207061369` | Actividad económica estatal |
| Población total | `1002000001` | Por entidad federativa |
| Nacimientos | `1002000030` | Registros vitales |
| Matrimonios | `1002000038` | Registros vitales |

---

## ☁️ Deployment en Azure

Para implementación en producción con Azure y manejo seguro de variables de entorno, consulta la guía completa:

👉 **[AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)**

---

## 🤝 Contribuir

### Proceso de Contribución
1. **Fork** el repositorio
2. **Crea una rama** para tu funcionalidad
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```
3. **Commit** tus cambios
   ```bash
   git commit -am 'Añade nueva funcionalidad'
   ```
4. **Push** a la rama
   ```bash
   git push origin feature/nueva-funcionalidad
   ```
5. **Abre un Pull Request**

### Ideas para Contribuir
- 🔧 Nuevas herramientas de análisis
- 📊 Visualizaciones de datos
- 🌐 APIs adicionales del INEGI
- 📚 Documentación y ejemplos
- 🧪 Tests y validaciones

---

## 📚 Recursos

### 📖 **Documentación Oficial**
- [API Indicadores INEGI](https://www.inegi.org.mx/servicios/api_indicadores.html)
- [API DENUE](https://www.inegi.org.mx/servicios/api_denue.html)
- [Banco de Indicadores INEGI](https://www.inegi.org.mx/app/indicadores/)
- [Model Context Protocol](https://modelcontextprotocol.io)

---

## 🔒 Seguridad

### ⚠️ **Mejores Prácticas**
- ✅ **NUNCA** compartas tus tokens en repositorios públicos
- ✅ Usa variables de entorno o Azure Key Vault para tokens
- ✅ Revisa `.gitignore` para asegurar que `.env` no se suba
- ✅ Rota tus tokens regularmente
- ✅ Monitorea el uso de tus APIs

---

## ❓ Soporte

### 🐛 **¿Encontraste un problema?**
- [Abre un issue en GitHub](https://github.com/gchavez83/inegi-mcp-server/issues)
- Consulta la [documentación oficial del INEGI](https://www.inegi.org.mx/servicios/api.html)
- Revisa la [guía de deployment en Azure](AZURE_DEPLOYMENT.md)

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Consulta [LICENSE](LICENSE) para más detalles.

---

## ⚡ Disclaimer

Este es un proyecto independiente y **no está oficialmente afiliado con el INEGI**. Los datos son proporcionados por las APIs públicas oficiales del INEGI.

---

## 🎯 Roadmap

### ✅ **Completado**
- [x] Búsqueda semántica en Banco de Indicadores BIE (`buscar_banco_indicadores`)
- [x] Obtención inteligente con detección geográfica automática (`obtener_indicador_inteligente`)
- [x] Catálogo de IDs validados via `diagnostico_bie2.py`
- [x] Fix `metodoBusqueda=1` y `orderby=RANKING` en cliente BIE
- [x] Tabla de sinónimos documentada (términos que el BIE reconoce vs. no reconoce)

### 🚀 **Próximas Funcionalidades**
- [ ] Caché inteligente para optimizar consultas repetidas
- [ ] Exportación a diferentes formatos (Excel, CSV, JSON)
- [ ] Soporte para consultas estatales con IDs del ITAEE
- [ ] Integración con más APIs gubernamentales mexicanas
- [ ] Tests automatizados con IDs validados

---

**📊 Desarrollado con ❤️ para facilitar el acceso a datos estadísticos de México**

**👨‍💻 Autor:** Guillermo Chávez  
**🔗 Repositorio:** [gchavez83/inegi-mcp-server](https://github.com/gchavez83/inegi-mcp-server)  
**📧 Contacto:** A través de GitHub Issues
