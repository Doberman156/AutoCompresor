#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Actualizaciones - Automatización de Compresión de Archivos

Este módulo maneja la verificación, descarga e instalación de actualizaciones
de la aplicación de forma segura y automática.

Autor: Sistema de Automatización
Versión: 1.0
Fecha: 2025
"""

import os
import sys
import json
import hashlib
import shutil
import zipfile
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Optional, Callable, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urljoin
import requests
from packaging import version


@dataclass
class UpdateInfo:
    """Información sobre una actualización disponible."""
    version: str
    download_url: str
    changelog: str
    file_size: int
    checksum: str
    release_date: str
    is_critical: bool = False
    min_version: str = "1.0.0"


@dataclass
class UpdateConfig:
    """Configuración del sistema de actualizaciones."""
    update_server_url: str
    check_frequency_hours: int = 24
    auto_download: bool = False
    auto_install: bool = False
    backup_enabled: bool = True
    verify_signatures: bool = True
    allow_prereleases: bool = False


class UpdateError(Exception):
    """Excepción base para errores de actualización."""
    pass


class DownloadError(UpdateError):
    """Error durante la descarga de actualización."""
    pass


class ValidationError(UpdateError):
    """Error de validación de actualización."""
    pass


class InstallationError(UpdateError):
    """Error durante la instalación de actualización."""
    pass


class Updater:
    """Sistema principal de actualizaciones."""
    
    def __init__(self, config: UpdateConfig, logger=None, progress_callback: Callable[[int, str], None] = None):
        """Inicializa el sistema de actualizaciones.
        
        Args:
            config: Configuración de actualizaciones
            logger: Logger para registrar eventos
            progress_callback: Callback para reportar progreso (porcentaje, mensaje)
        """
        self.config = config
        self.logger = logger
        self.progress_callback = progress_callback
        
        # Rutas importantes
        self.app_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path.cwd()
        self.temp_dir = Path(tempfile.gettempdir()) / "AutomatizacionCompresion_Updates"
        self.backup_dir = self.app_dir / "backup"
        self.version_file = self.app_dir / "version.json"
        
        # Crear directorios necesarios
        self.temp_dir.mkdir(exist_ok=True)
        if self.config.backup_enabled:
            self.backup_dir.mkdir(exist_ok=True)
        
        # Información de versión actual
        self.current_version = self._get_current_version()
        
        # Estado de actualización
        self.is_updating = False
        self.last_check = None
        
    def _log(self, level: str, message: str):
        """Registra un mensaje usando el logger si está disponible."""
        if self.logger:
            self.logger.log_operation(level, f"[UPDATER] {message}")
        else:
            print(f"[{level}] {message}")
    
    def _report_progress(self, percentage: int, message: str):
        """Reporta progreso usando el callback si está disponible."""
        if self.progress_callback:
            self.progress_callback(percentage, message)
    
    def _get_current_version(self) -> str:
        """Obtiene la versión actual de la aplicación."""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                    return version_data.get('version', '1.0.0')
            else:
                # Crear archivo de versión inicial
                self._save_version_info('1.0.0')
                return '1.0.0'
        except Exception as e:
            self._log('WARNING', f'Error al leer versión actual: {e}')
            return '1.0.0'
    
    def _save_version_info(self, version_str: str, additional_info: Dict[str, Any] = None):
        """Guarda información de versión."""
        try:
            version_data = {
                'version': version_str,
                'updated_at': datetime.now().isoformat(),
                'app_name': 'Automatización de Compresión de Archivos'
            }
            
            if additional_info:
                version_data.update(additional_info)
            
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self._log('ERROR', f'Error al guardar información de versión: {e}')
    
    def check_for_updates(self, force: bool = False) -> Optional[UpdateInfo]:
        """Verifica si hay actualizaciones disponibles.
        
        Args:
            force: Forzar verificación ignorando la frecuencia configurada
            
        Returns:
            Información de actualización si está disponible, None si no
        """
        try:
            # Verificar frecuencia de chequeo
            if not force and self.last_check:
                time_since_check = datetime.now() - self.last_check
                if time_since_check < timedelta(hours=self.config.check_frequency_hours):
                    self._log('INFO', 'Verificación de actualizaciones omitida (muy reciente)')
                    return None
            
            self._log('INFO', 'Verificando actualizaciones disponibles...')
            self._report_progress(10, 'Conectando al servidor de actualizaciones...')
            
            # Usar la URL de releases/latest de GitHub directamente
            check_url = self.config.update_server_url.replace('/releases', '/releases/latest')
            
            # Realizar solicitud HTTP a la API de GitHub
            response = requests.get(
                check_url,
                timeout=30,
                headers={'User-Agent': 'AutomatizacionCompresion-Updater/1.0'}
            )
            response.raise_for_status()
            
            self._report_progress(50, 'Procesando información de actualización...')
            
            # Procesar respuesta de la API de GitHub
            release_data = response.json()
            
            # Extraer información del release
            latest_version = release_data.get('tag_name', '').lstrip('v')
            
            if not latest_version:
                self._log('INFO', 'No hay actualizaciones disponibles')
                self.last_check = datetime.now()
                self._report_progress(100, 'Verificación completada - Sin actualizaciones')
                return None
            
            # Verificar si la versión es realmente más nueva
            if version.parse(latest_version) <= version.parse(self.current_version):
                self._log('INFO', f'Versión {latest_version} no es más nueva que {self.current_version}')
                self.last_check = datetime.now()
                self._report_progress(100, 'Verificación completada - Sin actualizaciones')
                return None
            
            # Buscar el asset ZIP en los archivos del release
            download_url = None
            file_size = 0
            
            for asset in release_data.get('assets', []):
                if asset['name'].endswith('.zip'):
                    download_url = asset['browser_download_url']
                    file_size = asset.get('size', 0)
                    break
            
            if not download_url:
                self._log('WARNING', 'No se encontró archivo ZIP en el release')
                self.last_check = datetime.now()
                return None
            
            # Crear objeto UpdateInfo
            update_info = UpdateInfo(
                version=latest_version,
                download_url=download_url,
                changelog=release_data.get('body', ''),
                file_size=file_size,
                checksum='',  # GitHub no proporciona checksum automáticamente
                release_date=release_data.get('published_at', ''),
                is_critical=False,
                min_version='1.0.0'
            )
            
            # Verificar versión mínima requerida
            if version.parse(self.current_version) < version.parse(update_info.min_version):
                self._log('WARNING', f'Versión actual {self.current_version} es menor que la mínima requerida {update_info.min_version}')
            
            self._log('INFO', f'Actualización disponible: v{update_info.version}')
            self.last_check = datetime.now()
            self._report_progress(100, f'Actualización v{update_info.version} disponible')
            
            return update_info
            
        except requests.RequestException as e:
            self._log('ERROR', f'Error de conexión al verificar actualizaciones: {e}')
            self._report_progress(100, 'Error de conexión')
            return None
        except Exception as e:
            self._log('ERROR', f'Error al verificar actualizaciones: {e}')
            self._report_progress(100, 'Error en verificación')
            return None
    
    def download_update(self, update_info: UpdateInfo) -> Optional[Path]:
        """Descarga una actualización.
        
        Args:
            update_info: Información de la actualización a descargar
            
        Returns:
            Ruta del archivo descargado o None si falló
        """
        try:
            self._log('INFO', f'Iniciando descarga de actualización v{update_info.version}')
            self._report_progress(0, 'Iniciando descarga...')
            
            # Preparar archivo de destino
            filename = f"update_v{update_info.version}.zip"
            download_path = self.temp_dir / filename
            
            # Eliminar descarga anterior si existe
            if download_path.exists():
                download_path.unlink()
            
            # Descargar archivo
            response = requests.get(
                update_info.download_url,
                stream=True,
                timeout=300,
                headers={'User-Agent': 'AutomatizacionCompresion-Updater/1.0'}
            )
            response.raise_for_status()
            
            # Obtener tamaño total
            total_size = int(response.headers.get('content-length', 0))
            if total_size == 0:
                total_size = update_info.file_size
            
            # Descargar con progreso
            downloaded = 0
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 80)  # 80% para descarga
                            self._report_progress(progress, f'Descargando... {downloaded // 1024} KB')
            
            self._report_progress(85, 'Validando descarga...')
            
            # Validar checksum si está disponible
            if update_info.checksum:
                if not self._validate_checksum(download_path, update_info.checksum):
                    download_path.unlink()
                    raise ValidationError('Checksum de descarga no válido')
            
            # Validar que es un archivo ZIP válido
            if not self._validate_zip_file(download_path):
                download_path.unlink()
                raise ValidationError('Archivo descargado no es un ZIP válido')
            
            self._log('INFO', f'Descarga completada: {download_path}')
            self._report_progress(100, 'Descarga completada')
            
            return download_path
            
        except requests.RequestException as e:
            self._log('ERROR', f'Error de red durante descarga: {e}')
            raise DownloadError(f'Error de red: {e}')
        except Exception as e:
            self._log('ERROR', f'Error durante descarga: {e}')
            raise DownloadError(f'Error de descarga: {e}')
    
    def _validate_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Valida el checksum de un archivo."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            
            actual_checksum = hash_md5.hexdigest()
            return actual_checksum.lower() == expected_checksum.lower()
            
        except Exception as e:
            self._log('ERROR', f'Error al validar checksum: {e}')
            return False
    
    def _validate_zip_file(self, file_path: Path) -> bool:
        """Valida que un archivo sea un ZIP válido."""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Verificar que el ZIP no esté corrupto
                bad_file = zip_file.testzip()
                if bad_file:
                    self._log('ERROR', f'Archivo corrupto en ZIP: {bad_file}')
                    return False
                
                # Verificar que contenga archivos esperados
                file_list = zip_file.namelist()
                if not file_list:
                    self._log('ERROR', 'ZIP está vacío')
                    return False
                
                return True
                
        except zipfile.BadZipFile:
            self._log('ERROR', 'Archivo no es un ZIP válido')
            return False
        except Exception as e:
            self._log('ERROR', f'Error al validar ZIP: {e}')
            return False
    
    def create_backup(self) -> bool:
        """Crea un respaldo de la aplicación actual."""
        if not self.config.backup_enabled:
            return True
        
        try:
            self._log('INFO', 'Creando respaldo de la aplicación actual...')
            self._report_progress(0, 'Creando respaldo...')
            
            # Crear nombre de respaldo con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_v{self.current_version}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            # Crear directorio de respaldo
            backup_path.mkdir(exist_ok=True)
            
            # Archivos y directorios a respaldar
            items_to_backup = [
                'main.py',
                'core/',
                'gui/',
                'utils/',
                'config.json',
                'requirements.txt'
            ]
            
            total_items = len(items_to_backup)
            for i, item in enumerate(items_to_backup):
                item_path = self.app_dir / item
                if item_path.exists():
                    dest_path = backup_path / item
                    
                    if item_path.is_file():
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item_path, dest_path)
                    elif item_path.is_dir():
                        shutil.copytree(item_path, dest_path, dirs_exist_ok=True)
                
                progress = int(((i + 1) / total_items) * 100)
                self._report_progress(progress, f'Respaldando {item}...')
            
            # Guardar información del respaldo
            backup_info = {
                'version': self.current_version,
                'created_at': datetime.now().isoformat(),
                'backup_path': str(backup_path)
            }
            
            with open(backup_path / 'backup_info.json', 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            self._log('INFO', f'Respaldo creado en: {backup_path}')
            return True
            
        except Exception as e:
            self._log('ERROR', f'Error al crear respaldo: {e}')
            return False
    
    def install_update(self, update_path: Path, update_info: UpdateInfo) -> bool:
        """Instala una actualización.
        
        Args:
            update_path: Ruta del archivo de actualización
            update_info: Información de la actualización
            
        Returns:
            True si la instalación fue exitosa
        """
        if self.is_updating:
            self._log('WARNING', 'Ya hay una actualización en progreso')
            return False
        
        self.is_updating = True
        
        try:
            self._log('INFO', f'Iniciando instalación de actualización v{update_info.version}')
            self._report_progress(0, 'Preparando instalación...')
            
            # Crear respaldo si está habilitado
            if self.config.backup_enabled:
                self._report_progress(10, 'Creando respaldo...')
                if not self.create_backup():
                    raise InstallationError('Error al crear respaldo')
            
            # Extraer actualización
            self._report_progress(30, 'Extrayendo archivos...')
            extract_path = self.temp_dir / f"extract_v{update_info.version}"
            
            if extract_path.exists():
                shutil.rmtree(extract_path)
            extract_path.mkdir()
            
            with zipfile.ZipFile(update_path, 'r') as zip_file:
                zip_file.extractall(extract_path)
            
            # Validar estructura de actualización
            self._report_progress(50, 'Validando actualización...')
            if not self._validate_update_structure(extract_path):
                raise InstallationError('Estructura de actualización inválida')
            
            # Aplicar actualización
            self._report_progress(70, 'Aplicando actualización...')
            if not self._apply_update(extract_path):
                raise InstallationError('Error al aplicar actualización')
            
            # Actualizar información de versión
            self._report_progress(90, 'Finalizando...')
            self._save_version_info(update_info.version, {
                'previous_version': self.current_version,
                'update_date': datetime.now().isoformat(),
                'changelog': update_info.changelog
            })
            
            # Limpiar archivos temporales
            self._cleanup_temp_files()
            
            self._log('INFO', f'Actualización v{update_info.version} instalada exitosamente')
            self._report_progress(100, 'Actualización completada')
            
            return True
            
        except Exception as e:
            self._log('ERROR', f'Error durante instalación: {e}')
            self._report_progress(100, f'Error: {e}')
            
            # Intentar rollback si hay error
            if self.config.backup_enabled:
                self._log('INFO', 'Intentando rollback...')
                self._attempt_rollback()
            
            return False
            
        finally:
            self.is_updating = False
    
    def _validate_update_structure(self, extract_path: Path) -> bool:
        """Valida la estructura de una actualización extraída."""
        try:
            # Verificar archivos esenciales
            required_files = ['main.py']
            required_dirs = ['core', 'gui', 'utils']
            
            for file_name in required_files:
                if not (extract_path / file_name).exists():
                    self._log('ERROR', f'Archivo requerido faltante: {file_name}')
                    return False
            
            for dir_name in required_dirs:
                if not (extract_path / dir_name).is_dir():
                    self._log('ERROR', f'Directorio requerido faltante: {dir_name}')
                    return False
            
            return True
            
        except Exception as e:
            self._log('ERROR', f'Error al validar estructura: {e}')
            return False
    
    def _apply_update(self, extract_path: Path) -> bool:
        """Aplica los archivos de actualización."""
        try:
            # Obtener lista de archivos a actualizar
            update_files = []
            for root, dirs, files in os.walk(extract_path):
                for file in files:
                    src_path = Path(root) / file
                    rel_path = src_path.relative_to(extract_path)
                    update_files.append((src_path, self.app_dir / rel_path))
            
            # Aplicar archivos
            total_files = len(update_files)
            for i, (src_path, dest_path) in enumerate(update_files):
                # Crear directorio padre si no existe
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copiar archivo
                shutil.copy2(src_path, dest_path)
                
                progress = int(((i + 1) / total_files) * 100)
                if progress % 10 == 0:  # Reportar cada 10%
                    self._report_progress(70 + (progress // 5), f'Copiando archivos... {i+1}/{total_files}')
            
            return True
            
        except Exception as e:
            self._log('ERROR', f'Error al aplicar actualización: {e}')
            return False
    
    def _attempt_rollback(self) -> bool:
        """Intenta hacer rollback a la versión anterior."""
        try:
            # Buscar el respaldo más reciente
            if not self.backup_dir.exists():
                self._log('ERROR', 'No hay directorio de respaldos')
                return False
            
            backup_dirs = [d for d in self.backup_dir.iterdir() if d.is_dir() and d.name.startswith('backup_')]
            if not backup_dirs:
                self._log('ERROR', 'No hay respaldos disponibles')
                return False
            
            # Ordenar por fecha de creación (más reciente primero)
            backup_dirs.sort(key=lambda x: x.stat().st_ctime, reverse=True)
            latest_backup = backup_dirs[0]
            
            self._log('INFO', f'Restaurando desde respaldo: {latest_backup}')
            
            # Restaurar archivos
            for item in latest_backup.iterdir():
                if item.name == 'backup_info.json':
                    continue
                
                dest_path = self.app_dir / item.name
                
                if item.is_file():
                    shutil.copy2(item, dest_path)
                elif item.is_dir():
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(item, dest_path)
            
            self._log('INFO', 'Rollback completado')
            return True
            
        except Exception as e:
            self._log('ERROR', f'Error durante rollback: {e}')
            return False
    
    def _cleanup_temp_files(self):
        """Limpia archivos temporales de actualización."""
        try:
            if self.temp_dir.exists():
                for item in self.temp_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                        
        except Exception as e:
            self._log('WARNING', f'Error al limpiar archivos temporales: {e}')
    
    def get_update_history(self) -> list:
        """Obtiene el historial de actualizaciones."""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                    return version_data.get('update_history', [])
            return []
            
        except Exception as e:
            self._log('ERROR', f'Error al obtener historial: {e}')
            return []
    
    def should_check_for_updates(self) -> bool:
        """Determina si es momento de verificar actualizaciones."""
        if not self.last_check:
            return True
        
        time_since_check = datetime.now() - self.last_check
        return time_since_check >= timedelta(hours=self.config.check_frequency_hours)
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del sistema de actualizaciones."""
        return {
            'current_version': self.current_version,
            'is_updating': self.is_updating,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'next_check': (self.last_check + timedelta(hours=self.config.check_frequency_hours)).isoformat() if self.last_check else None,
            'config': {
                'auto_download': self.config.auto_download,
                'auto_install': self.config.auto_install,
                'check_frequency_hours': self.config.check_frequency_hours
            }
        }