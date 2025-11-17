# INEGI MCP Server

Servidor MCP (Model Context Protocol) para acceder a las APIs del INEGI desde Claude Desktop.

## Características

Este servidor proporciona acceso a dos APIs principales del INEGI:

### API de Indicadores
- Búsqueda de indicadores económicos y demográficos
- Obtención de series temporales (PIB, población, inflación, etc.)
- Comparación de indicadores entre estados
- Consulta de metadatos detallados

### API del DENUE
- Búsqueda de establecimientos económicos
- Más de 5 millones de establecimientos
- Búsqueda por ubicación geográfica
- Estadísticas por sector y región

## Requisitos

- Python 3.10 o superior
- Tokens de la API del INEGI (obtener en: https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify)

## Instalación Local

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/inegi-mcp-server.git
cd inegi-mcp-server
```

### 2. Instalar dependencias

```bash
pip install -e .
```

### 3. Configurar tokens

Copia el archivo `.env.example` a `.env` y añade tus tokens:

```bash
cp .env.example .env
```

Edita `.env` y añade tus tokens:

```env
INEGI_INDICADORES_TOKEN=tu-token-indicadores-aqui
INEGI_DENUE_TOKEN=tu-token-denue-aqui
```

## Configuración en Claude Desktop

Edita el archivo de configuración de Claude Desktop:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Añade la configuración del servidor:

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

## Deployment en Azure

Para desplegar este servidor en Azure y usar variables de entorno seguras, consulta la guía completa: [AZURE_DEPLOYMENT.md](./AZURE_DEPLOYMENT.md)

## Herramientas Disponibles

### Indicadores

| Herramienta | Descripción |
|------------|-------------|
| `buscar_indicadores` | Busca indicadores por palabra clave |
| `obtener_serie_temporal` | Obtiene datos de un indicador |
| `comparar_estados` | Compara indicador entre estados |
| `listar_indicadores_disponibles` | Lista indicadores del catálogo |

### DENUE

| Herramienta | Descripción |
|------------|-------------|
| `buscar_establecimientos` | Busca establecimientos por término |
| `buscar_por_ubicacion` | Busca por coordenadas y radio |

## Ejemplos de Uso

### Consultar PIB de México
```
Claude, ¿puedes obtenerme la serie temporal del PIB de México?
```

### Comparar indicadores entre estados
```
Compara el PIB entre Yucatán, Nuevo León y Ciudad de México
```

### Buscar restaurantes
```
Busca restaurantes cerca de las coordenadas 20.9674, -89.5926 (Mérida)
```

### Análisis combinado
```
Dame el PIB de Yucatán y cuántos establecimientos manufactureros tiene
```

## Indicadores Comunes

- **1002000001**: Población total
- **381016**: PIB
- **444612**: Tasa de desempleo
- **216906**: INPC (Índice Nacional de Precios al Consumidor)
- **216668**: Inflación anual

## Enlaces Útiles

- [Documentación API Indicadores](https://www.inegi.org.mx/servicios/api_indicadores.html)
- [Documentación API DENUE](https://www.inegi.org.mx/servicios/api_denue.html)
- [Banco de Indicadores INEGI](https://www.inegi.org.mx/app/indicadores/)
- [Model Context Protocol](https://modelcontextprotocol.io)

## Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Haz fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añade nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## Licencia

Este proyecto es de código abierto bajo licencia MIT.

## Nota Importante

Este es un proyecto independiente y no está oficialmente afiliado con el INEGI. Los datos son proporcionados por las APIs públicas del INEGI.

## Seguridad

- **NUNCA** compartas tus tokens en repositorios públicos
- Usa variables de entorno o Azure Key Vault para tokens
- Revisa `.gitignore` para asegurar que `.env` no se suba al repositorio
- Rota tus tokens regularmente

## Soporte

Si encuentras problemas o tienes preguntas:
- Abre un issue en GitHub
- Consulta la documentación oficial del INEGI
- Revisa la guía de deployment en Azure
