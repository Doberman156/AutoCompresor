#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validadores - Automatización de Compresión de Archivos

Este módulo contiene funciones de validación para entrada de usuario,
rutas de archivos, configuraciones y otros datos del sistema.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import string


class ValidationError(Exception):
    """Excepción personalizada para errores de validación."""
    pass


class PathValidator:
    """Validador para rutas de archivos y directorios."""
    
    @staticmethod
    def validate_directory_path(path: str) -> Tuple[bool, str]:
        """Valida una ruta de directorio.
        
        Args:
            path: Ruta a validar
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if not path or not path.strip():
            return False, "La ruta no puede estar vacía"
        
        try:
            path_obj = Path(path)
            
            # Verificar caracteres inválidos (compatible con Windows)
            if os.name == 'nt':  # Windows
                # En Windows, ':' es válido solo después de la letra de unidad
                invalid_chars = '<>"|?*'
                # Verificar si hay ':' en posiciones inválidas
                colon_positions = [i for i, char in enumerate(path) if char == ':']
                for pos in colon_positions:
                    # ':' es válido solo en posición 1 (C:) o en UNC paths (\\server:port)
                    if pos != 1 and not (pos > 2 and path.startswith('\\\\')):
                        return False, "La ruta contiene ':' en posición inválida"
            else:  # Unix/Linux/Mac
                invalid_chars = '<>:"|?*'
            
            # Verificar otros caracteres inválidos
            for char in invalid_chars:
                if char in path:
                    return False, f"La ruta contiene caracteres inválidos: {char}"
            
            # Verificar longitud máxima (Windows tiene límite de 260 caracteres)
            if os.name == 'nt' and len(str(path_obj.resolve())) > 260:
                return False, "La ruta es demasiado larga (máximo 260 caracteres)"
            
            # Verificar si existe
            if not path_obj.exists():
                return False, "El directorio no existe"
            
            # Verificar si es directorio
            if not path_obj.is_dir():
                return False, "La ruta no es un directorio"
            
            # Verificar permisos
            if not os.access(path_obj, os.R_OK):
                return False, "Sin permisos de lectura en el directorio"
            
            return True, ""
        
        except Exception as e:
            return False, f"Error al validar ruta: {e}"
    
    @staticmethod
    def validate_file_path(path: str) -> Tuple[bool, str]:
        """Valida una ruta de archivo.
        
        Args:
            path: Ruta a validar
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if not path or not path.strip():
            return False, "La ruta no puede estar vacía"
        
        try:
            path_obj = Path(path)
            
            # Verificar caracteres inválidos (compatible con Windows)
            if os.name == 'nt':  # Windows
                # En Windows, ':' es válido solo después de la letra de unidad
                invalid_chars = '<>"|?*'
                # Verificar si hay ':' en posiciones inválidas
                colon_positions = [i for i, char in enumerate(path) if char == ':']
                for pos in colon_positions:
                    # ':' es válido solo en posición 1 (C:) o en UNC paths (\\server:port)
                    if pos != 1 and not (pos > 2 and path.startswith('\\\\')):
                        return False, "La ruta contiene ':' en posición inválida"
            else:  # Unix/Linux/Mac
                invalid_chars = '<>:"|?*'
            
            # Verificar otros caracteres inválidos
            for char in invalid_chars:
                if char in path:
                    return False, f"La ruta contiene caracteres inválidos: {char}"
            
            # Verificar si existe
            if not path_obj.exists():
                return False, "El archivo no existe"
            
            # Verificar si es archivo
            if not path_obj.is_file():
                return False, "La ruta no es un archivo"
            
            # Verificar permisos
            if not os.access(path_obj, os.R_OK):
                return False, "Sin permisos de lectura en el archivo"
            
            return True, ""
        
        except Exception as e:
            return False, f"Error al validar archivo: {e}"
    
    @staticmethod
    def can_create_directory(path: str) -> Tuple[bool, str]:
        """Verifica si se puede crear un directorio en la ruta especificada.
        
        Args:
            path: Ruta donde crear el directorio
            
        Returns:
            Tupla (se_puede_crear, mensaje_error)
        """
        try:
            path_obj = Path(path)
            
            # Si ya existe, verificar si es directorio
            if path_obj.exists():
                if path_obj.is_dir():
                    return True, ""
                else:
                    return False, "Ya existe un archivo con ese nombre"
            
            # Verificar directorio padre
            parent = path_obj.parent
            if not parent.exists():
                return False, "El directorio padre no existe"
            
            # Verificar permisos de escritura en el padre
            if not os.access(parent, os.W_OK):
                return False, "Sin permisos de escritura en el directorio padre"
            
            return True, ""
        
        except Exception as e:
            return False, f"Error al verificar creación de directorio: {e}"


