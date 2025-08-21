#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear releases automáticamente
Automatización de Compresión de Archivos

Uso:
    python scripts/create_release.py [patch|minor|major]
    
Ejemplos:
    python scripts/create_release.py patch   # 1.0.0 → 1.0.1
    python scripts/create_release.py minor   # 1.0.1 → 1.1.0
    python scripts/create_release.py major   # 1.1.0 → 2.0.0
"""

import json
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

class ReleaseManager:
    """Gestor de releases automáticos"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.version_file = self.project_root / 'version.json'
        self.config_file = self.project_root / 'config.json'
        
    def get_current_version(self):
        """Obtiene la versión actual del archivo version.json"""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('version', '1.0.0')
            else:
                return '1.0.0'
        except Exception as e:
            print(f"⚠️ Error al leer version.json: {e}")
            return '1.0.0'
    
    def increment_version(self, version, increment_type='patch'):
        """Incrementa la versión según el tipo"""
        try:
            parts = version.split('.')
            if len(parts) != 3:
                raise ValueError("Formato de versión inválido")
                
            major, minor, patch = map(int, parts)
            
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
        except Exception as e:
            print(f"❌ Error al incrementar versión: {e}")
            return None
    
    def update_version_file(self, new_version):
        """Actualiza el archivo version.json"""
        try:
            version_data = {
                "version": new_version,
                "build_date": datetime.now().strftime("%Y-%m-%d"),
                "build_number": int(datetime.now().timestamp()),
                "release_notes": f"Versión {new_version} con mejoras y correcciones",
                "changelog": [
                    "✨ Mejoras en la interfaz de usuario",
                    "🐛 Correcciones de errores menores",
                    "⚡ Optimizaciones de rendimiento",
                    "🔒 Mejoras de seguridad"
                ]
            }
            
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Archivo version.json actualizado a v{new_version}")
            return True
        except Exception as e:
            print(f"❌ Error al actualizar version.json: {e}")
            return False
    
    def run_command(self, command, description=""):
        """Ejecuta un comando y maneja errores"""
        try:
            if description:
                print(f"🔄 {description}...")
            
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                print(f"❌ Error en comando: {command}")
                print(f"Error: {result.stderr}")
                return False
            
            if result.stdout.strip():
                print(f"📝 {result.stdout.strip()}")
            
            return True
        except Exception as e:
            print(f"❌ Error ejecutando comando '{command}': {e}")
            return False
    
    def build_application(self):
        """Compila la aplicación"""
        print("🔨 Compilando aplicación...")
        
        # Verificar que existe build.py
        build_script = self.project_root / 'build.py'
        if not build_script.exists():
            print("❌ No se encontró build.py")
            return False
        
        # Ejecutar build
        return self.run_command(
            f'python "{build_script}"',
            "Ejecutando script de compilación"
        )
    
    def check_git_status(self):
        """Verifica el estado de git"""
        print("📋 Verificando estado de git...")
        
        # Verificar si hay cambios sin commit
        result = subprocess.run(
            ['git', 'status', '--porcelain'], 
            capture_output=True, 
            text=True,
            cwd=self.project_root
        )
        
        if result.stdout.strip():
            print("⚠️ Hay cambios sin commit:")
            print(result.stdout)
            print("✅ Continuando automáticamente con commit...")
        
        return True
    
    def git_operations(self, new_version):
        """Realiza operaciones de git"""
        print("📤 Realizando operaciones de git...")
        
        # Add todos los archivos
        if not self.run_command('git add .', "Agregando archivos"):
            return False
        
        # Commit
        commit_message = f"Release v{new_version}"
        if not self.run_command(f'git commit -m "{commit_message}"', "Creando commit"):
            return False
        
        # Push
        if not self.run_command('git push origin main', "Subiendo cambios"):
            return False
        
        # Crear tag
        tag_name = f"v{new_version}"
        if not self.run_command(f'git tag {tag_name}', f"Creando tag {tag_name}"):
            return False
        
        # Push tag
        if not self.run_command(f'git push origin {tag_name}', f"Subiendo tag {tag_name}"):
            return False
        
        return True
    
    def create_release(self, version_type='patch'):
        """Crea un nuevo release completo"""
        print("🚀 Iniciando proceso de release...")
        print("=" * 50)
        
        # Verificar git
        if not self.check_git_status():
            return False
        
        # Obtener versiones
        current_version = self.get_current_version()
        new_version = self.increment_version(current_version, version_type)
        
        if not new_version:
            return False
        
        print(f"📈 Versión actual: {current_version}")
        print(f"📈 Nueva versión: {new_version}")
        print(f"📈 Tipo de release: {version_type}")
        print()
        
        # Confirmar automáticamente
        print(f"✅ Creando release v{new_version} automáticamente...")
        
        print()
        
        # Actualizar version.json
        if not self.update_version_file(new_version):
            return False
        
        # Compilar aplicación
        if not self.build_application():
            return False
        
        # Operaciones de git
        if not self.git_operations(new_version):
            return False
        
        # Éxito
        print()
        print("=" * 50)
        print(f"🎉 Release v{new_version} creado exitosamente!")
        print(f"🔗 GitHub Actions se ejecutará automáticamente")
        print(f"📥 URL del release: https://github.com/TU-USUARIO/automatizacion-compresion/releases/tag/v{new_version}")
        print()
        print("📋 Próximos pasos:")
        print("1. Ve a GitHub y verifica que GitHub Actions se esté ejecutando")
        print("2. Una vez completado, el release estará disponible")
        print("3. Los usuarios recibirán notificaciones de actualización")
        
        return True

def show_help():
    """Muestra ayuda del script"""
    help_text = """
🚀 Script de Release Automático

Uso:
    python scripts/create_release.py [tipo]

Tipos de release:
    patch   - Incrementa versión patch (1.0.0 → 1.0.1)
    minor   - Incrementa versión minor (1.0.0 → 1.1.0)
    major   - Incrementa versión major (1.0.0 → 2.0.0)

Ejemplos:
    python scripts/create_release.py patch
    python scripts/create_release.py minor
    python scripts/create_release.py major

El script realizará:
    ✅ Incrementar versión en version.json
    ✅ Compilar la aplicación
    ✅ Crear commit y tag en git
    ✅ Subir cambios a GitHub
    ✅ Activar GitHub Actions para crear release
"""
    print(help_text)

def main():
    """Función principal"""
    # Verificar argumentos
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        show_help()
        return
    
    # Obtener tipo de versión
    version_type = 'patch'
    if len(sys.argv) > 1:
        version_type = sys.argv[1].lower()
        if version_type not in ['patch', 'minor', 'major']:
            print(f"❌ Tipo de versión inválido: {version_type}")
            print("Tipos válidos: patch, minor, major")
            return
    
    # Crear release
    manager = ReleaseManager()
    success = manager.create_release(version_type)
    
    if success:
        sys.exit(0)
    else:
        print("❌ Error al crear release")
        sys.exit(1)

if __name__ == '__main__':
    main()