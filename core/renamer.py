#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Renombrado Masivo de Archivos
Parte del sistema de Automatización de Compresión

Este módulo proporciona funcionalidad completa para renombrar archivos masivamente
con operaciones como agregar prefijos/sufijos, reemplazar texto, numeración automática,
y más, manteniendo siempre las extensiones de archivo.
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RenameOperation:
    """Representa una operación de renombrado"""
    operation_type: str  # 'prefix', 'suffix', 'replace', 'remove', 'numbering', 'case', 'padding'
    enabled: bool = True
    value: str = ""
    old_value: str = ""  # Para operaciones de reemplazo
    start_number: int = 1  # Para numeración
    padding: int = 3  # Ceros a la izquierda para numeración
    case_type: str = "lower"  # 'lower', 'upper', 'title', 'sentence'
    padding_length: int = 6  # Longitud total para padding numérico
    position: int = 0  # Posición en la lista de operaciones


@dataclass
class FileRenamePreview:
    """Representa la vista previa de un archivo a renombrar"""
    original_path: str
    original_name: str
    new_name: str
    extension: str
    has_conflict: bool = False
    conflict_reason: str = ""
    size: int = 0
    modified_date: datetime = None


class FileRenamer:
    """Clase principal para el renombrado masivo de archivos"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.operations: List[RenameOperation] = []
        self.files: List[str] = []
        self.preview_cache: List[FileRenamePreview] = []
        self.stats = {
            'total_files': 0,
            'renamed_files': 0,
            'skipped_files': 0,
            'errors': 0
        }
    
    def add_operation(self, operation: RenameOperation) -> None:
        """Agrega una nueva operación de renombrado"""
        operation.position = len(self.operations)
        self.operations.append(operation)
        self.logger.log_operation('INFO', f"Operación agregada: {operation.operation_type}")
    
    def remove_operation(self, index: int) -> bool:
        """Elimina una operación por índice"""
        if 0 <= index < len(self.operations):
            removed = self.operations.pop(index)
            # Reajustar posiciones
            for i, op in enumerate(self.operations):
                op.position = i
            self.logger.log_operation('INFO', f"Operación eliminada: {removed.operation_type}")
            return True
        return False
    
    def reorder_operations(self, new_order: List[int]) -> bool:
        """Reordena las operaciones según la nueva lista de índices"""
        if len(new_order) != len(self.operations):
            return False
        
        try:
            reordered = [self.operations[i] for i in new_order]
            for i, op in enumerate(reordered):
                op.position = i
            self.operations = reordered
            self.logger.log_operation('INFO', "Operaciones reordenadas exitosamente")
            return True
        except IndexError:
            return False
    
    def load_files_from_folder(self, folder_path: str, include_subfolders: bool = False, 
                              file_filters: List[str] = None) -> int:
        """Carga archivos desde una carpeta"""
        self.files.clear()
        folder = Path(folder_path)
        
        if not folder.exists() or not folder.is_dir():
            self.logger.log_operation('ERROR', f"Carpeta no válida: {folder_path}")
            return 0
        
        file_filters = file_filters or ['*']
        pattern = "**/*" if include_subfolders else "*"
        
        for filter_pattern in file_filters:
            if include_subfolders:
                files = folder.rglob(filter_pattern)
            else:
                files = folder.glob(filter_pattern)
            
            for file_path in files:
                if file_path.is_file():
                    self.files.append(str(file_path))
        
        # Eliminar duplicados y ordenar
        self.files = sorted(list(set(self.files)))
        self.stats['total_files'] = len(self.files)
        
        self.logger.log_operation('INFO', f"Cargados {len(self.files)} archivos desde {folder_path}")
        return len(self.files)
    
    def add_files(self, file_paths: List[str]) -> int:
        """Agrega archivos específicos a la lista"""
        added = 0
        for file_path in file_paths:
            path = Path(file_path)
            if path.exists() and path.is_file() and str(path) not in self.files:
                self.files.append(str(path))
                added += 1
        
        self.stats['total_files'] = len(self.files)
        self.logger.log_operation('INFO', f"Agregados {added} archivos")
        return added
    
    def clear_files(self) -> None:
        """Limpia la lista de archivos"""
        self.files.clear()
        self.preview_cache.clear()
        self.stats['total_files'] = 0
    
    def _apply_single_operation(self, filename: str, operation: RenameOperation, 
                               file_index: int = 0) -> str:
        """Aplica una sola operación a un nombre de archivo"""
        if not operation.enabled:
            return filename
        
        name, ext = os.path.splitext(filename)
        
        if operation.operation_type == 'prefix':
            name = operation.value + name
        
        elif operation.operation_type == 'suffix':
            name = name + operation.value
        
        elif operation.operation_type == 'replace':
            if operation.old_value:
                name = name.replace(operation.old_value, operation.value)
        
        elif operation.operation_type == 'remove':
            if operation.value:
                name = name.replace(operation.value, "")
        
        elif operation.operation_type == 'numbering':
            number = operation.start_number + file_index
            number_str = str(number).zfill(operation.padding)
            name = f"{number_str}_{name}"
        
        elif operation.operation_type == 'case':
            if operation.case_type == 'lower':
                name = name.lower()
            elif operation.case_type == 'upper':
                name = name.upper()
            elif operation.case_type == 'title':
                name = name.title()
            elif operation.case_type == 'sentence':
                name = name.capitalize()
        
        elif operation.operation_type == 'padding':
            # Importar NumberingHelper para usar la función de padding
            from utils.rename_operations import NumberingHelper
            name = NumberingHelper.pad_numbers(name, operation.padding_length)
        
        elif operation.operation_type == 'remove_padding':
            # Importar NumberingHelper para usar la función de remove padding
            from utils.rename_operations import NumberingHelper
            name = NumberingHelper.remove_padding(name)
        
        return name + ext
    
    def generate_preview(self) -> List[FileRenamePreview]:
        """Genera vista previa de todos los archivos con las operaciones aplicadas"""
        self.preview_cache.clear()
        
        # Ordenar operaciones por posición
        sorted_operations = sorted(self.operations, key=lambda x: x.position)
        
        for i, file_path in enumerate(self.files):
            path = Path(file_path)
            original_name = path.name
            new_name = original_name
            
            # Aplicar todas las operaciones en orden
            for operation in sorted_operations:
                new_name = self._apply_single_operation(new_name, operation, i)
            
            # Crear preview
            preview = FileRenamePreview(
                original_path=file_path,
                original_name=original_name,
                new_name=new_name,
                extension=path.suffix,
                size=path.stat().st_size if path.exists() else 0,
                modified_date=datetime.fromtimestamp(path.stat().st_mtime) if path.exists() else None
            )
            
            # Verificar conflictos
            new_path = path.parent / new_name
            if new_path.exists() and str(new_path) != file_path:
                preview.has_conflict = True
                preview.conflict_reason = "El archivo ya existe"
            elif new_name == original_name:
                preview.conflict_reason = "Sin cambios"
            
            self.preview_cache.append(preview)
        
        return self.preview_cache
    
    def check_conflicts(self) -> Dict[str, List[str]]:
        """Verifica conflictos en el renombrado"""
        conflicts = {
            'duplicates': [],
            'existing_files': [],
            'invalid_names': []
        }
        
        new_names = []
        for preview in self.preview_cache:
            # Verificar nombres duplicados
            if preview.new_name in new_names:
                conflicts['duplicates'].append(preview.new_name)
            else:
                new_names.append(preview.new_name)
            
            # Verificar archivos existentes
            if preview.has_conflict:
                conflicts['existing_files'].append(preview.new_name)
            
            # Verificar nombres inválidos
            invalid_chars = r'[<>:"/\|?*]'
            if re.search(invalid_chars, preview.new_name):
                conflicts['invalid_names'].append(preview.new_name)
        
        return conflicts
    
    def apply_rename(self, dry_run: bool = False) -> Dict[str, Any]:
        """Aplica el renombrado a todos los archivos"""
        if not self.preview_cache:
            self.generate_preview()
        
        results = {
            'success': [],
            'errors': [],
            'skipped': [],
            'total_processed': 0
        }
        
        self.stats['renamed_files'] = 0
        self.stats['skipped_files'] = 0
        self.stats['errors'] = 0
        
        for preview in self.preview_cache:
            results['total_processed'] += 1
            
            # Saltar si no hay cambios
            if preview.original_name == preview.new_name:
                results['skipped'].append({
                    'file': preview.original_name,
                    'reason': 'Sin cambios'
                })
                self.stats['skipped_files'] += 1
                continue
            
            # Saltar si hay conflictos
            if preview.has_conflict:
                results['skipped'].append({
                    'file': preview.original_name,
                    'reason': preview.conflict_reason
                })
                self.stats['skipped_files'] += 1
                continue
            
            if not dry_run:
                try:
                    old_path = Path(preview.original_path)
                    new_path = old_path.parent / preview.new_name
                    
                    old_path.rename(new_path)
                    
                    results['success'].append({
                        'old_name': preview.original_name,
                        'new_name': preview.new_name,
                        'path': str(new_path)
                    })
                    self.stats['renamed_files'] += 1
                    
                except Exception as e:
                    error_msg = f"Error renombrando {preview.original_name}: {str(e)}"
                    results['errors'].append({
                        'file': preview.original_name,
                        'error': error_msg
                    })
                    self.stats['errors'] += 1
                    self.logger.log_operation('ERROR', error_msg)
            else:
                # Modo dry run - solo simular
                results['success'].append({
                    'old_name': preview.original_name,
                    'new_name': preview.new_name,
                    'path': 'DRY RUN'
                })
        
        self.logger.log_operation('INFO', f"Renombrado completado: {self.stats['renamed_files']} exitosos, "
                        f"{self.stats['skipped_files']} omitidos, {self.stats['errors']} errores")
        
        return results
    
    def get_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas del renombrado"""
        return self.stats.copy()
    
    def reset(self) -> None:
        """Reinicia el renombrador"""
        self.operations.clear()
        self.files.clear()
        self.preview_cache.clear()
        self.stats = {
            'total_files': 0,
            'renamed_files': 0,
            'skipped_files': 0,
            'errors': 0
        }
        self.logger.log_operation('INFO', "Renombrador reiniciado")