class ConfigValidator:
    """Validador para configuraciones de la aplicación."""
    
    @staticmethod
    def validate_compression_level(level: int) -> Tuple[bool, str]:
        """Valida el nivel de compresión.
        
        Args:
            level: Nivel de compresión (0-9)
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if not isinstance(level, int):
            return False, "El nivel de compresión debe ser un número entero"
        
        if not (0 <= level <= 9):
            return False, "El nivel de compresión debe estar entre 0 y 9"
        
        return True, ""
    
    @staticmethod
    def validate_naming_pattern(pattern: str, available_patterns: List[str]) -> Tuple[bool, str]:
        """Valida un patrón de nomenclatura.
        
        Args:
            pattern: Patrón a validar
            available_patterns: Patrones disponibles
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if not pattern or not pattern.strip():
            return False, "El patrón no puede estar vacío"
        
        if pattern not in available_patterns and pattern != 'personalizado':
            return False, f"Patrón inválido. Opciones: {', '.join(available_patterns)}"
        
        return True, ""
    
    @staticmethod
    def validate_custom_pattern(pattern: str) -> Tuple[bool, str]:
        """Valida un patrón personalizado de nomenclatura.
        
        Args:
            pattern: Patrón personalizado
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if not pattern or not pattern.strip():
            return False, "El patrón personalizado no puede estar vacío"
        
        # Verificar caracteres inválidos para nombres de archivo
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            if char in pattern:
                return False, f"El patrón contiene caracteres inválidos: {char}"
        
        # Verificar que contenga al menos una variable
        if '{' not in pattern or '}' not in pattern:
            return False, "El patrón debe contener al menos una variable (ej: {nombre_original})"
        
        # Verificar variables válidas
        valid_vars = {
            'fecha', 'fecha_corta', 'hora', 'timestamp', 
            'nombre_original', 'contador', 'extension_original'
        }
        
        # Extraer variables del patrón
        import re
        variables = re.findall(r'\{([^}]+)\}', pattern)
        
        for var in variables:
            # Remover formato si existe (ej: contador:03d -> contador)
            var_name = var.split(':')[0]
            if var_name not in valid_vars:
                return False, f"Variable inválida: {var_name}. Variables válidas: {', '.join(valid_vars)}"
        
        return True, ""
    
    @staticmethod
    def validate_file_filters(filters: List[str]) -> Tuple[bool, str]:
        """Valida una lista de filtros de archivo.
        
        Args:
            filters: Lista de filtros (ej: ['*.pdf', '*.jpg'])
            
        Returns:
            Tupla (es_válidos, mensaje_error)
        """
        if not filters:
            return False, "La lista de filtros no puede estar vacía"
        
        for filter_pattern in filters:
            if not filter_pattern or not filter_pattern.strip():
                return False, "Los filtros no pueden estar vacíos"
            
            # Verificar formato básico
            if filter_pattern != '*' and not filter_pattern.startswith('*.'):
                return False, f"Formato de filtro inválido: {filter_pattern}. Use formato *.extensión"
        
        return True, ""


class InputValidator:
    """Validador para entrada de usuario."""
    
    @staticmethod
    def validate_profile_name(name: str) -> Tuple[bool, str]:
        """Valida un nombre de perfil.
        
        Args:
            name: Nombre del perfil
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if not name or not name.strip():
            return False, "El nombre del perfil no puede estar vacío"
        
        name = name.strip()
        
        # Verificar longitud
        if len(name) < 2:
            return False, "El nombre debe tener al menos 2 caracteres"
        
        if len(name) > 50:
            return False, "El nombre no puede tener más de 50 caracteres"
        
        # Verificar caracteres válidos (letras, números, espacios, guiones)
        valid_chars = string.ascii_letters + string.digits + ' -_'
        if not all(char in valid_chars for char in name):
            return False, "El nombre solo puede contener letras, números, espacios y guiones"
        
        # Verificar que no sea un nombre reservado
        reserved_names = ['default', 'config', 'settings', 'system']
        if name.lower() in reserved_names:
            return False, f"'{name}' es un nombre reservado"
        
        return True, ""
    
    @staticmethod
    def validate_numeric_input(value: str, min_val: float = None, 
                             max_val: float = None) -> Tuple[bool, str, Optional[float]]:
        """Valida entrada numérica.
        
        Args:
            value: Valor a validar
            min_val: Valor mínimo permitido
            max_val: Valor máximo permitido
            
        Returns:
            Tupla (es_válido, mensaje_error, valor_convertido)
        """
        if not value or not value.strip():
            return False, "El valor no puede estar vacío", None
        
        try:
            num_value = float(value.strip())
            
            if min_val is not None and num_value < min_val:
                return False, f"El valor debe ser mayor o igual a {min_val}", None
            
            if max_val is not None and num_value > max_val:
                return False, f"El valor debe ser menor o igual a {max_val}", None
            
            return True, "", num_value
        
        except ValueError:
            return False, "El valor debe ser un número válido", None


