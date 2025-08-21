#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validación del entorno para releases
Automatización de Compresión de Archivos

Este script verifica que el entorno esté correctamente configurado
para crear releases automáticos.
"""

import json
import subprocess
import sys
import os
from pathlib import Path
import requests

class EnvironmentValidator:
    """Validador del entorno de desarrollo"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0
    
    def check(self, description, condition, error_msg="", warning_msg="", is_warning=False):
        """Realiza una verificación"""
        self.total_checks += 1
        print(f"🔍 {description}...", end=" ")
        
        try:
            if callable(condition):
                result = condition()
            else:
                result = condition
            
            if result:
                print("✅")
                self.success_count += 1
                return True
            else:
                if is_warning:
                    print("⚠️")
                    if warning_msg:
                        self.warnings.append(f"⚠️ {description}: {warning_msg}")
                else:
                    print("❌")
                    if error_msg:
                        self.errors.append(f"❌ {description}: {error_msg}")
                return False
        except Exception as e:
            if is_warning:
                print("⚠️")
                self.warnings.append(f"⚠️ {description}: {str(e)}")
            else:
                print("❌")
                self.errors.append(f"❌ {description}: {str(e)}")
            return False
    
    def run_command_check(self, command, description=""):
        """Ejecuta un comando y verifica si fue exitoso"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def validate_python_environment(self):
        """Valida el entorno de Python"""
        print("\n🐍 VALIDANDO ENTORNO PYTHON")
        print("=" * 40)
        
        # Python version
        self.check(
            "Python 3.8+",
            sys.version_info >= (3, 8),
            f"Se requiere Python 3.8+, encontrado {sys.version_info.major}.{sys.version_info.minor}"
        )
        
        # pip
        self.check(
            "pip disponible",
            lambda: self.run_command_check("pip --version"),
            "pip no está disponible"
        )
        
        # Dependencias principales
        required_packages = ['tkinter', 'json', 'pathlib', 'subprocess']
        for package in required_packages:
            try:
                __import__(package)
                self.check(f"Módulo {package}", True)
            except ImportError:
                self.check(f"Módulo {package}", False, f"Módulo {package} no disponible")
    
    def validate_project_structure(self):
        """Valida la estructura del proyecto"""
        print("\n📁 VALIDANDO ESTRUCTURA DEL PROYECTO")
        print("=" * 40)
        
        # Archivos principales
        required_files = [
            ('main.py', 'Archivo principal de la aplicación'),
            ('build.py', 'Script de compilación'),
            ('requirements.txt', 'Lista de dependencias'),
            ('config.json', 'Archivo de configuración')
        ]
        
        for file_name, description in required_files:
            file_path = self.project_root / file_name
            self.check(
                f"{description} ({file_name})",
                file_path.exists(),
                f"Archivo {file_name} no encontrado"
            )
        
        # Carpetas importantes
        important_dirs = [
            ('core', 'Módulos principales'),
            ('ui', 'Interfaz de usuario'),
            ('scripts', 'Scripts de automatización')
        ]
        
        for dir_name, description in important_dirs:
            dir_path = self.project_root / dir_name
            self.check(
                f"{description} (/{dir_name})",
                dir_path.exists() and dir_path.is_dir(),
                f"Carpeta {dir_name} no encontrada",
                is_warning=True
            )
    
    def validate_git_configuration(self):
        """Valida la configuración de Git"""
        print("\n📤 VALIDANDO CONFIGURACIÓN GIT")
        print("=" * 40)
        
        # Git disponible
        self.check(
            "Git instalado",
            lambda: self.run_command_check("git --version"),
            "Git no está instalado o no está en PATH"
        )
        
        # Repositorio git
        git_dir = self.project_root / '.git'
        self.check(
            "Repositorio Git inicializado",
            git_dir.exists(),
            "No es un repositorio Git. Ejecuta 'git init'"
        )
        
        # Configuración de usuario
        self.check(
            "Usuario Git configurado",
            lambda: self.run_command_check("git config user.name"),
            "Usuario Git no configurado. Ejecuta 'git config user.name \"Tu Nombre\"'",
            is_warning=True
        )
        
        self.check(
            "Email Git configurado",
            lambda: self.run_command_check("git config user.email"),
            "Email Git no configurado. Ejecuta 'git config user.email \"tu@email.com\"'",
            is_warning=True
        )
        
        # Remote origin
        self.check(
            "Remote origin configurado",
            lambda: self.run_command_check("git remote get-url origin"),
            "Remote origin no configurado. Ejecuta 'git remote add origin <URL>'"
        )
    
    def validate_github_actions(self):
        """Valida la configuración de GitHub Actions"""
        print("\n⚙️ VALIDANDO GITHUB ACTIONS")
        print("=" * 40)
        
        # Archivo de workflow
        workflow_file = self.project_root / '.github' / 'workflows' / 'release.yml'
        self.check(
            "Workflow de release configurado",
            workflow_file.exists(),
            "Archivo .github/workflows/release.yml no encontrado"
        )
        
        # Validar contenido del workflow
        if workflow_file.exists():
            try:
                content = workflow_file.read_text(encoding='utf-8')
                
                self.check(
                    "Trigger por tags configurado",
                    "tags:" in content and "'v*'" in content,
                    "Trigger por tags no configurado correctamente"
                )
                
                self.check(
                    "Permisos de escritura configurados",
                    "contents: write" in content,
                    "Permisos de escritura no configurados"
                )
                
                self.check(
                    "Compilación configurada",
                    "python build.py" in content,
                    "Paso de compilación no configurado"
                )
                
            except Exception as e:
                self.errors.append(f"❌ Error al leer workflow: {e}")
    
    def validate_version_system(self):
        """Valida el sistema de versionado"""
        print("\n🔢 VALIDANDO SISTEMA DE VERSIONADO")
        print("=" * 40)
        
        # Archivo version.json
        version_file = self.project_root / 'version.json'
        self.check(
            "Archivo version.json existe",
            version_file.exists(),
            "Archivo version.json no encontrado",
            "Se creará automáticamente en el primer release",
            is_warning=True
        )
        
        # Validar contenido si existe
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                
                self.check(
                    "Campo 'version' en version.json",
                    'version' in version_data,
                    "Campo 'version' no encontrado en version.json"
                )
                
                if 'version' in version_data:
                    version = version_data['version']
                    parts = version.split('.')
                    self.check(
                        "Formato de versión válido (x.y.z)",
                        len(parts) == 3 and all(p.isdigit() for p in parts),
                        f"Formato de versión inválido: {version}"
                    )
                
            except json.JSONDecodeError:
                self.errors.append("❌ version.json contiene JSON inválido")
            except Exception as e:
                self.errors.append(f"❌ Error al leer version.json: {e}")
    
    def validate_build_system(self):
        """Valida el sistema de compilación"""
        print("\n🔨 VALIDANDO SISTEMA DE COMPILACIÓN")
        print("=" * 40)
        
        # PyInstaller
        self.check(
            "PyInstaller disponible",
            lambda: self.run_command_check("pyinstaller --version"),
            "PyInstaller no está instalado. Ejecuta 'pip install pyinstaller'"
        )
        
        # Probar compilación (sin ejecutar)
        build_script = self.project_root / 'build.py'
        if build_script.exists():
            try:
                with open(build_script, 'r', encoding='utf-8') as f:
                    build_content = f.read()
                
                self.check(
                    "Script build.py válido",
                    "pyinstaller" in build_content.lower(),
                    "build.py no parece usar PyInstaller"
                )
                
            except Exception as e:
                self.errors.append(f"❌ Error al leer build.py: {e}")
    
    def validate_configuration(self):
        """Valida la configuración de la aplicación"""
        print("\n⚙️ VALIDANDO CONFIGURACIÓN")
        print("=" * 40)
        
        config_file = self.project_root / 'config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Verificar configuración de actualizaciones
                if 'app_settings' in config_data and 'updates' in config_data['app_settings']:
                    updates_config = config_data['app_settings']['updates']
                    
                    self.check(
                        "URL de verificación configurada",
                        'update_check_url' in updates_config and updates_config['update_check_url'],
                        "URL de verificación de actualizaciones no configurada",
                        "Recuerda actualizar con tu repositorio real",
                        is_warning=True
                    )
                    
                    self.check(
                        "URL de descarga configurada",
                        'download_base_url' in updates_config and updates_config['download_base_url'],
                        "URL base de descarga no configurada",
                        "Recuerda actualizar con tu repositorio real",
                        is_warning=True
                    )
                
            except json.JSONDecodeError:
                self.errors.append("❌ config.json contiene JSON inválido")
            except Exception as e:
                self.errors.append(f"❌ Error al leer config.json: {e}")
    
    def show_summary(self):
        """Muestra el resumen de la validación"""
        print("\n" + "=" * 50)
        print("📋 RESUMEN DE VALIDACIÓN")
        print("=" * 50)
        
        print(f"✅ Verificaciones exitosas: {self.success_count}/{self.total_checks}")
        
        if self.warnings:
            print(f"⚠️ Advertencias: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if self.errors:
            print(f"❌ Errores: {len(self.errors)}")
            for error in self.errors:
                print(f"   {error}")
        
        print()
        
        if not self.errors:
            if not self.warnings:
                print("🎉 ¡Entorno completamente configurado!")
                print("✅ Puedes crear releases sin problemas")
            else:
                print("✅ Entorno configurado con advertencias menores")
                print("⚠️ Revisa las advertencias pero puedes continuar")
            return True
        else:
            print("❌ Hay errores que deben corregirse antes de crear releases")
            print("🔧 Corrige los errores listados arriba")
            return False
    
    def run_validation(self):
        """Ejecuta todas las validaciones"""
        print("🔍 VALIDADOR DE ENTORNO PARA RELEASES")
        print("=" * 50)
        print("Verificando configuración del proyecto...")
        
        # Ejecutar todas las validaciones
        self.validate_python_environment()
        self.validate_project_structure()
        self.validate_git_configuration()
        self.validate_github_actions()
        self.validate_version_system()
        self.validate_build_system()
        self.validate_configuration()
        
        # Mostrar resumen
        return self.show_summary()

def main():
    """Función principal"""
    validator = EnvironmentValidator()
    success = validator.run_validation()
    
    if success:
        print("\n🚀 Para crear un release, ejecuta:")
        print("   python scripts/create_release.py patch")
        print("   python scripts/create_release.py minor")
        print("   python scripts/create_release.py major")
        sys.exit(0)
    else:
        print("\n🔧 Corrige los errores antes de continuar")
        sys.exit(1)

if __name__ == '__main__':
    main()