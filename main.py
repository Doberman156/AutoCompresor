#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatización de Compresión de Archivos v1.0.12
Aplicación avanzada para comprimir archivos automáticamente con interfaz gráfica
Incluye sistema de actualizaciones automáticas y configuración personalizable
"""

import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import logging

# Agregar el directorio actual al path para importaciones
sys.path.insert(0, str(Path(__file__).parent))

# Configurar sistema de logging avanzado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


def check_python_version():
    """Verifica que la versión de Python sea compatible."""
    if sys.version_info < (3, 8):
        error_msg = (
            f"Esta aplicación requiere Python 3.8 o superior.\n"
            f"Versión actual: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n\n"
            f"Por favor, actualice Python e intente nuevamente."
        )
        
        # Mostrar error en GUI si es posible
        try:
            root = tk.Tk()
            root.withdraw()  # Ocultar ventana principal
            messagebox.showerror("Error de Versión de Python", error_msg)
            root.destroy()
        except:
            print(error_msg)
        
        sys.exit(1)


def check_dependencies():
    """Verifica que las dependencias requeridas estén instaladas."""
    missing_deps = []
    optional_deps = []
    
    # Dependencias críticas (incluidas en Python estándar)
    critical_deps = {
        'tkinter': 'Interfaz gráfica',
        'pathlib': 'Manejo de rutas',
        'zipfile': 'Compresión de archivos',
        'threading': 'Procesamiento en paralelo',
        'logging': 'Sistema de logs',
        'json': 'Configuración',
        'datetime': 'Manejo de fechas',
        'os': 'Sistema operativo',
        'shutil': 'Operaciones de archivos'
    }
    
    for dep, description in critical_deps.items():
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(f"{dep} ({description})")
    
    # Dependencias opcionales
    optional_deps_list = {
        'ttkthemes': 'Temas modernos para la interfaz',
        'psutil': 'Información del sistema',
        'pillow': 'Manejo de imágenes'
    }
    
    for dep, description in optional_deps_list.items():
        try:
            __import__(dep)
        except ImportError:
            optional_deps.append(f"{dep} ({description})")
    
    # Reportar dependencias faltantes
    if missing_deps:
        error_msg = (
            "Faltan dependencias críticas:\n\n" +
            "\n".join(f"• {dep}" for dep in missing_deps) +
            "\n\nLa aplicación no puede ejecutarse sin estas dependencias."
        )
        
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Dependencias Faltantes", error_msg)
            root.destroy()
        except:
            print(error_msg)
        
        sys.exit(1)
    
    # Advertir sobre dependencias opcionales
    if optional_deps:
        warning_msg = (
            "Dependencias opcionales no encontradas:\n\n" +
            "\n".join(f"• {dep}" for dep in optional_deps) +
            "\n\nLa aplicación funcionará, pero algunas características pueden estar limitadas.\n\n"
            "Para instalar dependencias opcionales, ejecute:\n"
            "pip install -r requirements.txt"
        )
        
        print("ADVERTENCIA:", warning_msg)


def setup_environment():
    """Configura el entorno de la aplicación."""
    # Crear directorios necesarios si no existen
    directories = ['logs', 'assets', 'temp']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # Configurar variables de entorno si es necesario
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    
    # En Windows, configurar DPI awareness para mejor renderizado
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass  # No crítico si falla


def handle_exception(exc_type, exc_value, exc_traceback):
    """Maneja excepciones no capturadas."""
    if issubclass(exc_type, KeyboardInterrupt):
        # Permitir Ctrl+C
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Log del error
    logging.error(
        "Excepción no capturada",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    
    # Mostrar error al usuario
    error_msg = (
        f"Ha ocurrido un error inesperado:\n\n"
        f"Tipo: {exc_type.__name__}\n"
        f"Mensaje: {str(exc_value)}\n\n"
        f"El error ha sido registrado en 'error.log'.\n"
        f"Si el problema persiste, por favor reporte este error."
    )
    
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error Crítico", error_msg)
        root.destroy()
    except:
        print(f"ERROR CRÍTICO: {error_msg}")


def main():
    """Función principal de la aplicación."""
    try:
        print("Iniciando Automatización de Compresión de Archivos v1.0...")
        
        # Verificaciones iniciales
        print("Verificando versión de Python...")
        check_python_version()
        
        print("Verificando dependencias...")
        check_dependencies()
        
        print("Configurando entorno...")
        setup_environment()
        
        # Configurar manejo de excepciones
        sys.excepthook = handle_exception
        
        # Importar y lanzar la aplicación principal
        print("Cargando interfaz gráfica...")
        
        try:
            from gui.main_window import MainWindow
            
            # Crear y ejecutar la aplicación
            print("Iniciando aplicación...")
            app = MainWindow()
            
            print("Aplicación lista. Mostrando interfaz...")
            app.run()
            
        except ImportError as e:
            error_msg = (
                f"Error al importar módulos de la aplicación:\n\n"
                f"{str(e)}\n\n"
                f"Verifique que todos los archivos estén presentes y sean accesibles."
            )
            
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Error de Importación", error_msg)
            root.destroy()
            sys.exit(1)
        
        except Exception as e:
            error_msg = (
                f"Error al inicializar la aplicación:\n\n"
                f"{str(e)}\n\n"
                f"Verifique la configuración y los permisos del sistema."
            )
            
            logging.error(f"Error en inicialización: {e}", exc_info=True)
            
            try:
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Error de Inicialización", error_msg)
                root.destroy()
            except:
                print(f"ERROR: {error_msg}")
            
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nAplicación interrumpida por el usuario.")
        sys.exit(0)
    
    except Exception as e:
        error_msg = f"Error crítico durante el inicio: {e}"
        logging.error(error_msg, exc_info=True)
        print(f"ERROR CRÍTICO: {error_msg}")
        sys.exit(1)
    
    finally:
        print("Cerrando aplicación...")


def show_help():
    """Muestra información de ayuda."""
    help_text = """
