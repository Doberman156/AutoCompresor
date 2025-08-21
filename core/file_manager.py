#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de Archivos - Automatización de Compresión de Archivos

Este módulo maneja todas las operaciones relacionadas con archivos:
- Exploración de directorios
- Filtrado de archivos
- Movimiento a carpetas de respaldo
- Validación de permisos
- Gestión de conflictos
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Generator, Set
from datetime import datetime
import fnmatch
import hashlib
from dataclasses import dataclass
from enum import Enum


class ConflictResolution(Enum):
    """Estrategias para resolución de conflictos."""
    RENAME = "rename"
    OVERWRITE = "overwrite"
    SKIP = "skip"
    ASK = "ask"


@dataclass
class FileInfo:
    """Información detallada de un archivo."""
    path: Path
    name: str
    size: int
    modified_time: datetime
    extension: str
    is_readable: bool
    is_writable: bool
    checksum: Optional[str] = None
    
    @classmethod
    def from_path(cls, file_path: Path) -> 'FileInfo':
        """Crea FileInfo desde una ruta de archivo."""
        try:
            stat = file_path.stat()
            return cls(
                path=file_path,
                name=file_path.name,
                size=stat.st_size,
                modified_time=datetime.fromtimestamp(stat.st_mtime),
                extension=file_path.suffix.lower(),
                is_readable=os.access(file_path, os.R_OK),
                is_writable=os.access(file_path, os.W_OK)
            )
        except Exception as e:
            # Crear objeto con información mínima si hay error
            return cls(
                path=file_path,
                name=file_path.name,
                size=0,
                modified_time=datetime.now(),
                extension=file_path.suffix.lower(),
                is_readable=False,
                is_writable=False
            )
    
    def calculate_checksum(self) -> str:
        """Calcula el checksum MD5 del archivo."""
        if self.checksum:
            return self.checksum
        
        try:
            hash_md5 = hashlib.md5()
            with open(self.path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            self.checksum = hash_md5.hexdigest()
            return self.checksum
        except Exception:
            return ""


class FileManager:
    """Gestor principal de archivos y operaciones del sistema de archivos."""
    
    def __init__(self, logger=None):
        """Inicializa el gestor de archivos.
        
        Args:
            logger: Logger personalizado para registrar operaciones
        """
        self.logger = logger
        self.processed_files: Set[str] = set()
        self.backup_operations: List[Tuple[Path, Path]] = []
    
    def _log(self, level: str, message: str, file_path: str = None):
        """Registra un mensaje usando el logger si está disponible."""
        if self.logger:
            self.logger.log_operation(level, message, file_path)
        else:
            print(f"[{level}] {message}")
    
    def scan_directory(self, directory: Path, include_subfolders: bool = False, 
                      file_filters: List[str] = None) -> List[FileInfo]:
        """Escanea un directorio y retorna información de archivos.
        
        Args:
            directory: Directorio a escanear
            include_subfolders: Si incluir subdirectorios
            file_filters: Lista de patrones de archivos (ej: ['*.pdf', '*.jpg'])
            
        Returns:
            Lista de FileInfo de archivos encontrados
        """
        if not directory.exists():
            self._log('ERROR', f'El directorio no existe: {directory}')
            return []
        
        if not directory.is_dir():
            self._log('ERROR', f'La ruta no es un directorio: {directory}')
            return []
        
        files = []
        file_filters = file_filters or ['*']
        
        try:
            # Función para procesar archivos
            def process_files(path: Path):
                try:
                    for item in path.iterdir():
                        if item.is_file():
                            # Verificar si el archivo coincide con los filtros
                            if self._matches_filters(item.name, file_filters):
                                file_info = FileInfo.from_path(item)
                                if file_info.is_readable:
                                    files.append(file_info)
                                else:
                                    self._log('WARNING', f'Archivo no legible: {item.name}', str(item))
                        
                        elif item.is_dir() and include_subfolders:
                            # Recursión para subdirectorios
                            process_files(item)
                
                except PermissionError:
                    self._log('WARNING', f'Sin permisos para acceder a: {path}')
                except Exception as e:
                    self._log('ERROR', f'Error al procesar directorio {path}: {e}')
            
            process_files(directory)
            
            self._log('INFO', f'Encontrados {len(files)} archivos en {directory}')
            return files
        
        except Exception as e:
            self._log('ERROR', f'Error al escanear directorio: {e}')
            return []
    
    def _matches_filters(self, filename: str, filters: List[str]) -> bool:
        """Verifica si un archivo coincide con los filtros especificados.
        
        Args:
            filename: Nombre del archivo
            filters: Lista de patrones (ej: ['*.pdf', '*.jpg'])
            
        Returns:
            True si el archivo coincide con algún filtro
        """
        if not filters or '*' in filters:
            return True
        
        for pattern in filters:
            if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                return True
        
        return False
    
    def create_backup_folder(self, backup_path: Path) -> bool:
        """Crea la carpeta de respaldo si no existe.
        
        Args:
            backup_path: Ruta de la carpeta de respaldo
            
        Returns:
            True si se creó o ya existe, False si hubo error
        """
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Verificar permisos de escritura
            if not os.access(backup_path, os.W_OK):
                self._log('ERROR', f'Sin permisos de escritura en: {backup_path}')
                return False
            
            self._log('INFO', f'Carpeta de respaldo lista: {backup_path}')
            return True
        
        except Exception as e:
            self._log('ERROR', f'Error al crear carpeta de respaldo: {e}')
            return False
    
    def move_to_backup(self, file_path: Path, backup_folder: Path, 
                      conflict_resolution: ConflictResolution = ConflictResolution.RENAME) -> Optional[Path]:
        """Mueve un archivo a la carpeta de respaldo.
        
        Args:
            file_path: Archivo a mover
            backup_folder: Carpeta de destino
            conflict_resolution: Estrategia para conflictos
            
        Returns:
            Ruta final del archivo movido o None si falló
        """
        if not file_path.exists():
            self._log('ERROR', f'Archivo no existe: {file_path}')
            return None
        
        # Crear carpeta de respaldo si no existe
        if not self.create_backup_folder(backup_folder):
            return None
        
        try:
            # Determinar ruta de destino
            destination = backup_folder / file_path.name
            
            # Manejar conflictos si el archivo ya existe
            if destination.exists():
                destination = self._resolve_conflict(destination, conflict_resolution)
                if destination is None:
                    self._log('WARNING', f'Operación cancelada por conflicto: {file_path.name}')
                    return None
            
            # Mover archivo
            shutil.move(str(file_path), str(destination))
            
            # Registrar operación para posible rollback
            self.backup_operations.append((file_path, destination))
            
            self._log('SUCCESS', f'Archivo movido a respaldo: {file_path.name}', str(destination))
            return destination
        
        except Exception as e:
            self._log('ERROR', f'Error al mover archivo {file_path.name}: {e}')
            return None
    
    def _resolve_conflict(self, destination: Path, resolution: ConflictResolution) -> Optional[Path]:
        """Resuelve conflictos cuando el archivo de destino ya existe.
        
        Args:
            destination: Ruta de destino que ya existe
            resolution: Estrategia de resolución
            
        Returns:
            Nueva ruta de destino o None si se cancela
        """
        if resolution == ConflictResolution.OVERWRITE:
            return destination
        
        elif resolution == ConflictResolution.SKIP:
            return None
        
        elif resolution == ConflictResolution.RENAME:
            return self._generate_unique_name(destination)
        
        elif resolution == ConflictResolution.ASK:
            # En una implementación real, esto mostraría un diálogo
            # Por ahora, usar rename como fallback
            return self._generate_unique_name(destination)
        
        return None
    
    def _generate_unique_name(self, file_path: Path) -> Path:
        """Genera un nombre único para evitar conflictos.
        
        Args:
            file_path: Ruta original
            
        Returns:
            Nueva ruta con nombre único
        """
        base = file_path.stem
        extension = file_path.suffix
        parent = file_path.parent
        
        counter = 1
        while True:
            new_name = f"{base}_{counter}{extension}"
            new_path = parent / new_name
            
            if not new_path.exists():
                return new_path
            
            counter += 1
            
            # Evitar bucle infinito
            if counter > 9999:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_name = f"{base}_{timestamp}{extension}"
                return parent / new_name
    
    def validate_permissions(self, directory: Path) -> Dict[str, bool]:
        """Valida permisos en un directorio.
        
        Args:
            directory: Directorio a validar
            
        Returns:
            Diccionario con resultados de validación
        """
        results = {
            'exists': False,
            'is_directory': False,
            'readable': False,
            'writable': False,
            'executable': False
        }
        
        try:
            if directory.exists():
                results['exists'] = True
                results['is_directory'] = directory.is_dir()
                results['readable'] = os.access(directory, os.R_OK)
                results['writable'] = os.access(directory, os.W_OK)
                results['executable'] = os.access(directory, os.X_OK)
        
        except Exception as e:
            self._log('ERROR', f'Error al validar permisos: {e}')
        
        return results
    
    def get_directory_size(self, directory: Path) -> int:
        """Calcula el tamaño total de un directorio.
        
        Args:
            directory: Directorio a analizar
            
        Returns:
            Tamaño total en bytes
        """
        total_size = 0
        
        try:
            for item in directory.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (OSError, IOError):
                        continue
        
        except Exception as e:
            self._log('ERROR', f'Error al calcular tamaño del directorio: {e}')
        
        return total_size
    
    def cleanup_empty_directories(self, root_directory: Path) -> int:
        """Limpia directorios vacíos de forma recursiva.
        
        Args:
            root_directory: Directorio raíz para limpiar
            
        Returns:
            Número de directorios eliminados
        """
        removed_count = 0
        
        try:
            # Obtener todos los directorios, ordenados por profundidad (más profundos primero)
            directories = []
            for item in root_directory.rglob('*'):
                if item.is_dir():
                    directories.append(item)
            
            # Ordenar por profundidad (más profundos primero)
            directories.sort(key=lambda x: len(x.parts), reverse=True)
            
            for directory in directories:
                try:
                    # Verificar si está vacío
                    if not any(directory.iterdir()):
                        directory.rmdir()
                        removed_count += 1
                        self._log('INFO', f'Directorio vacío eliminado: {directory}')
                
                except OSError:
                    # Directorio no vacío o sin permisos
                    continue
        
        except Exception as e:
            self._log('ERROR', f'Error al limpiar directorios vacíos: {e}')
        
        return removed_count
    
    def verify_file_integrity(self, file_path: Path, expected_checksum: str = None) -> bool:
        """Verifica la integridad de un archivo.
        
        Args:
            file_path: Archivo a verificar
            expected_checksum: Checksum esperado (opcional)
            
        Returns:
            True si el archivo es íntegro
        """
        try:
            if not file_path.exists():
                return False
            
            file_info = FileInfo.from_path(file_path)
            current_checksum = file_info.calculate_checksum()
            
            if expected_checksum:
                return current_checksum == expected_checksum
            
            # Si no hay checksum esperado, verificar que se pueda leer
            return bool(current_checksum)
        
        except Exception as e:
            self._log('ERROR', f'Error al verificar integridad: {e}')
            return False
    
    def rollback_backup_operations(self) -> int:
        """Revierte las operaciones de respaldo realizadas.
        
        Returns:
            Número de operaciones revertidas
        """
        reverted_count = 0
        
        # Revertir en orden inverso
        for original_path, backup_path in reversed(self.backup_operations):
            try:
                if backup_path.exists():
                    # Restaurar archivo a ubicación original
                    shutil.move(str(backup_path), str(original_path))
                    reverted_count += 1
                    self._log('INFO', f'Operación revertida: {original_path.name}')
            
            except Exception as e:
                self._log('ERROR', f'Error al revertir {original_path.name}: {e}')
        
        # Limpiar lista de operaciones
        self.backup_operations.clear()
        
        return reverted_count
    
    def get_file_statistics(self, files: List[FileInfo]) -> Dict[str, any]:
        """Calcula estadísticas de una lista de archivos.
        
        Args:
            files: Lista de archivos a analizar
            
        Returns:
            Diccionario con estadísticas
        """
        if not files:
            return {
                'total_files': 0,
                'total_size': 0,
                'average_size': 0,
                'extensions': {},
                'largest_file': None,
                'smallest_file': None
            }
        
        total_size = sum(f.size for f in files)
        extensions = {}
        
        # Contar extensiones
        for file_info in files:
            ext = file_info.extension or 'sin_extension'
            extensions[ext] = extensions.get(ext, 0) + 1
        
        # Encontrar archivos más grande y más pequeño
        largest = max(files, key=lambda f: f.size)
        smallest = min(files, key=lambda f: f.size)
        
        return {
            'total_files': len(files),
            'total_size': total_size,
            'average_size': total_size // len(files) if files else 0,
            'extensions': extensions,
            'largest_file': {
                'name': largest.name,
                'size': largest.size,
                'path': str(largest.path)
            },
            'smallest_file': {
                'name': smallest.name,
                'size': smallest.size,
                'path': str(smallest.path)
            }
        }
    
    def format_file_size(self, size_bytes: int) -> str:
        """Formatea el tamaño de archivo en unidades legibles.
        
        Args:
            size_bytes: Tamaño en bytes
            
        Returns:
            Tamaño formateado (ej: '1.5 MB')
        """
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.1f} {units[unit_index]}"
    
    def clear_processed_files(self):
        """Limpia la lista de archivos procesados."""
        self.processed_files.clear()
        self.backup_operations.clear()