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
- ✅ **Base de datos DENUE** - Más de 5 millones de establecimientos económicos
- ✅ **Búsquedas geográficas avanzadas** - Por coordenadas, estados, municipios
- ✅ **Análisis comparativos** - Entre estados y regiones
- ✅ **Datos históricos** - Series temporales completas
- ✅ **Optimizado para IA** - Respuestas estructuradas para procesamiento por LLMs

---

## 🏗️ Arquitectura del MCP

### Esquema de Funcionamiento

```
┌─────────────────┐    ┌───────────────────┐    ┌─────────────────┐
│                 │    │                   │    │                 │
│  Claude Desktop │◄──►│   MCP Server      │◄──►│   APIs INEGI    │
│                 │    │   (inegi_mcp)     │    │                 │
└─────────────────┘    └───────────────────┘    └─────────────────┘
         ▲                         │                       │
         │                         ▼                       ▼
    ┌─────────┐            ┌──────────────┐      ┌─────────────────┐
    │  User   │            │   Tools      │      │ • Indicadores   │
    │ Request │            │ & Clients    │      │ • DENUE         │
    └─────────┘            └──────────────┘      │ • Geoestadística│
                                   │              └─────────────────┘
                                   ▼
                           ┌──────────────┐
                           │ Structured   │
                           │ Response     │
                           └──────────────┘
```

### Componentes Principales

#### 🔧 **Clients** (`src/inegi_mcp/clients/`)
- **`indicadores_client.py`** - Cliente para API de Indicadores Económicos
- **`denue_client.py`** - Cliente para API del DENUE

#### 🛠️ **Tools** (`src/inegi_mcp/tools/`)
- **`indicadores_tools.py`** - Herramientas para datos estadísticos
- **`denue_tools.py`** - Herramientas para establecimientos económicos

#### ⚙️ **Server** (`src/inegi_mcp/server.py`)
- Coordinador principal que registra todas las herramientas
- Interfaz MCP estándar para comunicación con Claude Desktop

---

## ✨ Funcionalidades

### 📊 **Indicadores Económicos y Demográficos**
- Búsqueda en catálogo básico (~30 indicadores principales)
- **🆕 Búsqueda en catálogo completo** - Miles de indicadores disponibles
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
"Claude, ¿cuál es el PIB actual de Yucatán?"

"Compara la población entre Yucatán, Nuevo León y CDMX"

"Busca todos los OXXO en Mérida con sus coordenadas"

"¿Cuántos restaurantes hay en el centro de Mérida?"

"Dame la serie histórica de inflación en México"
```

---

## 📖 Ejemplos Prácticos

### 📊 **Análisis Económico**
```python
# Obtener PIB de México (serie temporal)
obtener_serie_temporal(indicador_id="381016", historica=True)

# Comparar PIB entre estados
comparar_estados(indicador_id="381016", estados=["31", "19", "09"])
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
| `buscar_indicadores` | Busca indicadores en catálogo básico | Búsquedas rápidas de indicadores comunes |
| `buscar_catalogo_completo` | 🆕 Busca en catálogo completo (miles) | Análisis detallados, investigación específica |
| `obtener_serie_temporal` | Obtiene datos históricos | Análisis de tendencias, proyecciones |
| `comparar_estados` | Compara indicador entre estados | Estudios regionales, benchmarking |
| `listar_indicadores_disponibles` | Lista indicadores del catálogo básico | Exploración inicial, referencia rápida |

### 🏢 **Herramientas de Establecimientos**

| Función | Descripción | Casos de Uso |
|---------|-------------|--------------|
| `buscar_establecimientos` | Búsqueda básica por término | Consultas generales |
| `buscar_area_act` | 🆕 Búsqueda avanzada con metadatos | Análisis detallados, estudios de mercado |
| `cuantificar_establecimientos` | Estadísticas por sector/región | Análisis cuantitativos, estudios sectoriales |
| `obtener_coordenadas_establecimientos` | Ubicaciones geográficas precisas | Mapeo, análisis espacial |

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

### 🔍 **Indicadores Comunes**
| Indicador | ID | Descripción |
|-----------|----|-----------| 
| Población total | `1002000001` | Población total por entidad |
| PIB | `381016` | Producto Interno Bruto |
| Tasa de desempleo | `444612` | Porcentaje de desempleo |
| INPC | `216906` | Índice Nacional de Precios al Consumidor |
| Inflación anual | `216668` | Tasa de inflación anualizada |

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

### 💬 **¿Necesitas ayuda?**
- Describe tu problema con el máximo detalle posible
- Incluye mensajes de error completos
- Menciona tu sistema operativo y versión de Python

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Consulta [LICENSE](LICENSE) para más detalles.

---

## ⚡ Disclaimer

Este es un proyecto independiente y **no está oficialmente afiliado con el INEGI**. Los datos son proporcionados por las APIs públicas oficiales del INEGI.

---

## 🎯 Roadmap

### 🚀 **Próximas Funcionalidades**
- [ ] Caché inteligente para optimizar consultas
- [ ] Exportación a diferentes formatos (Excel, CSV, JSON)
- [ ] Visualizaciones automáticas de datos
- [ ] Integración con más APIs gubernamentales mexicanas
- [ ] Dashboard web interactivo
- [ ] API REST complementaria

### 🔧 **Mejoras Técnicas**
- [ ] Tests automatizados
- [ ] CI/CD pipeline
- [ ] Documentación interactiva (OpenAPI)
- [ ] Monitoring y logging avanzado
- [ ] Rate limiting inteligente

---

**📊 Desarrollado con ❤️ para facilitar el acceso a datos estadísticos de México**

**👨‍💻 Autor:** Guillermo Chávez  
**🔗 Repositorio:** [gchavez83/inegi-mcp-server](https://github.com/gchavez83/inegi-mcp-server)  
**📧 Contacto:** A través de GitHub Issues