Automatización de Compresión de Archivos v1.0

Uso: python main.py [opciones]

Opciones:
  -h, --help     Muestra esta ayuda
  -v, --version  Muestra la versión
  --check-deps   Verifica dependencias sin iniciar la aplicación
  --reset-config Reinicia la configuración a valores por defecto

Ejemplos:
  python main.py                 # Inicia la aplicación normalmente
  python main.py --check-deps    # Solo verifica dependencias
  python main.py --reset-config  # Reinicia configuración

Para más información, consulte la documentación incluida.
"""
    print(help_text)


def show_version():
    """Muestra información de versión."""
    version_info = """
Automatización de Compresión de Archivos
Versión: 1.0.0
Python: {python_version}
Plataforma: {platform}
Directorio: {directory}
""".format(
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        platform=sys.platform,
        directory=Path(__file__).parent.absolute()
    )
    print(version_info)


def reset_config():
    """Reinicia la configuración a valores por defecto."""
    try:
        config_file = Path('config.json')
        if config_file.exists():
            backup_file = Path(f'config_backup_{int(time.time())}.json')
            config_file.rename(backup_file)
            print(f"Configuración actual respaldada como: {backup_file}")
        
        # La configuración se recreará automáticamente al iniciar
        print("Configuración reiniciada. Se creará una nueva al iniciar la aplicación.")
        
    except Exception as e:
        print(f"Error al reiniciar configuración: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Procesar argumentos de línea de comandos
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['-h', '--help']:
            show_help()
            sys.exit(0)
        
        elif arg in ['-v', '--version']:
            show_version()
            sys.exit(0)
        
        elif arg == '--check-deps':
            print("Verificando dependencias...")
            check_python_version()
            check_dependencies()
            print("Verificación completada.")
            sys.exit(0)
        
        elif arg == '--reset-config':
            import time
            reset_config()
            sys.exit(0)
        
        else:
            print(f"Argumento desconocido: {sys.argv[1]}")
            print("Use --help para ver las opciones disponibles.")
            sys.exit(1)
    
    # Ejecutar aplicación principal
    main()