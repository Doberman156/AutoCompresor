#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor de Compresión - Automatización de Compresión de Archivos

Este módulo contiene la lógica principal para comprimir archivos individuales,
generar nombres según patrones, manejar conflictos y coordinar todo el proceso.
"""

import zipfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from dataclasses import dataclass
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .file_manager import FileManager, FileInfo, ConflictResolution
from .logger import CustomLogger
from .config_manager import ConfigManager


@dataclass
class CompressionConfig:
    """Configuración para el proceso de compresión."""
    source_folder: str
    backup_folder: str
    naming_pattern: str
    include_subfolders: bool = False
    file_filters: List[str] = None
    compression_level: int = 6
    conflict_resolution: str = "rename"
    verify_integrity: bool = True
    max_workers: int = 4
    custom_pattern: str = ""
    
    def __post_init__(self):
        if self.file_filters is None:
            self.file_filters = ["*"]


@dataclass
class CompressionResult:
    """Resultado del proceso de compresión."""
    success: bool
    processed_files: int
    failed_files: int
    skipped_files: int
    total_size_saved: int
    execution_time: float
    errors: List[str]
    session_id: str
    
    @property
    def total_files(self) -> int:
        return self.processed_files + self.failed_files + self.skipped_files
    
    @property
    def success_rate(self) -> float:
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100


class CompressorEngine:
    """Motor principal de compresión de archivos."""
    
    def __init__(self, config_manager: ConfigManager = None, logger: CustomLogger = None):
        """Inicializa el motor de compresión.
        
        Args:
            config_manager: Gestor de configuración
            logger: Logger personalizado
        """
        self.config_manager = config_manager or ConfigManager()
        self.logger = logger or CustomLogger()
        self.file_manager = FileManager(self.logger)
        
        # Control de proceso
        self.is_running = False
        self.is_paused = False
        self.should_stop = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # Inicialmente no pausado
        
        # Callbacks para la UI
        self.progress_callback: Optional[Callable[[int, int, str], None]] = None
        self.file_callback: Optional[Callable[[str, str, str], None]] = None
        
        # Estadísticas de la última sesión
        self._last_session_stats = None
        
        # Contador global para nomenclatura
        self.file_counter = 1
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Establece callback para actualizar progreso en la UI.
        
        Args:
            callback: Función que recibe (current, total, current_file)
        """
        self.progress_callback = callback
    
    def set_file_callback(self, callback: Callable[[str, str, str], None]):
        """Establece callback para notificar operaciones de archivo.
        
        Args:
            callback: Función que recibe (operation, filename, status)
        """
        self.file_callback = callback
    
    def compress_files(self, config: CompressionConfig) -> CompressionResult:
        """Comprime archivos según la configuración especificada.
        
        Args:
            config: Configuración de compresión
            
        Returns:
            Resultado del proceso de compresión
        """
        start_time = time.time()
        self.is_running = True
        self.should_stop = False
        self.file_counter = 1
        
        # Iniciar sesión de logging
        session_id = self.logger.start_session()
        
        try:
            # Validar configuración
            validation_errors = self._validate_config(config)
            if validation_errors:
                error_msg = "; ".join(validation_errors)
                self.logger.log_operation('ERROR', f'Configuración inválida: {error_msg}')
                return CompressionResult(
                    success=False,
                    processed_files=0,
                    failed_files=0,
                    skipped_files=0,
                    total_size_saved=0,
                    execution_time=time.time() - start_time,
                    errors=validation_errors,
                    session_id=session_id
                )
            
            # Escanear archivos
            source_path = Path(config.source_folder)
            self.logger.log_operation('INFO', f'Escaneando directorio: {source_path}')
            
            files = self.file_manager.scan_directory(
                source_path,
                config.include_subfolders,
                config.file_filters
            )
            
            if not files:
                self.logger.log_operation('WARNING', 'No se encontraron archivos para procesar')
                return CompressionResult(
                    success=True,
                    processed_files=0,
                    failed_files=0,
                    skipped_files=0,
                    total_size_saved=0,
                    execution_time=time.time() - start_time,
                    errors=[],
                    session_id=session_id
                )
            
            # Actualizar estadísticas de sesión
            self.logger.update_session_stats(total_files=len(files))
            
            self.logger.log_operation('INFO', f'Encontrados {len(files)} archivos en {config.source_folder}')
            
            # Crear carpeta de respaldo
            backup_path = Path(config.backup_folder)
            if not self.file_manager.create_backup_folder(backup_path):
                error_msg = f'No se pudo crear carpeta de respaldo: {backup_path}'
                self.logger.log_operation('ERROR', error_msg)
                return CompressionResult(
                    success=False,
                    processed_files=0,
                    failed_files=0,
                    skipped_files=0,
                    total_size_saved=0,
                    execution_time=time.time() - start_time,
                    errors=[error_msg],
                    session_id=session_id
                )
            
            # Procesar archivos
            result = self._process_files(files, config)
            
            # Finalizar sesión
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            result.session_id = session_id
            
            self.logger.log_operation('INFO', 
                f'Proceso completado en {execution_time:.2f}s: '
                f'{result.processed_files} éxitos, {result.failed_files} errores')
            
            return result
        
        except Exception as e:
            error_msg = f'Error crítico en el proceso de compresión: {e}'
            self.logger.log_operation('ERROR', error_msg)
            return CompressionResult(
                success=False,
                processed_files=0,
                failed_files=0,
                skipped_files=0,
                total_size_saved=0,
                execution_time=time.time() - start_time,
                errors=[error_msg],
                session_id=session_id
            )
        
        finally:
            self.is_running = False
            # Finalizar sesión después de obtener estadísticas
            session_stats = self.logger.end_session()
            # Guardar las estadísticas finales para acceso posterior
            self._last_session_stats = session_stats
    
    def _validate_config(self, config: CompressionConfig) -> List[str]:
        """Valida la configuración de compresión.
        
        Args:
            config: Configuración a validar
            
        Returns:
            Lista de errores encontrados
        """
        errors = []
        
        # Validar carpeta origen
        source_path = Path(config.source_folder)
        if not source_path.exists():
            errors.append(f'Carpeta origen no existe: {config.source_folder}')
        elif not source_path.is_dir():
            errors.append(f'La ruta origen no es un directorio: {config.source_folder}')
        
        # Validar permisos
        permissions = self.file_manager.validate_permissions(source_path)
        if not permissions.get('readable', False):
            errors.append('Sin permisos de lectura en carpeta origen')
        
        # Validar nivel de compresión
        if not (0 <= config.compression_level <= 9):
            errors.append('Nivel de compresión debe estar entre 0 y 9')
        
        # Validar patrón de nomenclatura
        patterns = self.config_manager.get_naming_patterns()
        if config.naming_pattern not in patterns and config.naming_pattern != 'personalizado':
            errors.append(f'Patrón de nomenclatura inválido: {config.naming_pattern}')
        
        return errors
    
    def _process_files(self, files: List[FileInfo], config: CompressionConfig) -> CompressionResult:
        """Procesa la lista de archivos para compresión.
        
        Args:
            files: Lista de archivos a procesar
            config: Configuración de compresión
            
        Returns:
            Resultado del procesamiento
        """
        processed = 0
        failed = 0
        skipped = 0
        total_saved = 0
        errors = []
        
        total_files = len(files)
        
        # Procesar archivos (secuencial para mejor control)
        for i, file_info in enumerate(files):
            if self.should_stop:
                self.logger.log_operation('INFO', 'Proceso detenido por el usuario')
                break
            
            # Manejar pausa
            self._pause_event.wait()
            
            # Actualizar progreso
            if self.progress_callback:
                self.progress_callback(i + 1, total_files, file_info.name)
            
            try:
                # Comprimir archivo individual
                result = self._compress_single_file(file_info, config)
                
                if result['status'] == 'success':
                    processed += 1
                    total_saved += result.get('size_saved', 0)
                    
                    # Mover archivo original a respaldo
                    backup_path = Path(config.backup_folder)
                    conflict_res = ConflictResolution(config.conflict_resolution)
                    
                    moved_path = self.file_manager.move_to_backup(
                        file_info.path, backup_path, conflict_res
                    )
                    
                    if not moved_path:
                        self.logger.log_operation('WARNING', 
                            f'No se pudo mover a respaldo: {file_info.name}')
                
                elif result['status'] == 'error':
                    failed += 1
                    errors.append(result.get('error', 'Error desconocido'))
                
                elif result['status'] == 'skip':
                    skipped += 1
            
            except Exception as e:
                failed += 1
                error_msg = f'Error procesando {file_info.name}: {e}'
                errors.append(error_msg)
                # Asegurar que se registre en el logger también
                self.logger.log_file_operation('compress', str(file_info.path), 'error', 
                                             error_msg=error_msg)
        
        # Verificar consistencia de contadores
        total_processed = processed + failed + skipped
        if total_processed != total_files:
            self.logger.log_operation('WARNING', 
                f'Discrepancia en conteo: {total_processed} procesados vs {total_files} encontrados')
        
        return CompressionResult(
            success=failed == 0,
            processed_files=processed,
            failed_files=failed,
            skipped_files=skipped,
            total_size_saved=total_saved,
            execution_time=0,  # Se establecerá en el método principal
            errors=errors,
            session_id=""  # Se establecerá en el método principal
        )
    
    def _compress_single_file(self, file_info: FileInfo, config: CompressionConfig) -> Dict[str, Any]:
        """Comprime un archivo individual.
        
        Args:
            file_info: Información del archivo
            config: Configuración de compresión
            
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            # Generar nombre del archivo ZIP
            zip_name = self._generate_zip_name(file_info, config)
            zip_path = file_info.path.parent / zip_name
            
            # Manejar conflictos si el ZIP ya existe
            if zip_path.exists():
                conflict_res = ConflictResolution(config.conflict_resolution)
                if conflict_res == ConflictResolution.SKIP:
                    self.logger.log_file_operation('compress', str(file_info.path), 'skip', 
                                                  error_msg='Archivo ZIP ya existe')
                    return {'status': 'skip', 'reason': 'ZIP ya existe'}
                elif conflict_res == ConflictResolution.RENAME:
                    zip_path = self.file_manager._generate_unique_name(zip_path)
            
            # Crear archivo ZIP
            original_size = file_info.size
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, 
                               compresslevel=config.compression_level) as zipf:
                zipf.write(file_info.path, file_info.name)
            
            # Verificar integridad si está habilitado
            if config.verify_integrity:
                if not self._verify_zip_integrity(zip_path, file_info):
                    zip_path.unlink()  # Eliminar ZIP corrupto
                    error_msg = 'Verificación de integridad falló'
                    self.logger.log_file_operation('compress', str(file_info.path), 'error', 
                                                  error_msg=error_msg)
                    return {'status': 'error', 'error': error_msg}
            
            # Calcular estadísticas
            compressed_size = zip_path.stat().st_size
            size_saved = original_size - compressed_size
            
            # Log exitoso
            self.logger.log_file_operation('compress', str(file_info.path), 'success',
                                         original_size, compressed_size)
            
            # Callback para UI
            if self.file_callback:
                self.file_callback('compress', file_info.name, 'success')
            
            return {
                'status': 'success',
                'zip_path': zip_path,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'size_saved': size_saved
            }
        
        except Exception as e:
            error_msg = str(e)
            self.logger.log_file_operation('compress', str(file_info.path), 'error', 
                                         error_msg=error_msg)
            
            if self.file_callback:
                self.file_callback('compress', file_info.name, 'error')
            
            return {'status': 'error', 'error': error_msg}
    
    def _generate_zip_name(self, file_info: FileInfo, config: CompressionConfig) -> str:
        """Genera el nombre del archivo ZIP según el patrón configurado.
        
        Args:
            file_info: Información del archivo
            config: Configuración de compresión
            
        Returns:
            Nombre del archivo ZIP
        """
        patterns = self.config_manager.get_naming_patterns()
        base_name = file_info.path.stem
        
        # Obtener patrón
        if config.naming_pattern == 'personalizado' and config.custom_pattern:
            pattern = config.custom_pattern
        else:
            pattern = patterns.get(config.naming_pattern, patterns['fecha_archivo'])
        
        # Variables disponibles para el patrón
        now = datetime.now()
        variables = {
            'fecha': now.strftime('%Y-%m-%d'),
            'fecha_corta': now.strftime('%Y%m%d'),
            'hora': now.strftime('%H-%M-%S'),
            'timestamp': now.strftime('%Y%m%d_%H%M%S'),
            'nombre_original': base_name,
            'contador': self.file_counter,
            'extension_original': file_info.extension,
            'numero_factura': self._extract_invoice_number(base_name)
        }
        
        # Aplicar patrón
        try:
            zip_name = pattern.format(**variables)
            self.file_counter += 1
        except KeyError as e:
            # Si falla el patrón, usar patrón por defecto
            self.logger.log_operation('WARNING', f'Error en patrón de nomenclatura: {e}')
            zip_name = f"{now.strftime('%Y-%m-%d')}_{base_name}"
        
        return f"{zip_name}.zip"
    
    def _verify_zip_integrity(self, zip_path: Path, original_file: FileInfo) -> bool:
        """Verifica la integridad del archivo ZIP creado.
        
        Args:
            zip_path: Ruta del archivo ZIP
            original_file: Información del archivo original
            
        Returns:
            True si el ZIP es válido
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                # Verificar que el ZIP no esté corrupto
                bad_file = zipf.testzip()
                if bad_file:
                    return False
                
                # Verificar que contiene el archivo esperado
                names = zipf.namelist()
                if original_file.name not in names:
                    return False
                
                # Verificar tamaño del archivo dentro del ZIP
                info = zipf.getinfo(original_file.name)
                if info.file_size != original_file.size:
                    return False
            
            return True
        
        except Exception:
            return False
    
    def pause(self):
        """Pausa el proceso de compresión."""
        if self.is_running:
            self.is_paused = True
            self._pause_event.clear()
            self.logger.log_operation('INFO', 'Proceso pausado')
    
    def resume(self):
        """Reanuda el proceso de compresión."""
        if self.is_running and self.is_paused:
            self.is_paused = False
            self._pause_event.set()
            self.logger.log_operation('INFO', 'Proceso reanudado')
    
    def stop(self):
        """Detiene el proceso de compresión."""
        if self.is_running:
            self.should_stop = True
            self._pause_event.set()  # Asegurar que no esté pausado
            self.logger.log_operation('INFO', 'Deteniendo proceso...')
    
    def get_last_session_stats(self) -> Optional[Dict[str, Any]]:
        """Obtiene las estadísticas de la última sesión completada.
        
        Returns:
            Diccionario con las estadísticas o None si no hay sesión disponible
        """
        if not self._last_session_stats:
            return None
        
        stats = self._last_session_stats
        return {
            'session_id': stats.session_id,
            'start_time': stats.start_time.isoformat(),
            'duration': str(stats.duration),
            'total_files': stats.total_files,
            'processed_files': stats.processed_files,
            'failed_files': stats.failed_files,
            'skipped_files': stats.skipped_files,
            'success_rate': stats.success_rate,
            'compression_ratio': stats.compression_ratio,
            'total_original_size': stats.total_original_size,
            'total_compressed_size': stats.total_compressed_size,
            'space_saved': stats.total_original_size - stats.total_compressed_size,
            'errors_count': len(stats.errors),
            'warnings_count': len(stats.warnings)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del motor de compresión.
        
        Returns:
            Diccionario con información de estado
        """
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'should_stop': self.should_stop,
            'current_session': self.logger.get_session_stats()
        }
    
    def estimate_compression_time(self, files: List[FileInfo], 
                                config: CompressionConfig) -> float:
        """Estima el tiempo de compresión basado en el tamaño de archivos.
        
        Args:
            files: Lista de archivos a comprimir
            config: Configuración de compresión
            
        Returns:
            Tiempo estimado en segundos
        """
        if not files:
            return 0.0
        
        total_size = sum(f.size for f in files)
        
        # Estimación basada en velocidad promedio (bytes por segundo)
        # Estos valores son aproximados y pueden variar según el hardware
        speed_factors = {
            0: 50_000_000,  # Sin compresión - muy rápido
            1: 30_000_000,  # Compresión mínima
            6: 10_000_000,  # Compresión normal
            9: 5_000_000    # Compresión máxima - más lento
        }
        
        speed = speed_factors.get(config.compression_level, 10_000_000)
        base_time = total_size / speed
        
        # Agregar overhead por número de archivos
        file_overhead = len(files) * 0.1  # 0.1 segundos por archivo
        
        return base_time + file_overhead
    
    def _extract_invoice_number(self, filename: str) -> str:
        """Extrae el número de factura del nombre del archivo.
        
        Args:
            filename: Nombre del archivo sin extensión
            
        Returns:
            Número de factura extraído o el nombre completo si no se puede extraer
        """
        import re
        
        # Patrones comunes para números de factura
        patterns = [
            r'^([A-Z]{3,4}\d{3,6})',  # HOSP001, FACT123, etc.
            r'^([A-Z]+\d+)',          # ABC123, XYZ456, etc.
            r'^(\d{3,6})',            # 001, 123456, etc.
            r'([A-Z]{2,4}-\d{3,6})',  # AB-001, HOSP-123, etc.
            r'([A-Z]+_\d+)',          # FACT_001, HOSP_123, etc.
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename.upper())
            if match:
                return match.group(1)
        
        # Si no se encuentra un patrón, usar el nombre completo
        return filename