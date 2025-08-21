# 🚀 Guía Completa: Configurar Actualizaciones Automáticas con GitHub

Esta guía te ayudará a configurar un sistema completo de actualizaciones automáticas para tu aplicación de compresión de archivos usando GitHub.

## 📋 Índice

1. [Preparación Inicial](#preparación-inicial)
2. [Crear Repositorio en GitHub](#crear-repositorio-en-github)
3. [Configurar GitHub Actions](#configurar-github-actions)
4. [Configurar la Aplicación](#configurar-la-aplicación)
5. [Crear tu Primer Release](#crear-tu-primer-release)
6. [Automatización Completa](#automatización-completa)
7. [Solución de Problemas](#solución-de-problemas)

---

## 🎯 Preparación Inicial

### Requisitos Previos

- ✅ Cuenta de GitHub
- ✅ Git instalado en tu computadora
- ✅ Tu aplicación funcionando correctamente
- ✅ Archivo ejecutable (.exe) compilado

### Archivos Necesarios

Antes de empezar, asegúrate de tener estos archivos en tu proyecto:

```
tu-proyecto/
├── dist/
│   └── AutomatizacionCompresion.exe  # Tu aplicación compilada
├── version.json                       # Información de versión
├── config.json                        # Configuración actualizada
├── README.md                          # Documentación del proyecto
└── .github/
    └── workflows/
        └── release.yml                # GitHub Actions (lo crearemos)
```

---

## 📦 Crear Repositorio en GitHub

### Paso 1: Crear el Repositorio

1. **Ve a GitHub.com** y haz clic en "New repository"
2. **Nombre del repositorio**: `automatizacion-compresion` (o el nombre que prefieras)
3. **Descripción**: "Aplicación para automatizar la compresión de archivos con nomenclatura personalizable"
4. **Visibilidad**: 
   - ✅ **Public** (recomendado para distribución)
   - ❌ Private (solo si es para uso interno)
5. **Inicializar con**:
   - ✅ Add a README file
   - ✅ Add .gitignore (Python)
   - ❌ Choose a license (opcional)

### Paso 2: Clonar el Repositorio

```bash
# Clona tu repositorio
git clone https://github.com/TU-USUARIO/automatizacion-compresion.git
cd automatizacion-compresion
```

### Paso 3: Subir tu Código

```bash
# Copia todos los archivos de tu proyecto al repositorio clonado
# Luego:

git add .
git commit -m "Versión inicial de la aplicación"
git push origin main
```

---

## ⚙️ Configurar GitHub Actions

### Paso 1: Crear el Workflow

Crea el archivo `.github/workflows/release.yml`:

```yaml
name: 🚀 Build and Release

on:
  push:
    tags:
      - 'v*.*.*'  # Se ejecuta cuando creas un tag como v1.0.0
  workflow_dispatch:  # Permite ejecutar manualmente

jobs:
  build-and-release:
    runs-on: windows-latest
    
    steps:
    - name: 📥 Checkout code
      uses: actions/checkout@v4
      
    - name: 🐍 Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: 📦 Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
        
    - name: 🔨 Build executable
      run: |
        python build.py
        
    - name: 📋 Get version from tag
      id: get_version
      run: |
        $version = $env:GITHUB_REF -replace 'refs/tags/v', ''
        echo "version=$version" >> $env:GITHUB_OUTPUT
        
    - name: 📝 Generate changelog
      id: changelog
      run: |
        $changelog = @"
        ## 🎉 Novedades en esta versión
        
        ### ✨ Nuevas funcionalidades
        - Sistema de actualizaciones automáticas
        - Mejoras en la interfaz de usuario
        - Optimizaciones de rendimiento
        
        ### 🐛 Correcciones
        - Corrección de estadísticas de archivos procesados
        - Mejoras en la validación de rutas
        - Estabilidad general mejorada
        
        ### 📥 Instalación
        1. Descarga `AutomatizacionCompresion.exe`
        2. Ejecuta el archivo
        3. ¡Listo para usar!
        
        ### 🔄 Actualización Automática
        Si ya tienes una versión anterior, la aplicación te notificará automáticamente sobre esta actualización.
        "@
        echo "changelog<<EOF" >> $env:GITHUB_OUTPUT
        echo $changelog >> $env:GITHUB_OUTPUT
        echo "EOF" >> $env:GITHUB_OUTPUT
        
    - name: 🎉 Create Release
      uses: softprops/action-gh-release@v1
      with:
        tag_name: ${{ github.ref_name }}
        name: "Automatización Compresión v${{ steps.get_version.outputs.version }}"
        body: ${{ steps.changelog.outputs.changelog }}
        files: |
          dist/AutomatizacionCompresion.exe
          README.txt
          config.json
        draft: false
        prerelease: false
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        
    - name: ✅ Success notification
      run: |
        echo "🎉 Release v${{ steps.get_version.outputs.version }} created successfully!"
        echo "📥 Download URL: https://github.com/${{ github.repository }}/releases/tag/${{ github.ref_name }}"
```

### Paso 2: Configurar Permisos

1. Ve a tu repositorio en GitHub
2. **Settings** → **Actions** → **General**
3. En "Workflow permissions":
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**

---

## 🔧 Configurar la Aplicación

### Paso 1: Actualizar config.json

Reemplaza la URL de ejemplo con tu repositorio real:

```json
{
  "updates": {
    "auto_check": true,
    "update_server_url": "https://api.github.com/repos/TU-USUARIO/automatizacion-compresion/releases",
    "check_frequency_hours": 24,
    "auto_download": false,
    "auto_install": false,
    "backup_enabled": true,
    "verify_signatures": false,
    "allow_prereleases": false
  }
}
```

**⚠️ IMPORTANTE**: Reemplaza `TU-USUARIO` con tu nombre de usuario de GitHub.

### Paso 2: Actualizar version.json

```json
{
  "version": "1.0.0",
  "build_date": "2025-01-20",
  "build_number": 1,
  "release_notes": "Versión inicial con sistema de actualizaciones automáticas"
}
```

---

## 🎉 Crear tu Primer Release

### Método 1: Usando Git Tags (Recomendado)

```bash
# 1. Asegúrate de que todos los cambios estén subidos
git add .
git commit -m "Preparar para release v1.0.0"
git push origin main

# 2. Crear y subir el tag
git tag v1.0.0
git push origin v1.0.0

# 3. GitHub Actions se ejecutará automáticamente
```

### Método 2: Desde la Interfaz de GitHub

1. Ve a tu repositorio en GitHub
2. **Releases** → **Create a new release**
3. **Tag version**: `v1.0.0`
4. **Release title**: `Automatización Compresión v1.0.0`
5. **Describe this release**: Agrega las novedades
6. **Attach binaries**: Sube `AutomatizacionCompresion.exe`
7. **Publish release**

---

## 🤖 Automatización Completa

### Script de Release Automático

Crea `scripts/create_release.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear releases automáticamente
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def get_current_version():
    """Obtiene la versión actual del archivo version.json"""
    try:
        with open('version.json', 'r') as f:
            data = json.load(f)
        return data['version']
    except:
        return '1.0.0'

def increment_version(version, increment_type='patch'):
    """Incrementa la versión según el tipo"""
    major, minor, patch = map(int, version.split('.'))
    
    if increment_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif increment_type == 'minor':
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    return f"{major}.{minor}.{patch}"

def update_version_file(new_version):
    """Actualiza el archivo version.json"""
    version_data = {
        "version": new_version,
        "build_date": datetime.now().strftime("%Y-%m-%d"),
        "build_number": int(datetime.now().timestamp()),
        "release_notes": f"Versión {new_version} con mejoras y correcciones"
    }
    
    with open('version.json', 'w') as f:
        json.dump(version_data, f, indent=2)

def create_release(version_type='patch'):
    """Crea un nuevo release"""
    print(f"🚀 Creando nuevo release...")
    
    # Obtener versión actual
    current_version = get_current_version()
    new_version = increment_version(current_version, version_type)
    
    print(f"📈 Versión actual: {current_version}")
    print(f"📈 Nueva versión: {new_version}")
    
    # Actualizar version.json
    update_version_file(new_version)
    
    # Compilar aplicación
    print("🔨 Compilando aplicación...")
    result = subprocess.run([sys.executable, 'build.py'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error al compilar: {result.stderr}")
        return False
    
    # Commit y push
    print("📤 Subiendo cambios...")
    subprocess.run(['git', 'add', '.'])
    subprocess.run(['git', 'commit', '-m', f'Release v{new_version}'])
    subprocess.run(['git', 'push', 'origin', 'main'])
    
    # Crear tag
    print(f"🏷️ Creando tag v{new_version}...")
    subprocess.run(['git', 'tag', f'v{new_version}'])
    subprocess.run(['git', 'push', 'origin', f'v{new_version}'])
    
    print(f"✅ Release v{new_version} creado exitosamente!")
    print(f"🔗 URL: https://github.com/TU-USUARIO/automatizacion-compresion/releases/tag/v{new_version}")
    
    return True

if __name__ == '__main__':
    version_type = sys.argv[1] if len(sys.argv) > 1 else 'patch'
    create_release(version_type)
```

### Uso del Script

```bash
# Release patch (1.0.0 → 1.0.1)
python scripts/create_release.py patch

# Release minor (1.0.1 → 1.1.0)
python scripts/create_release.py minor

# Release major (1.1.0 → 2.0.0)
python scripts/create_release.py major
```

---

## 🔍 Solución de Problemas

### Problema: GitHub Actions falla al compilar

**Solución**:
1. Verifica que `requirements.txt` esté actualizado
2. Asegúrate de que `build.py` funcione localmente
3. Revisa los logs en la pestaña "Actions" de GitHub

### Problema: La aplicación no encuentra actualizaciones

**Solución**:
1. Verifica que la URL en `config.json` sea correcta
2. Asegúrate de que el repositorio sea público
3. Verifica que exista al menos un release

### Problema: Error 404 al verificar actualizaciones

**Solución**:
```json
{
  "updates": {
    "update_server_url": "https://api.github.com/repos/TU-USUARIO/TU-REPOSITORIO/releases"
  }
}
```

### Problema: Permisos denegados en GitHub Actions

**Solución**:
1. Ve a **Settings** → **Actions** → **General**
2. Selecciona "Read and write permissions"
3. Guarda los cambios

---

## 🎯 Próximos Pasos

1. **✅ Configurar repositorio**: Sigue esta guía paso a paso
2. **✅ Crear primer release**: Usa el método que prefieras
3. **✅ Probar actualizaciones**: Ejecuta tu aplicación y verifica
4. **✅ Automatizar**: Usa el script para releases futuros
5. **✅ Distribuir**: Comparte el enlace de GitHub con tus usuarios

---

## 📞 Soporte

Si tienes problemas:

1. **Revisa los logs** de GitHub Actions
2. **Verifica la configuración** de URLs y permisos
3. **Prueba localmente** antes de crear releases
4. **Consulta la documentación** de GitHub Actions

---

**¡Felicidades! 🎉 Tu aplicación ahora tiene actualizaciones automáticas profesionales.**

Tus usuarios recibirán notificaciones automáticas cuando publiques nuevas versiones, y podrán actualizar con un solo clic desde la aplicación.