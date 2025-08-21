# Sistema de Actualizaciones - Automatización de Compresión de Archivos

## Descripción

Este sistema permite mantener la aplicación actualizada automáticamente, verificando nuevas versiones desde un servidor remoto y aplicando las actualizaciones de forma segura.

## Características

### ✅ Funcionalidades Implementadas

- **Verificación Automática**: Comprueba actualizaciones al iniciar la aplicación
- **Descarga Segura**: Valida la integridad de las actualizaciones con checksums
- **Instalación Automática**: Aplica actualizaciones con respaldo automático
- **Interfaz Intuitiva**: Notificaciones y progreso visual
- **Configuración Flexible**: Opciones personalizables de actualización
- **Sistema de Respaldo**: Rollback automático en caso de errores
- **Verificación Manual**: Opción para buscar actualizaciones desde el menú

## Configuración

### Archivo config.json

La configuración se encuentra en la sección `updates` del archivo `config.json`:

```json
{
  "updates": {
    "auto_check": true,
    "auto_download": false,
    "auto_install": false,
    "check_frequency_hours": 24,
    "backup_enabled": true,
    "verify_signatures": true,
    "allow_prereleases": false,
    "update_server_url": "https://api.github.com/repos/usuario/automatizacion-compresion/releases",
    "last_check": null,
    "dismissed_versions": []
  }
}
```

### Parámetros de Configuración

| Parámetro | Descripción | Valor por Defecto |
|-----------|-------------|-------------------|
| `auto_check` | Verificar actualizaciones automáticamente | `true` |
| `auto_download` | Descargar actualizaciones automáticamente | `false` |
| `auto_install` | Instalar actualizaciones automáticamente | `false` |
| `check_frequency_hours` | Frecuencia de verificación en horas | `24` |
| `backup_enabled` | Crear respaldo antes de actualizar | `true` |
| `verify_signatures` | Verificar firmas digitales | `true` |
| `allow_prereleases` | Incluir versiones beta | `false` |
| `update_server_url` | URL del servidor de actualizaciones | GitHub API |

## Uso

### Verificación Automática

1. **Al Iniciar**: La aplicación verifica automáticamente si hay actualizaciones disponibles
2. **Notificación**: Si hay una actualización, se muestra un diálogo informativo
3. **Opciones**: El usuario puede elegir:
   - **Actualizar Ahora**: Inicia el proceso inmediatamente
   - **Más Tarde**: Pospone la actualización
   - **Omitir Versión**: Ignora esta versión específica

### Verificación Manual

1. Ir al menú **Ayuda** → **Buscar Actualizaciones**
2. La aplicación verificará inmediatamente si hay actualizaciones
3. Se mostrará el resultado de la verificación

### Configuración de Actualizaciones

1. Ir al menú **Ayuda** → **Configurar Actualizaciones**
2. Ajustar las opciones según sus preferencias:
   - Frecuencia de verificación
   - Descarga automática
   - Instalación automática
   - Opciones de respaldo
   - Versiones beta

## Proceso de Actualización

### Pasos del Proceso

1. **Verificación**: Consulta al servidor por nuevas versiones
2. **Descarga**: Descarga el archivo de actualización
3. **Validación**: Verifica la integridad del archivo
4. **Respaldo**: Crea una copia de seguridad de la versión actual
5. **Instalación**: Aplica los nuevos archivos
6. **Verificación**: Confirma que la instalación fue exitosa
7. **Limpieza**: Elimina archivos temporales

### Ventana de Progreso

Durante la actualización se muestra una ventana con:
- Barra de progreso visual
- Estado actual del proceso
- Log detallado de operaciones
- Opción de cancelar (solo durante descarga)

## Seguridad

### Medidas Implementadas

- **Validación de Checksums**: Verifica la integridad de las descargas
- **Respaldo Automático**: Permite rollback en caso de errores
- **Verificación de Estructura**: Valida que la actualización sea válida
- **Fuentes Confiables**: Solo descarga desde URLs configuradas
- **Validación de Versiones**: Verifica que la versión sea más nueva