# Funciones de utilidad
def create_prefix_operation(prefix: str, enabled: bool = True) -> RenameOperation:
    """Crea una operación de prefijo"""
    return RenameOperation(
        operation_type='prefix',
        enabled=enabled,
        value=prefix
    )


def create_suffix_operation(suffix: str, enabled: bool = True) -> RenameOperation:
    """Crea una operación de sufijo"""
    return RenameOperation(
        operation_type='suffix',
        enabled=enabled,
        value=suffix
    )


def create_replace_operation(old_text: str, new_text: str, enabled: bool = True) -> RenameOperation:
    """Crea una operación de reemplazo"""
    return RenameOperation(
        operation_type='replace',
        enabled=enabled,
        old_value=old_text,
        value=new_text
    )


def create_numbering_operation(start: int = 1, padding: int = 3, enabled: bool = True) -> RenameOperation:
    """Crea una operación de numeración"""
    return RenameOperation(
        operation_type='numbering',
        enabled=enabled,
        start_number=start,
        padding=padding
    )


def create_case_operation(case_type: str = 'lower', enabled: bool = True) -> RenameOperation:
    """Crea una operación de cambio de mayúsculas/minúsculas"""
    return RenameOperation(
        operation_type='case',
        enabled=enabled,
        case_type=case_type
    )