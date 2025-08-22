#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Operaciones Específicas de Renombrado
Parte del sistema de Automatización de Compresión

Este módulo contiene operaciones específicas, plantillas predefinidas,
y funciones helper para el renombrado masivo de archivos.
"""

import os
import re
import string
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any


class RenameTemplates:
    """Plantillas predefinidas para renombrado común"""
    
    TEMPLATES = {
        'fotos_fecha': {
            'name': 'Fotos con Fecha',
            'description': 'IMG_YYYYMMDD_001.jpg',
            'operations': [
                {'type': 'replace', 'old': '', 'new': 'IMG_', 'enabled': True},
                {'type': 'numbering', 'start': 1, 'padding': 3, 'enabled': True}
            ]
        },
        'documentos_trabajo': {
            'name': 'Documentos de Trabajo',
            'description': 'DOC_nombre_original.pdf',
            'operations': [
                {'type': 'prefix', 'value': 'DOC_', 'enabled': True},
                {'type': 'case', 'case_type': 'lower', 'enabled': True}
            ]
        },
        'backup_numerado': {
            'name': 'Backup Numerado',
            'description': '001_archivo_backup.zip',
            'operations': [
                {'type': 'numbering', 'start': 1, 'padding': 3, 'enabled': True},
                {'type': 'suffix', 'value': '_backup', 'enabled': True}
            ]
        },
        'limpieza_basica': {
            'name': 'Limpieza Básica',
            'description': 'Elimina espacios y caracteres especiales',
            'operations': [
                {'type': 'replace', 'old': ' ', 'new': '_', 'enabled': True},
                {'type': 'remove', 'value': '()', 'enabled': True},
                {'type': 'remove', 'value': '[]', 'enabled': True},
                {'type': 'case', 'case_type': 'lower', 'enabled': True}
            ]
        },
        'version_control': {
            'name': 'Control de Versiones',
            'description': 'archivo_v001.ext',
            'operations': [
                {'type': 'suffix', 'value': '_v', 'enabled': True},
                {'type': 'numbering', 'start': 1, 'padding': 3, 'enabled': True}
            ]
        }
    }
    
    @classmethod
    def get_template(cls, template_name: str) -> Optional[Dict]:
        """Obtiene una plantilla por nombre"""
        return cls.TEMPLATES.get(template_name)
    
    @classmethod
    def get_all_templates(cls) -> Dict[str, Dict]:
        """Obtiene todas las plantillas disponibles"""
        return cls.TEMPLATES.copy()
    
    @classmethod
    def get_template_names(cls) -> List[str]:
        """Obtiene los nombres de todas las plantillas"""
        return list(cls.TEMPLATES.keys())


class FileNameValidator:
    """Validador de nombres de archivo"""
    
    # Caracteres no permitidos en Windows
    INVALID_CHARS = r'[<>:"/\\|?*]'
    RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    @classmethod
    def is_valid_filename(cls, filename: str) -> Tuple[bool, str]:
        """Valida si un nombre de archivo es válido"""
        if not filename or filename.strip() == "":
            return False, "El nombre no puede estar vacío"
        
        # Verificar caracteres inválidos
        if re.search(cls.INVALID_CHARS, filename):
            return False, "Contiene caracteres no permitidos: < > : \" / \\ | ? *"
        
        # Verificar nombres reservados
        name_without_ext = os.path.splitext(filename)[0].upper()
        if name_without_ext in cls.RESERVED_NAMES:
            return False, f"'{name_without_ext}' es un nombre reservado del sistema"
        
        # Verificar longitud
        if len(filename) > 255:
            return False, "El nombre es demasiado largo (máximo 255 caracteres)"
        
        # Verificar que no termine en punto o espacio
        if filename.endswith('.') or filename.endswith(' '):
            return False, "El nombre no puede terminar en punto o espacio"
        
        return True, "Nombre válido"
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Limpia un nombre de archivo para hacerlo válido"""
        # Eliminar caracteres inválidos
        sanitized = re.sub(cls.INVALID_CHARS, '_', filename)
        
        # Eliminar espacios al inicio y final
        sanitized = sanitized.strip()
        
        # Eliminar puntos al final
        sanitized = sanitized.rstrip('.')
        
        # Verificar nombres reservados
        name, ext = os.path.splitext(sanitized)
        if name.upper() in cls.RESERVED_NAMES:
            sanitized = f"{name}_file{ext}"
        
        # Limitar longitud
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            max_name_length = 255 - len(ext)
            sanitized = name[:max_name_length] + ext
        
        return sanitized or "unnamed_file"


