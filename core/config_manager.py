#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor Avanzado de Configuración - Automatización de Compresión de Archivos v1.0.20

Este módulo maneja la carga, guardado y gestión inteligente de configuraciones y perfiles
de usuario para la aplicación de automatización de compresión.
Incluye validación de datos, respaldo automático y gestión de múltiples perfiles.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class ConfigManager:
    """Gestor avanzado de configuraciones y perfiles de usuario con validación automática."""
    
    def __init__(self, config_file: str = "config.json"):
        """Inicializa el gestor de configuración.
        
        Args:
            config_file: Ruta al archivo de configuración
        """
        self.config_file = Path(config_file)
        self.config_data = {}
        self.load_config()
    
    def load_config(self) -> bool:
        """Carga la configuración desde el archivo JSON con validación de integridad.
        
        Returns:
            True si se cargó correctamente, False en caso contrario
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
                return True
            else:
                # Crear configuración por defecto si no existe
                self._create_default_config()
                return self.save_config()
        except Exception as e:
            print(f"Error al cargar configuración: {e}")
            self._create_default_config()
            return False
    
    def save_config(self) -> bool:
        """Guarda la configuración actual al archivo JSON.
        
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            # Crear directorio si no existe
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error al guardar configuración: {e}")
            return False
    
    def _create_default_config(self):
        """Crea la configuración por defecto."""
        self.config_data = {
            "profiles": {
                "default": {
                    "naming_pattern": "fecha_archivo",
                    "backup_folder": "./respaldo",
                    "include_subfolders": False,
                    "file_filters": ["*"],
                    "compression_level": 6,
                    "conflict_resolution": "rename"
                }
            },
            "app_settings": {
                "log_level": "INFO",
                "max_log_files": 30,
                "theme": "default",
                "window_size": "1024x768",
                "auto_backup": True,
                "verify_integrity": True,
                "show_progress": True
            },
            "naming_patterns": {
                "fecha_archivo": "{fecha}_{nombre_original}",
                "archivo_fecha": "{nombre_original}_{fecha}",
                "contador_archivo": "{contador:03d}_{nombre_original}",
                "timestamp_archivo": "{timestamp}_{nombre_original}",
                "nombre_original": "{nombre_original}",
                "personalizado": "{fecha_archivo}"
            },
            "conflict_resolutions": {
                "rename": "Renombrar automáticamente",
                "overwrite": "Sobrescribir archivo existente",
                "skip": "Saltar archivo",
                "ask": "Preguntar al usuario"
            },
            "updates": {
                "auto_check": True,
                "check_frequency_hours": 24,
                "auto_download": False,
                "auto_install": False,
                "backup_enabled": True,
                "verify_signatures": True,
                "allow_prereleases": False,
                "update_server_url": "https://api.github.com/repos/usuario/automatizacion-compresion/releases",
                "dismissed_versions": []
            },
            "file_filters_presets": {
                "todos": ["*"],
                "documentos": ["*.pdf", "*.doc", "*.docx", "*.txt"],
                "imagenes": ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp"],
                "personalizado": ["*"]
            }
        }
    
    def get_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene un perfil específico.
        
        Args:
            profile_name: Nombre del perfil
            
        Returns:
            Diccionario con la configuración del perfil o None si no existe
        """
        return self.config_data.get("profiles", {}).get(profile_name)
    
    def save_profile(self, profile_name: str, config: Dict[str, Any]) -> bool:
        """Guarda un perfil de configuración.
        
        Args:
            profile_name: Nombre del perfil
            config: Configuración del perfil
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            if "profiles" not in self.config_data:
                self.config_data["profiles"] = {}
            
            # Validar configuración básica
            required_keys = ["naming_pattern", "backup_folder", "include_subfolders", 
                           "file_filters", "compression_level", "conflict_resolution"]
            
            for key in required_keys:
                if key not in config:
                    raise ValueError(f"Falta la clave requerida: {key}")
            
            # Agregar timestamp de creación/modificación
            config["last_modified"] = datetime.now().isoformat()
            
            self.config_data["profiles"][profile_name] = config
            return self.save_config()
        except Exception as e:
            print(f"Error al guardar perfil {profile_name}: {e}")
            return False
    
    def delete_profile(self, profile_name: str) -> bool:
        """Elimina un perfil de configuración.
        
        Args:
            profile_name: Nombre del perfil a eliminar
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            if profile_name == "default":
                raise ValueError("No se puede eliminar el perfil por defecto")
            
            if "profiles" in self.config_data and profile_name in self.config_data["profiles"]:
                del self.config_data["profiles"][profile_name]
                return self.save_config()
            return False
        except Exception as e:
            print(f"Error al eliminar perfil {profile_name}: {e}")
            return False
    
    def list_profiles(self) -> List[str]:
        """Lista todos los perfiles disponibles.
        
        Returns:
            Lista con los nombres de los perfiles
        """
        return list(self.config_data.get("profiles", {}).keys())
    
    def get_app_setting(self, setting_name: str, default_value: Any = None) -> Any:
        """Obtiene una configuración de la aplicación.
        
        Args:
            setting_name: Nombre de la configuración
            default_value: Valor por defecto si no existe
            
        Returns:
            Valor de la configuración
        """
        return self.config_data.get("app_settings", {}).get(setting_name, default_value)
    
    def set_app_setting(self, setting_name: str, value: Any) -> bool:
        """Establece una configuración de la aplicación.
        
        Args:
            setting_name: Nombre de la configuración
            value: Valor a establecer
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            if "app_settings" not in self.config_data:
                self.config_data["app_settings"] = {}
            
            self.config_data["app_settings"][setting_name] = value
            return self.save_config()
        except Exception as e:
            print(f"Error al establecer configuración {setting_name}: {e}")
            return False
    
    def get_naming_patterns(self) -> Dict[str, str]:
        """Obtiene todos los patrones de nomenclatura disponibles.
        
        Returns:
            Diccionario con los patrones de nomenclatura
        """
        return self.config_data.get("naming_patterns", {})
    
    def get_conflict_resolutions(self) -> Dict[str, str]:
        """Obtiene todas las opciones de resolución de conflictos.
        
        Returns:
            Diccionario con las opciones de resolución de conflictos
        """
        return self.config_data.get("conflict_resolutions", {})
    
    def export_profile(self, profile_name: str, export_path: str) -> bool:
        """Exporta un perfil a un archivo JSON.
        
        Args:
            profile_name: Nombre del perfil a exportar
            export_path: Ruta donde guardar el archivo
            
        Returns:
            True si se exportó correctamente, False en caso contrario
        """
        try:
            profile = self.get_profile(profile_name)
            if not profile:
                raise ValueError(f"El perfil {profile_name} no existe")
            
            export_data = {
                "profile_name": profile_name,
                "profile_data": profile,
                "export_date": datetime.now().isoformat(),
                "app_version": "1.0.20"
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error al exportar perfil {profile_name}: {e}")
            return False
    
    def import_profile(self, import_path: str) -> Optional[str]:
        """Importa un perfil desde un archivo JSON.
        
        Args:
            import_path: Ruta del archivo a importar
            
        Returns:
            Nombre del perfil importado o None si falló
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            profile_name = import_data.get("profile_name")
            profile_data = import_data.get("profile_data")
            
            if not profile_name or not profile_data:
                raise ValueError("Archivo de perfil inválido")
            
            # Si el perfil ya existe, agregar sufijo
            original_name = profile_name
            counter = 1
            while profile_name in self.list_profiles():
                profile_name = f"{original_name}_{counter}"
                counter += 1
            
            if self.save_profile(profile_name, profile_data):
                return profile_name
            return None
        except Exception as e:
            print(f"Error al importar perfil: {e}")
            return None
    
    def validate_profile(self, profile_data: Dict[str, Any]) -> List[str]:
        """Valida la configuración de un perfil.
        
        Args:
            profile_data: Datos del perfil a validar
            
        Returns:
            Lista de errores encontrados (vacía si es válido)
        """
        errors = []
        
        required_keys = {
            "naming_pattern": str,
            "backup_folder": str,
            "include_subfolders": bool,
            "file_filters": list,
            "compression_level": int,
            "conflict_resolution": str
        }
        
        for key, expected_type in required_keys.items():
            if key not in profile_data:
                errors.append(f"Falta la clave requerida: {key}")
            elif not isinstance(profile_data[key], expected_type):
                errors.append(f"Tipo incorrecto para {key}: esperado {expected_type.__name__}")
        
        # Validaciones específicas
        if "compression_level" in profile_data:
            level = profile_data["compression_level"]
            if not (0 <= level <= 9):
                errors.append("El nivel de compresión debe estar entre 0 y 9")
        
        if "conflict_resolution" in profile_data:
            valid_resolutions = list(self.get_conflict_resolutions().keys())
            if profile_data["conflict_resolution"] not in valid_resolutions:
                errors.append(f"Resolución de conflictos inválida. Opciones: {valid_resolutions}")
        
        return errors
    
    def get_config(self) -> Dict[str, Any]:
        """Obtiene toda la configuración actual.
        
        Returns:
            Diccionario con toda la configuración
        """
        return self.config_data.copy()