class SystemValidator:
    """Validador para recursos del sistema."""
    
    @staticmethod
    def validate_disk_space(path: str, required_space: int) -> Tuple[bool, str]:
        """Valida que haya suficiente espacio en disco.
        
        Args:
            path: Ruta a verificar
            required_space: Espacio requerido en bytes
            
        Returns:
            Tupla (hay_espacio, mensaje_error)
        """
        try:
            import shutil
            
            # Obtener espacio libre
            free_space = shutil.disk_usage(path).free
            
            if free_space < required_space:
                return False, f"Espacio insuficiente. Requerido: {required_space}, Disponible: {free_space}"
            
            return True, ""
        
        except Exception as e:
            return False, f"Error al verificar espacio en disco: {e}"
    
    @staticmethod
    def validate_memory_usage() -> Tuple[bool, str]:
        """Valida el uso de memoria del sistema.
        
        Returns:
            Tupla (memoria_ok, mensaje_error)
        """
        try:
            import psutil
            
            # Obtener uso de memoria
            memory = psutil.virtual_memory()
            
            # Verificar que haya al menos 100MB libres
            min_free_memory = 100 * 1024 * 1024  # 100MB
            
            if memory.available < min_free_memory:
                return False, "Memoria insuficiente para la operación"
            
            return True, ""
        
        except ImportError:
            # Si psutil no está disponible, asumir que está bien
            return True, ""
        except Exception as e:
            return False, f"Error al verificar memoria: {e}"


def validate_compression_config(config: Dict[str, Any]) -> List[str]:
    """Valida una configuración completa de compresión.
    
    Args:
        config: Diccionario con configuración
        
    Returns:
        Lista de errores encontrados
    """
    errors = []
    
    # Validar carpeta origen
    if 'source_folder' in config:
        valid, error = PathValidator.validate_directory_path(config['source_folder'])
        if not valid:
            errors.append(f"Carpeta origen: {error}")
    else:
        errors.append("Falta especificar carpeta origen")
    
    # Validar carpeta de respaldo
    if 'backup_folder' in config:
        valid, error = PathValidator.can_create_directory(config['backup_folder'])
        if not valid:
            errors.append(f"Carpeta de respaldo: {error}")
    else:
        errors.append("Falta especificar carpeta de respaldo")
    
    # Validar nivel de compresión
    if 'compression_level' in config:
        valid, error = ConfigValidator.validate_compression_level(config['compression_level'])
        if not valid:
            errors.append(error)
    
    # Validar filtros de archivo
    if 'file_filters' in config:
        valid, error = ConfigValidator.validate_file_filters(config['file_filters'])
        if not valid:
            errors.append(error)
    
    # Validar patrón personalizado si se especifica
    if config.get('naming_pattern') == 'personalizado':
        if 'custom_pattern' in config:
            valid, error = ConfigValidator.validate_custom_pattern(config['custom_pattern'])
            if not valid:
                errors.append(f"Patrón personalizado: {error}")
        else:
            errors.append("Falta especificar patrón personalizado")
    
    return errors