class TextProcessor:
    """Procesador de texto para operaciones avanzadas"""
    
    @staticmethod
    def remove_accents(text: str) -> str:
        """Elimina acentos y caracteres especiales"""
        replacements = {
            'á': 'a', 'à': 'a', 'ä': 'a', 'â': 'a', 'ā': 'a', 'ã': 'a',
            'é': 'e', 'è': 'e', 'ë': 'e', 'ê': 'e', 'ē': 'e',
            'í': 'i', 'ì': 'i', 'ï': 'i', 'î': 'i', 'ī': 'i',
            'ó': 'o', 'ò': 'o', 'ö': 'o', 'ô': 'o', 'ō': 'o', 'õ': 'o',
            'ú': 'u', 'ù': 'u', 'ü': 'u', 'û': 'u', 'ū': 'u',
            'ñ': 'n', 'ç': 'c',
            'Á': 'A', 'À': 'A', 'Ä': 'A', 'Â': 'A', 'Ā': 'A', 'Ã': 'A',
            'É': 'E', 'È': 'E', 'Ë': 'E', 'Ê': 'E', 'Ē': 'E',
            'Í': 'I', 'Ì': 'I', 'Ï': 'I', 'Î': 'I', 'Ī': 'I',
            'Ó': 'O', 'Ò': 'O', 'Ö': 'O', 'Ô': 'O', 'Ō': 'O', 'Õ': 'O',
            'Ú': 'U', 'Ù': 'U', 'Ü': 'U', 'Û': 'U', 'Ū': 'U',
            'Ñ': 'N', 'Ç': 'C'
        }
        
        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
        return result
    
    @staticmethod
    def to_snake_case(text: str) -> str:
        """Convierte texto a snake_case"""
        # Reemplazar espacios y guiones por underscore
        text = re.sub(r'[\s-]+', '_', text)
        # Insertar underscore antes de mayúsculas
        text = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)
        # Convertir a minúsculas
        return text.lower()
    
    @staticmethod
    def to_camel_case(text: str) -> str:
        """Convierte texto a camelCase"""
        words = re.split(r'[\s_-]+', text)
        if not words:
            return text
        
        result = words[0].lower()
        for word in words[1:]:
            if word:
                result += word.capitalize()
        return result
    
    @staticmethod
    def to_pascal_case(text: str) -> str:
        """Convierte texto a PascalCase"""
        words = re.split(r'[\s_-]+', text)
        return ''.join(word.capitalize() for word in words if word)
    
    @staticmethod
    def remove_numbers(text: str) -> str:
        """Elimina todos los números del texto"""
        return re.sub(r'\d+', '', text)
    
    @staticmethod
    def remove_special_chars(text: str, keep_chars: str = '') -> str:
        """Elimina caracteres especiales, manteniendo los especificados"""
        pattern = f'[^a-zA-Z0-9\s{re.escape(keep_chars)}]'
        return re.sub(pattern, '', text)
    
    @staticmethod
    def normalize_spaces(text: str) -> str:
        """Normaliza espacios múltiples a uno solo"""
        return re.sub(r'\s+', ' ', text).strip()


class DateTimeFormatter:
    """Formateador de fecha y hora para nombres de archivo"""
    
    FORMATS = {
        'YYYYMMDD': '%Y%m%d',
        'YYYY-MM-DD': '%Y-%m-%d',
        'DD-MM-YYYY': '%d-%m-%Y',
        'MMDDYYYY': '%m%d%Y',
        'YYYYMMDD_HHMMSS': '%Y%m%d_%H%M%S',
        'YYYY-MM-DD_HH-MM-SS': '%Y-%m-%d_%H-%M-%S',
        'timestamp': 'timestamp'
    }
    
    @classmethod
    def format_date(cls, date: datetime, format_name: str) -> str:
        """Formatea una fecha según el formato especificado"""
        if format_name == 'timestamp':
            return str(int(date.timestamp()))
        
        format_str = cls.FORMATS.get(format_name, '%Y%m%d')
        return date.strftime(format_str)
    
    @classmethod
    def get_current_date(cls, format_name: str) -> str:
        """Obtiene la fecha actual en el formato especificado"""
        return cls.format_date(datetime.now(), format_name)
    
    @classmethod
    def get_available_formats(cls) -> Dict[str, str]:
        """Obtiene todos los formatos disponibles"""
        return cls.FORMATS.copy()


