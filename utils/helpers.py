#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funciones Auxiliares - Automatización de Compresión de Archivos

Este módulo contiene funciones de utilidad general para formateo,
conversiones, cálculos y otras operaciones auxiliares.
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import hashlib
import json


class FileUtils:
    """Utilidades para manejo de archivos."""
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Formatea el tamaño de archivo en unidades legibles.
        
        Args:
            size_bytes: Tamaño en bytes
            
        Returns:
            Tamaño formateado (ej: '1.5 MB')
        """
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"
    
    @staticmethod
    def get_file_extension_info(extension: str) -> Dict[str, str]:
        """Obtiene información sobre una extensión de archivo.
        
        Args:
            extension: Extensión del archivo (con o sin punto)
            
        Returns:
            Diccionario con información de la extensión
        """
        # Normalizar extensión
        ext = extension.lower().lstrip('.')
        
        # Mapeo de extensiones a tipos y descripciones
        extension_map = {
            # Documentos
            'pdf': {'type': 'document', 'description': 'Documento PDF', 'icon': '📄'},
            'doc': {'type': 'document', 'description': 'Documento Word', 'icon': '📝'},
            'docx': {'type': 'document', 'description': 'Documento Word', 'icon': '📝'},
            'txt': {'type': 'document', 'description': 'Archivo de texto', 'icon': '📄'},
            'rtf': {'type': 'document', 'description': 'Texto enriquecido', 'icon': '📄'},
            
            # Hojas de cálculo
            'xls': {'type': 'spreadsheet', 'description': 'Hoja Excel', 'icon': '📊'},
            'xlsx': {'type': 'spreadsheet', 'description': 'Hoja Excel', 'icon': '📊'},
            'csv': {'type': 'spreadsheet', 'description': 'Valores separados por comas', 'icon': '📊'},
            
            # Presentaciones
            'ppt': {'type': 'presentation', 'description': 'Presentación PowerPoint', 'icon': '📽️'},
            'pptx': {'type': 'presentation', 'description': 'Presentación PowerPoint', 'icon': '📽️'},
            
            # Imágenes
            'jpg': {'type': 'image', 'description': 'Imagen JPEG', 'icon': '🖼️'},
            'jpeg': {'type': 'image', 'description': 'Imagen JPEG', 'icon': '🖼️'},
            'png': {'type': 'image', 'description': 'Imagen PNG', 'icon': '🖼️'},
            'gif': {'type': 'image', 'description': 'Imagen GIF', 'icon': '🖼️'},
            'bmp': {'type': 'image', 'description': 'Imagen Bitmap', 'icon': '🖼️'},
            'tiff': {'type': 'image', 'description': 'Imagen TIFF', 'icon': '🖼️'},
            'svg': {'type': 'image', 'description': 'Imagen vectorial SVG', 'icon': '🖼️'},
            
            # Audio
            'mp3': {'type': 'audio', 'description': 'Audio MP3', 'icon': '🎵'},
            'wav': {'type': 'audio', 'description': 'Audio WAV', 'icon': '🎵'},
            'flac': {'type': 'audio', 'description': 'Audio FLAC', 'icon': '🎵'},
            
            # Video
            'mp4': {'type': 'video', 'description': 'Video MP4', 'icon': '🎬'},
            'avi': {'type': 'video', 'description': 'Video AVI', 'icon': '🎬'},
            'mkv': {'type': 'video', 'description': 'Video MKV', 'icon': '🎬'},
            
            # Archivos comprimidos
            'zip': {'type': 'archive', 'description': 'Archivo ZIP', 'icon': '📦'},
            'rar': {'type': 'archive', 'description': 'Archivo RAR', 'icon': '📦'},
            '7z': {'type': 'archive', 'description': 'Archivo 7-Zip', 'icon': '📦'},
            'tar': {'type': 'archive', 'description': 'Archivo TAR', 'icon': '📦'},
            'gz': {'type': 'archive', 'description': 'Archivo GZIP', 'icon': '📦'},
        }
        
        return extension_map.get(ext, {
            'type': 'unknown',
            'description': f'Archivo .{ext.upper()}',
            'icon': '📄'
        })
    
    @staticmethod
    def calculate_compression_ratio(original_size: int, compressed_size: int) -> float:
        """Calcula la ratio de compresión.
        
        Args:
            original_size: Tamaño original en bytes
            compressed_size: Tamaño comprimido en bytes
            
        Returns:
            Porcentaje de compresión (0-100)
        """
        if original_size == 0:
            return 0.0
        
        return ((original_size - compressed_size) / original_size) * 100
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """Convierte un nombre de archivo a uno seguro para el sistema.
        
        Args:
            filename: Nombre original del archivo
            
        Returns:
            Nombre de archivo seguro
        """
        # Caracteres no permitidos en nombres de archivo
        invalid_chars = '<>:"/\\|?*'
        
        # Reemplazar caracteres inválidos
        safe_name = filename
        for char in invalid_chars:
            safe_name = safe_name.replace(char, '_')
        
        # Remover espacios múltiples y al inicio/final
        safe_name = ' '.join(safe_name.split())
        
        # Limitar longitud
        if len(safe_name) > 200:
            name_part = safe_name[:190]
            extension = Path(safe_name).suffix
            safe_name = name_part + extension
        
        return safe_name


class TimeUtils:
    """Utilidades para manejo de tiempo y fechas."""
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Formatea una duración en segundos a formato legible.
        
        Args:
            seconds: Duración en segundos
            
        Returns:
            Duración formateada (ej: '2h 30m 15s')
        """
        if seconds < 0:
            return "0s"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")
        
        return " ".join(parts)
    
    @staticmethod
    def estimate_remaining_time(processed: int, total: int, elapsed_time: float) -> float:
        """Estima el tiempo restante basado en el progreso actual.
        
        Args:
            processed: Elementos procesados
            total: Total de elementos
            elapsed_time: Tiempo transcurrido en segundos
            
        Returns:
            Tiempo estimado restante en segundos
        """
        if processed == 0 or total == 0:
            return 0.0
        
        remaining = total - processed
        if remaining <= 0:
            return 0.0
        
        avg_time_per_item = elapsed_time / processed
        return remaining * avg_time_per_item
    
    @staticmethod
    def format_timestamp(timestamp: Optional[datetime] = None, 
                        format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Formatea un timestamp a string.
        
        Args:
            timestamp: Timestamp a formatear (usa actual si es None)
            format_str: Formato de salida
            
        Returns:
            Timestamp formateado
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        return timestamp.strftime(format_str)


class MathUtils:
    """Utilidades matemáticas y de cálculo."""
    
    @staticmethod
    def calculate_percentage(part: float, total: float) -> float:
        """Calcula un porcentaje.
        
        Args:
            part: Parte del total
            total: Total
            
        Returns:
            Porcentaje (0-100)
        """
        if total == 0:
            return 0.0
        return (part / total) * 100
    
    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """Limita un valor entre un mínimo y máximo.
        
        Args:
            value: Valor a limitar
            min_val: Valor mínimo
            max_val: Valor máximo
            
        Returns:
            Valor limitado
        """
        return max(min_val, min(value, max_val))
    
    @staticmethod
    def moving_average(values: List[float], window_size: int = 5) -> List[float]:
        """Calcula promedio móvil de una serie de valores.
        
        Args:
            values: Lista de valores
            window_size: Tamaño de la ventana
            
        Returns:
            Lista con promedios móviles
        """
        if len(values) < window_size:
            return values
        
        averages = []
        for i in range(len(values) - window_size + 1):
            window = values[i:i + window_size]
            avg = sum(window) / len(window)
            averages.append(avg)
        
        return averages


class StringUtils:
    """Utilidades para manejo de strings."""
    
    @staticmethod
    def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
        """Trunca un string a una longitud máxima.
        
        Args:
            text: Texto a truncar
            max_length: Longitud máxima
            suffix: Sufijo a agregar si se trunca
            
        Returns:
            Texto truncado
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def sanitize_string(text: str) -> str:
        """Sanitiza un string removiendo caracteres problemáticos.
        
        Args:
            text: Texto a sanitizar
            
        Returns:
            Texto sanitizado
        """
        # Remover caracteres de control
        sanitized = ''.join(char for char in text if ord(char) >= 32)
        
        # Normalizar espacios
        sanitized = ' '.join(sanitized.split())
        
        return sanitized
    
    @staticmethod
    def generate_unique_id(prefix: str = "") -> str:
        """Genera un ID único.
        
        Args:
            prefix: Prefijo opcional
            
        Returns:
            ID único
        """
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        if prefix:
            return f"{prefix}_{unique_id}"
        
        return unique_id


class ConfigUtils:
    """Utilidades para manejo de configuraciones."""
    
    @staticmethod
    def merge_configs(base_config: Dict[str, Any], 
                     override_config: Dict[str, Any]) -> Dict[str, Any]:
        """Combina dos configuraciones, dando prioridad a la segunda.
        
        Args:
            base_config: Configuración base
            override_config: Configuración que sobrescribe
            
        Returns:
            Configuración combinada
        """
        merged = base_config.copy()
        
        for key, value in override_config.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                merged[key] = ConfigUtils.merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    @staticmethod
    def validate_config_keys(config: Dict[str, Any], 
                           required_keys: List[str]) -> List[str]:
        """Valida que una configuración tenga las claves requeridas.
        
        Args:
            config: Configuración a validar
            required_keys: Claves requeridas
            
        Returns:
            Lista de claves faltantes
        """
        missing_keys = []
        
        for key in required_keys:
            if key not in config:
                missing_keys.append(key)
        
        return missing_keys
    
    @staticmethod
    def export_config_to_json(config: Dict[str, Any], file_path: str) -> bool:
        """Exporta configuración a archivo JSON.
        
        Args:
            config: Configuración a exportar
            file_path: Ruta del archivo
            
        Returns:
            True si se exportó correctamente
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception:
            return False
    
    @staticmethod
    def import_config_from_json(file_path: str) -> Optional[Dict[str, Any]]:
        """Importa configuración desde archivo JSON.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Configuración importada o None si falló
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None


class PerformanceUtils:
    """Utilidades para monitoreo de rendimiento."""
    
    @staticmethod
    def measure_execution_time(func):
        """Decorador para medir tiempo de ejecución de una función.
        
        Args:
            func: Función a medir
            
        Returns:
            Función decorada
        """
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            execution_time = end_time - start_time
            print(f"{func.__name__} ejecutado en {execution_time:.4f} segundos")
            
            return result
        
        return wrapper
    
    @staticmethod
    def get_memory_usage() -> Optional[Dict[str, float]]:
        """Obtiene información de uso de memoria.
        
        Returns:
            Diccionario con información de memoria o None si no está disponible
        """
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss': memory_info.rss / 1024 / 1024,  # MB
                'vms': memory_info.vms / 1024 / 1024,  # MB
                'percent': process.memory_percent()
            }
        except ImportError:
            return None
        except Exception:
            return None
    
    @staticmethod
    def get_cpu_usage() -> Optional[float]:
        """Obtiene el uso de CPU del proceso actual.
        
        Returns:
            Porcentaje de uso de CPU o None si no está disponible
        """
        try:
            import psutil
            process = psutil.Process()
            return process.cpu_percent()
        except ImportError:
            return None
        except Exception:
            return None


def create_progress_bar(current: int, total: int, width: int = 50) -> str:
    """Crea una barra de progreso en texto.
    
    Args:
        current: Progreso actual
        total: Total
        width: Ancho de la barra
        
    Returns:
        Barra de progreso como string
    """
    if total == 0:
        percentage = 0
    else:
        percentage = (current / total) * 100
    
    filled = int(width * current / total) if total > 0 else 0
    bar = '█' * filled + '░' * (width - filled)
    
    return f"[{bar}] {percentage:.1f}% ({current}/{total})"


def get_system_info() -> Dict[str, Any]:
    """Obtiene información del sistema.
    
    Returns:
        Diccionario con información del sistema
    """
    import platform
    
    info = {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.architecture()[0],
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'current_directory': os.getcwd(),
        'user_home': str(Path.home())
    }
    
    try:
        import psutil
        info.update({
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'disk_usage': psutil.disk_usage('/').total if platform.system() != 'Windows' else psutil.disk_usage('C:\\').total
        })
    except ImportError:
        pass
    
    return info