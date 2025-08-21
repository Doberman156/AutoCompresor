#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Logging Personalizado - Automatización de Compresión de Archivos

Este módulo proporciona un sistema de logging avanzado con múltiples niveles,
rotación de archivos, estadísticas de sesión y logging tanto en consola como en archivos.
"""

import logging
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import threading
import queue
from dataclasses import dataclass, field


@dataclass
class SessionStats:
    """Estadísticas de una sesión de compresión."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_original_size: int = 0
    total_compressed_size: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calcula la tasa de éxito."""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100
    
    @property
    def compression_ratio(self) -> float:
        """Calcula la ratio de compresión."""
        if self.total_original_size == 0:
            return 0.0
        return (1 - (self.total_compressed_size / self.total_original_size)) * 100
    
    @property
    def duration(self) -> timedelta:
        """Calcula la duración de la sesión."""
        end = self.end_time or datetime.now()
        return end - self.start_time


class CustomFormatter(logging.Formatter):
    """Formateador personalizado para logs con colores y estilos."""
    
    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Verde
        'WARNING': '\033[33m',   # Amarillo
        'ERROR': '\033[31m',     # Rojo
        'CRITICAL': '\033[35m',  # Magenta
        'SUCCESS': '\033[92m',   # Verde brillante
        'RESET': '\033[0m'       # Reset
    }
    
    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors
    
    def format(self, record):
        # Formato base
        log_format = '[%(asctime)s] %(levelname)s - %(message)s'
        
        # Agregar información adicional si está disponible
        if hasattr(record, 'file_path'):
            log_format = '[%(asctime)s] %(levelname)s - %(file_path)s: %(message)s'
        
        formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
        formatted = formatter.format(record)
        
        # Aplicar colores si está habilitado
        if self.use_colors and record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            reset = self.COLORS['RESET']
            formatted = f"{color}{formatted}{reset}"
        
        return formatted


class CustomLogger:
    """Sistema de logging personalizado con funcionalidades avanzadas."""
    
    def __init__(self, name: str = "AutomatizacionCompresion", log_dir: str = "logs"):
        """Inicializa el logger personalizado.
        
        Args:
            name: Nombre del logger
            log_dir: Directorio donde guardar los logs
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configuración
        self.max_log_files = 30
        self.log_level = logging.INFO
        
        # Estadísticas de sesión
        self.current_session: Optional[SessionStats] = None
        self.sessions_history: List[SessionStats] = []
        
        # Queue para logging asíncrono
        self.log_queue = queue.Queue()
        self.log_thread = None
        self.stop_logging = threading.Event()
        
        # Callbacks para la UI
        self.ui_callbacks: List[Callable[[str, str, str], None]] = []
        
        # Configurar logger
        self._setup_logger()
        self._start_log_thread()
    
    def _setup_logger(self):
        """Configura el sistema de logging."""
        # Logger principal
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.log_level)
        
        # Limpiar handlers existentes
        self.logger.handlers.clear()
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_formatter = CustomFormatter(use_colors=True)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Handler para archivo
        log_file = self.log_dir / f"compression_{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(self.log_level)
        file_formatter = CustomFormatter(use_colors=False)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Agregar nivel SUCCESS personalizado
        logging.addLevelName(25, 'SUCCESS')
        
        def success(self, message, *args, **kwargs):
            if self.isEnabledFor(25):
                self._log(25, message, args, **kwargs)
        
        logging.Logger.success = success
    
    def _start_log_thread(self):
        """Inicia el hilo de logging asíncrono."""
        self.log_thread = threading.Thread(target=self._log_worker, daemon=True)
        self.log_thread.start()
    
    def _log_worker(self):
        """Worker para procesamiento asíncrono de logs."""
        while not self.stop_logging.is_set():
            try:
                # Obtener mensaje de la queue con timeout
                log_item = self.log_queue.get(timeout=1.0)
                if log_item is None:  # Señal de parada
                    break
                
                level, message, file_path, extra = log_item
                
                # Crear record con información adicional
                record = logging.LogRecord(
                    name=self.name,
                    level=getattr(logging, level.upper()),
                    pathname='',
                    lineno=0,
                    msg=message,
                    args=(),
                    exc_info=None
                )
                
                if file_path:
                    record.file_path = file_path
                
                # Procesar con handlers
                self.logger.handle(record)
                
                # Notificar a callbacks de UI
                for callback in self.ui_callbacks:
                    try:
                        callback(level, message, file_path or '')
                    except Exception as e:
                        print(f"Error en callback de UI: {e}")
                
                self.log_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error en log worker: {e}")
    
    def add_ui_callback(self, callback: Callable[[str, str, str], None]):
        """Agrega un callback para notificar a la UI.
        
        Args:
            callback: Función que recibe (level, message, file_path)
        """
        self.ui_callbacks.append(callback)
    
    def remove_ui_callback(self, callback: Callable[[str, str, str], None]):
        """Remueve un callback de UI."""
        if callback in self.ui_callbacks:
            self.ui_callbacks.remove(callback)
    
    def log_operation(self, level: str, message: str, file_path: Optional[str] = None, **extra):
        """Registra una operación de forma asíncrona.
        
        Args:
            level: Nivel de log (DEBUG, INFO, WARNING, ERROR, SUCCESS)
            message: Mensaje a registrar
            file_path: Ruta del archivo relacionado (opcional)
            **extra: Información adicional
        """
        try:
            self.log_queue.put((level, message, file_path, extra), timeout=1.0)
        except queue.Full:
            # Si la queue está llena, log directamente
            getattr(self.logger, level.lower(), self.logger.info)(message)
    
    def start_session(self, session_id: Optional[str] = None) -> str:
        """Inicia una nueva sesión de logging.
        
        Args:
            session_id: ID de la sesión (se genera automáticamente si no se proporciona)
            
        Returns:
            ID de la sesión iniciada
        """
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Finalizar sesión anterior si existe
        if self.current_session:
            self.end_session()
        
        self.current_session = SessionStats(
            session_id=session_id,
            start_time=datetime.now()
        )
        
        self.log_operation('INFO', f'Sesión iniciada: {session_id}')
        return session_id
    
    def end_session(self) -> Optional[SessionStats]:
        """Finaliza la sesión actual.
        
        Returns:
            Estadísticas de la sesión finalizada
        """
        if not self.current_session:
            return None
        
        self.current_session.end_time = datetime.now()
        
        # Log de resumen
        stats = self.current_session
        self.log_operation('INFO', 
            f'Sesión completada: {stats.processed_files} éxitos, '
            f'{stats.failed_files} errores, {stats.skipped_files} omitidos')
        
        # Agregar a historial
        self.sessions_history.append(self.current_session)
        session = self.current_session
        self.current_session = None
        
        return session
    
    def update_session_stats(self, **kwargs):
        """Actualiza las estadísticas de la sesión actual."""
        if not self.current_session:
            return
        
        for key, value in kwargs.items():
            if hasattr(self.current_session, key):
                if key in ['errors', 'warnings'] and isinstance(value, str):
                    getattr(self.current_session, key).append(value)
                else:
                    setattr(self.current_session, key, value)
    
    def log_file_operation(self, operation: str, file_path: str, status: str, 
                          original_size: int = 0, compressed_size: int = 0, 
                          error_msg: str = None):
        """Registra una operación específica de archivo.
        
        Args:
            operation: Tipo de operación (compress, move, etc.)
            file_path: Ruta del archivo
            status: Estado (success, error, skip)
            original_size: Tamaño original del archivo
            compressed_size: Tamaño comprimido
            error_msg: Mensaje de error si aplica
        """
        file_name = Path(file_path).name
        
        if status == 'success':
            if compressed_size > 0 and original_size > 0:
                ratio = (1 - (compressed_size / original_size)) * 100
                message = f'{operation.upper()} - {file_name} (Reducido {ratio:.1f}%)'
            else:
                message = f'{operation.upper()} - {file_name}'
            
            self.log_operation('SUCCESS', message, file_path)
            
            # Actualizar estadísticas
            if self.current_session:
                self.current_session.processed_files += 1
                self.current_session.total_original_size += original_size
                self.current_session.total_compressed_size += compressed_size
        
        elif status == 'error':
            message = f'ERROR - {file_name}'
            if error_msg:
                message += f': {error_msg}'
            
            self.log_operation('ERROR', message, file_path)
            
            # Actualizar estadísticas
            if self.current_session:
                self.current_session.failed_files += 1
                if error_msg:
                    self.current_session.errors.append(f'{file_name}: {error_msg}')
        
        elif status == 'skip':
            message = f'SKIP - {file_name}'
            if error_msg:
                message += f': {error_msg}'
            
            self.log_operation('WARNING', message, file_path)
            
            # Actualizar estadísticas
            if self.current_session:
                self.current_session.skipped_files += 1
                if error_msg:
                    self.current_session.warnings.append(f'{file_name}: {error_msg}')
    
    def get_session_stats(self) -> Optional[Dict[str, Any]]:
        """Obtiene las estadísticas de la sesión actual.
        
        Returns:
            Diccionario con las estadísticas o None si no hay sesión activa
        """
        if not self.current_session:
            return None
        
        stats = self.current_session
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
    
    def set_log_level(self, level: str):
        """Establece el nivel de logging.
        
        Args:
            level: Nivel de log (DEBUG, INFO, WARNING, ERROR)
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.log_level = log_level
        self.logger.setLevel(log_level)
        
        for handler in self.logger.handlers:
            handler.setLevel(log_level)
    
    def cleanup_old_logs(self):
        """Limpia logs antiguos según la configuración."""
        try:
            log_files = list(self.log_dir.glob("compression_*.log"))
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Mantener solo los archivos más recientes
            for old_log in log_files[self.max_log_files:]:
                old_log.unlink()
                self.log_operation('INFO', f'Log antiguo eliminado: {old_log.name}')
        
        except Exception as e:
            self.log_operation('ERROR', f'Error al limpiar logs antiguos: {e}')
    
    def export_session_report(self, session_stats: SessionStats, export_path: str) -> bool:
        """Exporta un reporte detallado de la sesión.
        
        Args:
            session_stats: Estadísticas de la sesión
            export_path: Ruta donde guardar el reporte
            
        Returns:
            True si se exportó correctamente
        """
        try:
            report = {
                'session_info': {
                    'session_id': session_stats.session_id,
                    'start_time': session_stats.start_time.isoformat(),
                    'end_time': session_stats.end_time.isoformat() if session_stats.end_time else None,
                    'duration': str(session_stats.duration)
                },
                'statistics': {
                    'total_files': session_stats.total_files,
                    'processed_files': session_stats.processed_files,
                    'failed_files': session_stats.failed_files,
                    'skipped_files': session_stats.skipped_files,
                    'success_rate': session_stats.success_rate,
                    'compression_ratio': session_stats.compression_ratio,
                    'total_original_size': session_stats.total_original_size,
                    'total_compressed_size': session_stats.total_compressed_size,
                    'space_saved': session_stats.total_original_size - session_stats.total_compressed_size
                },
                'errors': session_stats.errors,
                'warnings': session_stats.warnings,
                'export_date': datetime.now().isoformat()
            }
            
            import json
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            self.log_operation('ERROR', f'Error al exportar reporte: {e}')
            return False
    
    def shutdown(self):
        """Cierra el sistema de logging de forma segura."""
        # Finalizar sesión actual
        if self.current_session:
            self.end_session()
        
        # Detener hilo de logging
        self.stop_logging.set()
        self.log_queue.put(None)  # Señal de parada
        
        if self.log_thread and self.log_thread.is_alive():
            self.log_thread.join(timeout=5.0)
        
        # Limpiar logs antiguos
        self.cleanup_old_logs()
        
        self.log_operation('INFO', 'Sistema de logging cerrado')