class NumberingHelper:
    """Helper para operaciones de numeración"""
    
    @staticmethod
    def generate_sequence(start: int, count: int, padding: int = 3, 
                         prefix: str = '', suffix: str = '') -> List[str]:
        """Genera una secuencia numerada"""
        sequence = []
        for i in range(count):
            number = start + i
            padded_number = str(number).zfill(padding)
            sequence.append(f"{prefix}{padded_number}{suffix}")
        return sequence
    
    @staticmethod
    def extract_numbers(filename: str) -> List[int]:
        """Extrae todos los números de un nombre de archivo"""
        numbers = re.findall(r'\d+', filename)
        return [int(num) for num in numbers]
    
    @staticmethod
    def increment_number(filename: str, increment: int = 1) -> str:
        """Incrementa el último número encontrado en el nombre"""
        def replace_last_number(match):
            number = int(match.group())
            return str(number + increment)
        
        # Buscar el último número en el archivo
        pattern = r'(\d+)(?!.*\d)'
        return re.sub(pattern, replace_last_number, filename)
    
    @staticmethod
    def pad_numbers(filename: str, target_length: int) -> str:
        """Agrega ceros a la izquierda de todos los números en el nombre de archivo
        
        Args:
            filename: Nombre del archivo (ej: 'RIPS_M7738.json')
            target_length: Longitud total deseada para los números (ej: 6)
            
        Returns:
            Nombre con números con padding (ej: 'RIPS_M007738.json')
        """
        def pad_number_match(match):
            number = match.group()
            # SIEMPRE aplicar padding a la longitud especificada
            return number.zfill(target_length)
        
        # Buscar todos los números y aplicar padding
        pattern = r'\d+'
        return re.sub(pattern, pad_number_match, filename)
    
    @staticmethod
    def remove_padding(filename: str) -> str:
        """Elimina ceros a la izquierda de todos los números en el nombre de archivo
        
        Args:
            filename: Nombre del archivo (ej: 'RIPS_M007738.json')
            
        Returns:
            Nombre sin ceros a la izquierda (ej: 'RIPS_M7738.json')
        """
        def remove_leading_zeros(match):
            number = match.group()
            # Eliminar ceros a la izquierda, pero mantener al menos un dígito
            return str(int(number))
        
        # Buscar todos los números y eliminar ceros a la izquierda
        pattern = r'\d+'
        return re.sub(pattern, remove_leading_zeros, filename)
    
    @staticmethod
    def pad_specific_number(filename: str, number_position: int, target_length: int) -> str:
        """Agrega ceros a un número específico por posición
        
        Args:
            filename: Nombre del archivo
            number_position: Posición del número (1 = primer número, 2 = segundo, etc.)
            target_length: Longitud total deseada
            
        Returns:
            Nombre con el número específico con padding
        """
        numbers = re.findall(r'\d+', filename)
        if number_position <= 0 or number_position > len(numbers):
            return filename
        
        # Obtener el número objetivo
        target_number = numbers[number_position - 1]
        padded_number = target_number.zfill(target_length)
        
        # Reemplazar solo la primera ocurrencia del número objetivo
        count = 0
        def replace_nth_occurrence(match):
            nonlocal count
            count += 1
            if count == number_position:
                return padded_number
            return match.group()
        
        pattern = r'\d+'
        return re.sub(pattern, replace_nth_occurrence, filename)


class ConflictResolver:
    """Resolvedor de conflictos de nombres"""
    
    @staticmethod
    def resolve_duplicate(base_name: str, existing_names: List[str], 
                         strategy: str = 'number') -> str:
        """Resuelve conflictos de nombres duplicados"""
        if base_name not in existing_names:
            return base_name
        
        name, ext = os.path.splitext(base_name)
        
        if strategy == 'number':
            counter = 1
            while True:
                new_name = f"{name}_{counter}{ext}"
                if new_name not in existing_names:
                    return new_name
                counter += 1
        
        elif strategy == 'timestamp':
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"{name}_{timestamp}{ext}"
        
        elif strategy == 'random':
            import random
            import string
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            return f"{name}_{random_str}{ext}"
        
        return base_name
    
    @staticmethod
    def check_path_conflicts(file_paths: List[str]) -> Dict[str, List[str]]:
        """Verifica conflictos en una lista de rutas de archivo"""
        conflicts = {}
        name_counts = {}
        
        for path in file_paths:
            filename = os.path.basename(path)
            if filename in name_counts:
                name_counts[filename] += 1
                if filename not in conflicts:
                    conflicts[filename] = []
                conflicts[filename].append(path)
            else:
                name_counts[filename] = 1
        
        return conflicts


# Funciones de utilidad
def get_file_info(file_path: str) -> Dict[str, Any]:
    """Obtiene información detallada de un archivo"""
    path = Path(file_path)
    if not path.exists():
        return {}
    
    stat = path.stat()
    return {
        'name': path.name,
        'stem': path.stem,
        'suffix': path.suffix,
        'size': stat.st_size,
        'created': datetime.fromtimestamp(stat.st_ctime),
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'is_hidden': path.name.startswith('.'),
        'parent': str(path.parent)
    }


def batch_validate_names(names: List[str]) -> Dict[str, Tuple[bool, str]]:
    """Valida una lista de nombres de archivo en lote"""
    results = {}
    for name in names:
        is_valid, message = FileNameValidator.is_valid_filename(name)
        results[name] = (is_valid, message)
    return results


def suggest_improvements(filename: str) -> List[str]:
    """Sugiere mejoras para un nombre de archivo"""
    suggestions = []
    
    # Verificar espacios
    if ' ' in filename:
        suggestions.append("Reemplazar espacios por guiones bajos")
    
    # Verificar mayúsculas
    if filename != filename.lower():
        suggestions.append("Convertir a minúsculas")
    
    # Verificar caracteres especiales
    if re.search(r'[^a-zA-Z0-9._-]', filename):
        suggestions.append("Eliminar caracteres especiales")
    
    # Verificar longitud
    if len(filename) > 100:
        suggestions.append("Acortar el nombre (muy largo)")
    
    # Verificar acentos
    if re.search(r'[áéíóúñüç]', filename, re.IGNORECASE):
        suggestions.append("Eliminar acentos")
    
    return suggestions