### Carpetas de Respaldo

Los respaldos se almacenan en:
- **Ubicación**: `./backup/`
- **Formato**: `backup_v{version}_{timestamp}/`
- **Contenido**: Archivos principales de la aplicación
- **Información**: Archivo `backup_info.json` con metadatos

## Estructura de Archivos

### Archivos del Sistema

```
core/
├── updater.py              # Módulo principal de actualizaciones
└── ...

gui/
├── update_dialog.py        # Interfaces de usuario para actualizaciones
└── ...

version.json                 # Información de versión actual
config.json                  # Configuración (sección updates)
backup/                      # Carpeta de respaldos
temp/                        # Archivos temporales de actualización
```

### Archivo version.json

```json
{
  "version": "1.0.0",
  "app_name": "Automatización de Compresión de Archivos",
  "build_date": "2025-08-20",
  "updated_at": "2025-08-20T00:00:00",
  "update_history": [
    {
      "version": "1.0.0",
      "date": "2025-08-20",
      "changes": ["Versión inicial"]
    }
  ]
}
```

## API del Servidor

### Endpoint de Verificación

**URL**: `{update_server_url}/check`

**Parámetros**:
- `current_version`: Versión actual de la aplicación
- `allow_prereleases`: Si incluir versiones beta

**Respuesta**:
```json
{
  "update_available": true,
  "version": "1.1.0",
  "download_url": "https://github.com/usuario/repo/releases/download/v1.1.0/update.zip",
  "changelog": "Mejoras y correcciones...",
  "file_size": 5242880,
  "checksum": "abc123def456...",
  "release_date": "2025-08-21",
  "is_critical": false,
  "min_version": "1.0.0"
}
```

## Solución de Problemas

### Problemas Comunes

#### Error de Conexión
- **Causa**: No hay conexión a internet o servidor no disponible
- **Solución**: Verificar conexión y intentar más tarde

#### Error de Descarga
- **Causa**: Archivo corrupto o conexión interrumpida
- **Solución**: Reintentar descarga o verificar espacio en disco

#### Error de Instalación
- **Causa**: Permisos insuficientes o archivos en uso
- **Solución**: Ejecutar como administrador o cerrar aplicación

#### Rollback Automático
- **Causa**: Error durante instalación
- **Acción**: El sistema restaura automáticamente la versión anterior

### Logs de Depuración

Los logs del sistema de actualizaciones se encuentran en:
- **Archivo**: `logs/compression_YYYY-MM-DD.log`
- **Prefijo**: `[UPDATER]`
- **Niveles**: INFO, WARNING, ERROR

### Comandos de Diagnóstico

```python
# Verificar estado del actualizador
status = updater.get_status()
print(status)

# Obtener historial de actualizaciones
history = updater.get_update_history()
print(history)

# Verificar si es momento de actualizar
should_check = updater.should_check_for_updates()
print(should_check)
```

## Desarrollo

### Agregar Nuevas Funcionalidades

1. **Modificar `core/updater.py`**: Lógica principal
2. **Actualizar `gui/update_dialog.py`**: Interfaces de usuario
3. **Configurar `config.json`**: Nuevas opciones
4. **Probar**: Verificar funcionamiento completo

### Testing

```bash
# Instalar dependencias de testing
pip install pytest pytest-cov

# Ejecutar pruebas
pytest tests/test_updater.py -v

# Cobertura de código
pytest tests/test_updater.py --cov=core.updater
```

## Licencia

Este sistema de actualizaciones es parte de la aplicación "Automatización de Compresión de Archivos" y está sujeto a los mismos términos de licencia.

---

**Nota**: Para configurar un servidor de actualizaciones personalizado, consulte la documentación del servidor o configure GitHub Releases para distribución automática.