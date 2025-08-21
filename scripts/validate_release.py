#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validación de releases
Automatización de Compresión de Archivos

Este script valida que un release esté listo para ser publicado,
verificando la integridad del ejecutable, documentación y configuración.
"""

import json
import subprocess
import sys
import os
import hashlib
from pathlib import Path
from datetime import datetime

class ReleaseValidator:
    """Validador de releases"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0
        
    def log_result(self, description, success, error_msg="", warning_msg="", is_warning=False):
        """Registra el resultado de una validación"""
        self.total_checks += 1
        status = "✅" if success else ("⚠️" if is_warning else "❌")
        print(f"{status} {description}")
        
        if success:
            self.success_count += 1
        elif is_warning:
            if warning_msg:
                self.warnings.append(f"⚠️ {description}: {warning_msg}")
        else:
            if error_msg:
                self.errors.append(f"❌ {description}: {error_msg}")
        
        return success
    
    def validate_executable(self):
        """Valida el ejecutable compilado"""
        print("\n🔍 VALIDANDO EJECUTABLE")
        print("=" * 40)
        
        exe_path = self.project_root / 'dist' / 'AutomatizacionCompresion.exe'
        
        # Verificar que existe
        exists = self.log_result(
            "Ejecutable existe",
            exe_path.exists(),
            "No se encontró AutomatizacionCompresion.exe en dist/"
        )
        
        if not exists:
            return False
        
        # Verificar tamaño
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        size_ok = self.log_result(
            f"Tamaño del ejecutable ({size_mb:.1f} MB)",
            10 < size_mb < 100,  # Entre 10MB y 100MB es razonable
            f"Tamaño inusual: {size_mb:.1f} MB",
            f"Tamaño: {size_mb:.1f} MB (verificar si es correcto)",
            is_warning=True
        )
        
        # Verificar que no está corrupto (intento de ejecución rápida)
        try:
            result = subprocess.run(
                [str(exe_path), '--version'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_root
            )
            
            version_check = self.log_result(
                "Ejecutable responde a --version",
                result.returncode == 0 or "version" in result.stdout.lower(),
                "El ejecutable no responde correctamente",
                "El ejecutable no soporta --version pero puede estar bien",
                is_warning=True
            )
            
        except subprocess.TimeoutExpired:
            self.log_result(
                "Ejecutable no cuelga al iniciar",
                False,
                "El ejecutable se cuelga al iniciar"
            )
        except Exception as e:
            self.log_result(
                "Ejecutable es válido",
                False,
                f"Error al probar ejecutable: {e}"
            )
        
        # Calcular hash para integridad
        try:
            with open(exe_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            print(f"📋 SHA256: {file_hash[:16]}...")
            
            # Guardar hash para referencia
            hash_file = self.project_root / 'dist' / 'AutomatizacionCompresion.exe.sha256'
            with open(hash_file, 'w') as f:
                f.write(f"{file_hash}  AutomatizacionCompresion.exe\n")
            
            self.log_result(
                "Hash SHA256 generado",
                True
            )
            
        except Exception as e:
            self.log_result(
                "Generación de hash",
                False,
                f"Error al generar hash: {e}"
            )
        
        return True
    
    def validate_version_consistency(self):
        """Valida consistencia de versiones"""
        print("\n🔢 VALIDANDO CONSISTENCIA DE VERSIONES")
        print("=" * 40)
        
        versions = {}
        
        # version.json
        version_file = self.project_root / 'version.json'
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                versions['version.json'] = version_data.get('version', 'N/A')
                
                self.log_result(
                    "version.json es válido",
                    'version' in version_data,
                    "version.json no contiene campo 'version'"
                )
                
            except Exception as e:
                self.log_result(
                    "version.json es legible",
                    False,
                    f"Error al leer version.json: {e}"
                )
        
        # config.json
        config_file = self.project_root / 'config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                if 'app_settings' in config_data and 'version' in config_data['app_settings']:
                    versions['config.json'] = config_data['app_settings']['version']
                
                self.log_result(
                    "config.json es válido",
                    True
                )
                
            except Exception as e:
                self.log_result(
                    "config.json es legible",
                    False,
                    f"Error al leer config.json: {e}"
                )
        
        # Git tags
        try:
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                git_tag = result.stdout.strip()
                versions['git_tag'] = git_tag
                
                self.log_result(
                    f"Último tag de Git: {git_tag}",
                    True
                )
            
        except Exception:
            self.log_result(
                "Git tag disponible",
                False,
                "No se pudo obtener el último tag de Git",
                is_warning=True
            )
        
        # Verificar consistencia
        if len(versions) > 1:
            version_values = list(versions.values())
            all_same = all(v == version_values[0] for v in version_values)
            
            self.log_result(
                "Versiones son consistentes",
                all_same,
                f"Versiones inconsistentes: {versions}"
            )
            
            if all_same:
                print(f"📋 Versión consistente: {version_values[0]}")
        
        return True
    
    def validate_documentation(self):
        """Valida la documentación"""
        print("\n📖 VALIDANDO DOCUMENTACIÓN")
        print("=" * 40)
        
        required_docs = [
            ('README.md', 'Documentación principal'),
            ('MANUAL_USUARIO.md', 'Manual de usuario'),
            ('FAQ_ACTUALIZACIONES.md', 'Preguntas frecuentes'),
            ('CHANGELOG.md', 'Historial de cambios'),
            ('LICENSE', 'Archivo de licencia'),
            ('GUIA_GITHUB.md', 'Guía de GitHub')
        ]
        
        for filename, description in required_docs:
            file_path = self.project_root / filename
            exists = file_path.exists()
            
            if exists:
                # Verificar que no esté vacío
                try:
                    content = file_path.read_text(encoding='utf-8')
                    not_empty = len(content.strip()) > 100  # Al menos 100 caracteres
                    
                    self.log_result(
                        f"{description} ({filename})",
                        not_empty,
                        f"{filename} está vacío o muy corto"
                    )
                    
                except Exception as e:
                    self.log_result(
                        f"{description} ({filename})",
                        False,
                        f"Error al leer {filename}: {e}"
                    )
            else:
                self.log_result(
                    f"{description} ({filename})",
                    False,
                    f"Archivo {filename} no encontrado"
                )
        
        return True
    
    def validate_github_configuration(self):
        """Valida la configuración de GitHub"""
        print("\n⚙️ VALIDANDO CONFIGURACIÓN GITHUB")
        print("=" * 40)
        
        # GitHub Actions workflow
        workflow_file = self.project_root / '.github' / 'workflows' / 'release.yml'
        self.log_result(
            "Workflow de GitHub Actions",
            workflow_file.exists(),
            "Archivo .github/workflows/release.yml no encontrado"
        )
        
        # .gitignore
        gitignore_file = self.project_root / '.gitignore'
        self.log_result(
            "Archivo .gitignore",
            gitignore_file.exists(),
            "Archivo .gitignore no encontrado",
            is_warning=True
        )
        
        # Verificar configuración de Git
        try:
            # Remote origin
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                origin_url = result.stdout.strip()
                is_github = 'github.com' in origin_url
                
                self.log_result(
                    f"Remote origin configurado ({origin_url})",
                    is_github,
                    "Remote origin no apunta a GitHub",
                    "Remote origin no es de GitHub",
                    is_warning=not is_github
                )
            else:
                self.log_result(
                    "Remote origin configurado",
                    False,
                    "No se encontró remote origin"
                )
        
        except Exception as e:
            self.log_result(
                "Configuración de Git",
                False,
                f"Error al verificar Git: {e}"
            )
        
        return True
    
    def validate_scripts(self):
        """Valida los scripts de automatización"""
        print("\n🔧 VALIDANDO SCRIPTS")
        print("=" * 40)
        
        scripts = [
            ('scripts/create_release.py', 'Script de creación de releases'),
            ('scripts/validate_environment.py', 'Script de validación de entorno'),
            ('build.py', 'Script de compilación')
        ]
        
        for script_path, description in scripts:
            file_path = self.project_root / script_path
            exists = file_path.exists()
            
            if exists:
                # Verificar que es ejecutable Python
                try:
                    content = file_path.read_text(encoding='utf-8')
                    is_python = content.startswith('#!') and 'python' in content[:50]
                    has_main = 'def main(' in content or 'if __name__ == "__main__"' in content
                    
                    self.log_result(
                        f"{description}",
                        is_python and has_main,
                        f"{script_path} no parece ser un script Python válido"
                    )
                    
                except Exception as e:
                    self.log_result(
                        f"{description}",
                        False,
                        f"Error al leer {script_path}: {e}"
                    )
            else:
                self.log_result(
                    f"{description}",
                    False,
                    f"Script {script_path} no encontrado"
                )
        
        return True
    
    def generate_release_report(self):
        """Genera un reporte del release"""
        print("\n📋 GENERANDO REPORTE DE RELEASE")
        print("=" * 40)
        
        try:
            # Información básica
            version_file = self.project_root / 'version.json'
            version_info = {}
            
            if version_file.exists():
                with open(version_file, 'r', encoding='utf-8') as f:
                    version_info = json.load(f)
            
            # Información del ejecutable
            exe_path = self.project_root / 'dist' / 'AutomatizacionCompresion.exe'
            exe_info = {}
            
            if exe_path.exists():
                stat = exe_path.stat()
                exe_info = {
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            
            # Crear reporte
            report = {
                'validation_date': datetime.now().isoformat(),
                'version_info': version_info,
                'executable_info': exe_info,
                'validation_results': {
                    'total_checks': self.total_checks,
                    'successful_checks': self.success_count,
                    'errors': len(self.errors),
                    'warnings': len(self.warnings)
                },
                'errors': self.errors,
                'warnings': self.warnings,
                'ready_for_release': len(self.errors) == 0
            }
            
            # Guardar reporte
            report_file = self.project_root / 'release_validation_report.json'
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.log_result(
                "Reporte de validación generado",
                True
            )
            
            print(f"📄 Reporte guardado en: {report_file}")
            
        except Exception as e:
            self.log_result(
                "Generación de reporte",
                False,
                f"Error al generar reporte: {e}"
            )
    
    def show_summary(self):
        """Muestra el resumen de la validación"""
        print("\n" + "=" * 50)
        print("📋 RESUMEN DE VALIDACIÓN DE RELEASE")
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
                print("🎉 ¡Release listo para publicación!")
                print("✅ Todas las validaciones pasaron exitosamente")
                print("🚀 Puedes proceder con la publicación del release")
            else:
                print("✅ Release listo con advertencias menores")
                print("⚠️ Revisa las advertencias pero puedes continuar")
                print("🚀 El release puede ser publicado")
            return True
        else:
            print("❌ Release NO está listo para publicación")
            print("🔧 Corrige los errores antes de publicar")
            print("⛔ NO publiques el release hasta resolver los problemas")
            return False
    
    def run_validation(self):
        """Ejecuta todas las validaciones"""
        print("🔍 VALIDADOR DE RELEASES")
        print("=" * 50)
        print("Verificando que el release esté listo para publicación...")
        
        # Ejecutar todas las validaciones
        self.validate_executable()
        self.validate_version_consistency()
        self.validate_documentation()
        self.validate_github_configuration()
        self.validate_scripts()
        self.generate_release_report()
        
        # Mostrar resumen
        return self.show_summary()

def main():
    """Función principal"""
    validator = ReleaseValidator()
    success = validator.run_validation()
    
    if success:
        print("\n🚀 Próximos pasos para publicar:")
        print("   1. python scripts/create_release.py [patch|minor|major]")
        print("   2. Verificar que GitHub Actions se ejecute correctamente")
        print("   3. Confirmar que el release esté disponible en GitHub")
        sys.exit(0)
    else:
        print("\n🔧 Corrige los errores antes de continuar")
        print("   Revisa el reporte: release_validation_report.json")
        sys.exit(1)

if __name__ == '__main__':
    main()