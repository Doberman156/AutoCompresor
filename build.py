#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de construcción para generar ejecutable de Automatización de Compresión

Este script automatiza el proceso de creación del ejecutable usando PyInstaller.
Incluye verificaciones previas, limpieza de archivos temporales y validaciones.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_step(message):
    """Imprime un paso del proceso con formato."""
    print(f"\n{'='*60}")
    print(f"🔧 {message}")
    print(f"{'='*60}")

def print_success(message):
    """Imprime mensaje de éxito."""
    print(f"✅ {message}")

def print_error(message):
    """Imprime mensaje de error."""
    print(f"❌ {message}")

def print_warning(message):
    """Imprime mensaje de advertencia."""
    print(f"⚠️  {message}")

def check_python_version():
    """Verifica que la versión de Python sea compatible."""
    print_step("Verificando versión de Python")
    
    if sys.version_info < (3, 8):
        print_error(f"Python {sys.version_info.major}.{sys.version_info.minor} no es compatible.")
        print_error("Se requiere Python 3.8 o superior.")
        return False
    
    print_success(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} ✓")
    return True

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas."""
    print_step("Verificando dependencias")
    
    try:
        import PyInstaller
        print_success(f"PyInstaller {PyInstaller.__version__} ✓")
    except ImportError:
        print_error("PyInstaller no está instalado.")
        print("Ejecuta: pip install -r requirements.txt")
        return False
    
    # Verificar otras dependencias críticas
    dependencies = ['tkinter', 'pathlib', 'configparser', 'threading']
    
    for dep in dependencies:
        try:
            __import__(dep)
            print_success(f"{dep} ✓")
        except ImportError:
            print_error(f"{dep} no está disponible.")
            return False
    
    return True

def check_project_structure():
    """Verifica que la estructura del proyecto sea correcta."""
    print_step("Verificando estructura del proyecto")
    
    required_files = [
        'main.py',
        'config.json',
        'requirements.txt',
        'build.spec'
    ]
    
    required_dirs = [
        'gui',
        'core',
        'utils'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print_error(f"Archivo requerido no encontrado: {file}")
            return False
        print_success(f"{file} ✓")
    
    for dir in required_dirs:
        if not os.path.exists(dir):
            print_error(f"Directorio requerido no encontrado: {dir}")
            return False
        print_success(f"{dir}/ ✓")
    
    return True

def clean_build_files():
    """Limpia archivos de construcción anteriores."""
    print_step("Limpiando archivos de construcción anteriores")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.pyc', '*.pyo']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print_success(f"Eliminado: {dir_name}/")
    
    # Limpiar archivos __pycache__ recursivamente
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs[:]:
            if dir_name == '__pycache__':
                full_path = os.path.join(root, dir_name)
                shutil.rmtree(full_path)
                print_success(f"Eliminado: {full_path}")
                dirs.remove(dir_name)

def create_icon():
    """Crea un icono básico si no existe."""
    print_step("Verificando icono de la aplicación")
    
    assets_dir = Path('assets')
    assets_dir.mkdir(exist_ok=True)
    
    icon_path = assets_dir / 'icon.ico'
    
    if not icon_path.exists():
        print_warning("No se encontró icon.ico, el ejecutable usará el icono por defecto.")
        print("Para agregar un icono personalizado, coloca 'icon.ico' en la carpeta 'assets/'.")
    else:
        print_success(f"Icono encontrado: {icon_path}")

def build_executable():
    """Construye el ejecutable usando PyInstaller."""
    print_step("Construyendo ejecutable")
    
    try:
        # Ejecutar PyInstaller con el archivo de especificación
        cmd = [sys.executable, '-m', 'PyInstaller', '--clean', 'build.spec']
        
        print(f"Ejecutando: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("Ejecutable creado exitosamente!")
            
            # Verificar que el ejecutable se haya creado
            exe_path = Path('dist') / 'AutomatizacionCompresion.exe'
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print_success(f"Archivo: {exe_path}")
                print_success(f"Tamaño: {size_mb:.1f} MB")
                return True
            else:
                print_error("El ejecutable no se encontró en dist/")
                return False
        else:
            print_error("Error durante la construcción:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        return False

def create_distribution_info():
    """Crea información adicional para la distribución."""
    print_step("Creando información de distribución")
    
    dist_dir = Path('dist')
    
    # Crear archivo README para la distribución
    readme_content = """# Automatización de Compresión de Archivos

## Instrucciones de Uso

1. Ejecuta AutomatizacionCompresion.exe
2. Selecciona la carpeta origen con los archivos a comprimir
3. Configura las opciones según tus necesidades
4. Inicia el proceso y monitorea el progreso

## Características

- Compresión individual de archivos en formato ZIP
- Nomenclatura personalizable
- Sistema de respaldo automático
- Logging completo de operaciones
- Interfaz gráfica intuitiva

## Soporte

Para reportar problemas o sugerencias, contacta al desarrollador.

Versión: 1.0.0
Fecha de construcción: {}
""".format(Path().cwd().name)
    
    readme_path = dist_dir / 'README.txt'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print_success(f"Creado: {readme_path}")

def main():
    """Función principal del script de construcción."""
    print("🚀 Script de Construcción - Automatización de Compresión")
    print("=" * 60)
    
    # Verificaciones previas
    if not check_python_version():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    if not check_project_structure():
        sys.exit(1)
    
    # Preparación
    clean_build_files()
    create_icon()
    
    # Construcción
    if not build_executable():
        sys.exit(1)
    
    # Finalización
    create_distribution_info()
    
    print_step("¡Construcción completada exitosamente!")
    print("")
    print("📁 El ejecutable se encuentra en: dist/AutomatizacionCompresion.exe")
    print("")
    print("💡 Consejos:")
    print("   • Puedes distribuir toda la carpeta 'dist/' como un paquete completo")
    print("   • El ejecutable es portable y no requiere instalación")
    print("   • Asegúrate de que el sistema de destino tenga Windows 7 o superior")
    print("")
    print("✨ ¡Listo para usar!")

if __name__ == '__main__':
    main()