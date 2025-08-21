#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz de Usuario para Actualizaciones - Automatización de Compresión de Archivos

Este módulo contiene las ventanas y diálogos para el sistema de actualizaciones.

Autor: Sistema de Automatización
Versión: 1.0
Fecha: 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from typing import Callable, Optional
from datetime import datetime
from core.updater import UpdateInfo, Updater
from pathlib import Path


class UpdateNotificationDialog:
    """Diálogo de notificación de actualización disponible."""
    
    def __init__(self, parent, update_info: UpdateInfo, on_update: Callable = None, on_dismiss: Callable = None):
        """Inicializa el diálogo de notificación.
        
        Args:
            parent: Ventana padre
            update_info: Información de la actualización
            on_update: Callback cuando el usuario acepta actualizar
            on_dismiss: Callback cuando el usuario rechaza
        """
        self.parent = parent
        self.update_info = update_info
        self.on_update = on_update
        self.on_dismiss = on_dismiss
        
        self.dialog = None
        self.result = None
        
    def show(self) -> str:
        """Muestra el diálogo y retorna la respuesta del usuario.
        
        Returns:
            'update', 'later', o 'dismiss'
        """
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Actualización Disponible")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Centrar en la pantalla
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        self._create_widgets()
        
        # Esperar respuesta
        self.dialog.wait_window()
        return self.result or 'dismiss'
    
    def _create_widgets(self):
        """Crea los widgets del diálogo."""
        # Frame principal
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Icono y título
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Título
        title_label = ttk.Label(
            header_frame,
            text="🔄 Nueva Actualización Disponible",
            font=('Segoe UI', 14, 'bold')
        )
        title_label.pack(anchor=tk.W)
        
        # Información de versión
        version_frame = ttk.LabelFrame(main_frame, text="Información de Versión", padding=10)
        version_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Versión actual vs nueva
        ttk.Label(version_frame, text="Versión Actual:", font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(version_frame, text="v1.0.0").grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(version_frame, text="Nueva Versión:", font=('Segoe UI', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        new_version_label = ttk.Label(version_frame, text=f"v{self.update_info.version}", foreground='green')
        new_version_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # Fecha de lanzamiento
        if self.update_info.release_date:
            ttk.Label(version_frame, text="Fecha de Lanzamiento:", font=('Segoe UI', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
            ttk.Label(version_frame, text=self.update_info.release_date).grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        # Tamaño de descarga
        if self.update_info.file_size > 0:
            size_mb = self.update_info.file_size / (1024 * 1024)
            ttk.Label(version_frame, text="Tamaño:", font=('Segoe UI', 9, 'bold')).grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
            ttk.Label(version_frame, text=f"{size_mb:.1f} MB").grid(row=3, column=1, sticky=tk.W, pady=(5, 0))
        
        # Indicador de actualización crítica
        if self.update_info.is_critical:
            critical_frame = ttk.Frame(main_frame)
            critical_frame.pack(fill=tk.X, pady=(0, 10))
            
            critical_label = ttk.Label(
                critical_frame,
                text="⚠️ Esta es una actualización crítica de seguridad",
                foreground='red',
                font=('Segoe UI', 9, 'bold')
            )
            critical_label.pack(anchor=tk.W)
        
        # Changelog
        if self.update_info.changelog:
            changelog_frame = ttk.LabelFrame(main_frame, text="Novedades", padding=10)
            changelog_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
            
            changelog_text = scrolledtext.ScrolledText(
                changelog_frame,
                height=8,
                wrap=tk.WORD,
                font=('Segoe UI', 9)
            )
            changelog_text.pack(fill=tk.BOTH, expand=True)
            changelog_text.insert(tk.END, self.update_info.changelog)
            changelog_text.config(state=tk.DISABLED)
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Botón Actualizar Ahora
        update_btn = ttk.Button(
            button_frame,
            text="🔄 Actualizar Ahora",
            command=self._on_update_now,
            style='Accent.TButton'
        )
        update_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Botón Más Tarde
        later_btn = ttk.Button(
            button_frame,
            text="⏰ Más Tarde",
            command=self._on_update_later
        )
        later_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Botón Omitir (solo si no es crítica)
        if not self.update_info.is_critical:
            dismiss_btn = ttk.Button(
                button_frame,
                text="❌ Omitir Esta Versión",
                command=self._on_dismiss
            )
            dismiss_btn.pack(side=tk.RIGHT)
        
        # Configurar foco inicial
        update_btn.focus_set()
        
        # Manejar cierre de ventana
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _on_update_now(self):
        """Maneja el botón 'Actualizar Ahora'."""
        self.result = 'update'
        if self.on_update:
            self.on_update()
        self.dialog.destroy()
    
    def _on_update_later(self):
        """Maneja el botón 'Más Tarde'."""
        self.result = 'later'
        self.dialog.destroy()
    
    def _on_dismiss(self):
        """Maneja el botón 'Omitir Esta Versión'."""
        self.result = 'dismiss'
        if self.on_dismiss:
            self.on_dismiss()
        self.dialog.destroy()
    
    def _on_close(self):
        """Maneja el cierre de la ventana."""
        self.result = 'later'
        self.dialog.destroy()


class UpdateProgressDialog:
    """Diálogo de progreso de actualización."""
    
    def __init__(self, parent, update_info: UpdateInfo):
        """Inicializa el diálogo de progreso.
        
        Args:
            parent: Ventana padre
            update_info: Información de la actualización
        """
        self.parent = parent
        self.update_info = update_info
        
        self.dialog = None
        self.progress_var = None
        self.status_var = None
        self.detail_var = None
        self.cancel_requested = False
        
        self.updater = None
        self.update_thread = None
    
    def show(self, updater: Updater) -> bool:
        """Muestra el diálogo de progreso y ejecuta la actualización.
        
        Args:
            updater: Instancia del actualizador
            
        Returns:
            True si la actualización fue exitosa
        """
        self.updater = updater
        
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Actualizando Aplicación")
        self.dialog.geometry("450x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Centrar en la pantalla
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 75,
            self.parent.winfo_rooty() + 75
        ))
        
        self._create_widgets()
        
        # Iniciar actualización en hilo separado
        self.update_thread = threading.Thread(target=self._run_update, daemon=True)
        self.update_thread.start()
        
        # Esperar a que termine
        self.dialog.wait_window()
        
        return not self.cancel_requested
    
    def _create_widgets(self):
        """Crea los widgets del diálogo."""
        # Frame principal
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text=f"Actualizando a v{self.update_info.version}",
            font=('Segoe UI', 12, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Estado actual
        self.status_var = tk.StringVar(value="Preparando actualización...")
        status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=('Segoe UI', 10)
        )
        status_label.pack(pady=(0, 10))
        
        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode='determinate'
        )
        progress_bar.pack(pady=(0, 10))
        
        # Detalles
        self.detail_var = tk.StringVar(value="")
        detail_label = ttk.Label(
            main_frame,
            textvariable=self.detail_var,
            font=('Segoe UI', 8),
            foreground='gray'
        )
        detail_label.pack(pady=(0, 20))
        
        # Log de progreso
        log_frame = ttk.LabelFrame(main_frame, text="Detalles", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=6,
            wrap=tk.WORD,
            font=('Consolas', 8),
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Botón cancelar (inicialmente deshabilitado)
        self.cancel_btn = ttk.Button(
            main_frame,
            text="Cancelar",
            command=self._on_cancel,
            state=tk.DISABLED
        )
        self.cancel_btn.pack()
        
        # Manejar cierre de ventana
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _run_update(self):
        """Ejecuta el proceso de actualización."""
        try:
            # Configurar callback de progreso
            self.updater.progress_callback = self._update_progress
            
            # Paso 1: Descargar actualización
            self._log_message("Iniciando descarga...")
            download_path = self.updater.download_update(self.update_info)
            
            if self.cancel_requested:
                return
            
            if not download_path:
                self._show_error("Error al descargar la actualización")
                return
            
            # Paso 2: Instalar actualización
            self._log_message("Iniciando instalación...")
            success = self.updater.install_update(download_path, self.update_info)
            
            if success and not self.cancel_requested:
                self._show_success()
            elif not success:
                self._show_error("Error durante la instalación")
                
        except Exception as e:
            self._show_error(f"Error inesperado: {e}")
    
    def _update_progress(self, percentage: int, message: str):
        """Actualiza el progreso en la interfaz."""
        if self.cancel_requested:
            return
        
        # Actualizar en el hilo principal
        self.dialog.after(0, lambda: self._update_ui(percentage, message))
    
    def _update_ui(self, percentage: int, message: str):
        """Actualiza la interfaz de usuario."""
        if self.progress_var:
            self.progress_var.set(percentage)
        
        if self.status_var:
            self.status_var.set(message)
        
        self._log_message(f"[{percentage}%] {message}")
        
        # Habilitar cancelar solo durante descarga
        if "Descargando" in message and self.cancel_btn:
            self.cancel_btn.config(state=tk.NORMAL)
        elif percentage >= 70 and self.cancel_btn:  # Deshabilitar durante instalación
            self.cancel_btn.config(state=tk.DISABLED)
    
    def _log_message(self, message: str):
        """Agrega un mensaje al log."""
        if not self.log_text:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _show_success(self):
        """Muestra mensaje de éxito."""
        self.dialog.after(0, lambda: self._show_success_ui())
    
    def _show_success_ui(self):
        """Muestra la interfaz de éxito."""
        self.progress_var.set(100)
        self.status_var.set("¡Actualización completada exitosamente!")
        self._log_message("Actualización finalizada. La aplicación se reiniciará.")
        
        # Cambiar botón a "Reiniciar"
        self.cancel_btn.config(text="Reiniciar Aplicación", state=tk.NORMAL, command=self._on_restart)
    
    def _show_error(self, error_message: str):
        """Muestra mensaje de error."""
        self.dialog.after(0, lambda: self._show_error_ui(error_message))
    
    def _show_error_ui(self, error_message: str):
        """Muestra la interfaz de error."""
        self.status_var.set(f"Error: {error_message}")
        self._log_message(f"ERROR: {error_message}")
        
        # Cambiar botón a "Cerrar"
        self.cancel_btn.config(text="Cerrar", state=tk.NORMAL, command=self._on_close)
        
        # Mostrar mensaje de error
        messagebox.showerror(
            "Error de Actualización",
            f"No se pudo completar la actualización:\n\n{error_message}\n\nRevise los detalles para más información."
        )
    
    def _on_cancel(self):
        """Maneja la cancelación de la actualización."""
        if messagebox.askyesno(
            "Cancelar Actualización",
            "¿Está seguro de que desea cancelar la actualización?\n\nEsto puede dejar la aplicación en un estado inconsistente."
        ):
            self.cancel_requested = True
            self.status_var.set("Cancelando...")
            self.cancel_btn.config(state=tk.DISABLED)
            
            # Cerrar después de un momento
            self.dialog.after(2000, self._on_close)
    
    def _on_restart(self):
        """Maneja el reinicio de la aplicación."""
        self.dialog.destroy()
        
        # Mostrar mensaje de reinicio
        if messagebox.askyesno(
            "Reiniciar Aplicación",
            "La actualización se completó exitosamente.\n\n¿Desea reiniciar la aplicación ahora para aplicar los cambios?"
        ):
            self._restart_application()
    
    def _restart_application(self):
        """Reinicia la aplicación."""
        try:
            import sys
            import subprocess
            
            if getattr(sys, 'frozen', False):
                # Aplicación compilada
                subprocess.Popen([sys.executable])
            else:
                # Aplicación en desarrollo
                subprocess.Popen([sys.executable, 'main.py'])
            
            # Cerrar aplicación actual
            self.parent.quit()
            
        except Exception as e:
            messagebox.showerror(
                "Error de Reinicio",
                f"No se pudo reiniciar automáticamente:\n{e}\n\nPor favor, reinicie manualmente la aplicación."
            )
    
    def _on_close(self):
        """Maneja el cierre de la ventana."""
        if self.update_thread and self.update_thread.is_alive():
            self.cancel_requested = True
        
        self.dialog.destroy()


class UpdateSettingsDialog:
    """Diálogo de configuración de actualizaciones."""
    
    def __init__(self, parent, config_manager):
        """Inicializa el diálogo de configuración.
        
        Args:
            parent: Ventana padre
            config_manager: Gestor de configuración
        """
        self.parent = parent
        self.config_manager = config_manager
        
        self.dialog = None
        self.result = False
        
        # Variables de configuración
        self.auto_check_var = None
        self.auto_download_var = None
        self.auto_install_var = None
        self.frequency_var = None
        self.backup_var = None
        self.prereleases_var = None
    
    def show(self) -> bool:
        """Muestra el diálogo de configuración.
        
        Returns:
            True si se guardaron cambios
        """
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Configuración de Actualizaciones")
        self.dialog.geometry("400x350")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Centrar en la pantalla
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 100,
            self.parent.winfo_rooty() + 100
        ))
        
        self._create_widgets()
        self._load_current_settings()
        
        # Esperar respuesta
        self.dialog.wait_window()
        return self.result
    
    def _create_widgets(self):
        """Crea los widgets del diálogo."""
        # Frame principal
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="Configuración de Actualizaciones",
            font=('Segoe UI', 12, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Verificación automática
        check_frame = ttk.LabelFrame(main_frame, text="Verificación Automática", padding=10)
        check_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.auto_check_var = tk.BooleanVar()
        auto_check_cb = ttk.Checkbutton(
            check_frame,
            text="Verificar actualizaciones automáticamente",
            variable=self.auto_check_var
        )
        auto_check_cb.pack(anchor=tk.W)
        
        # Frecuencia
        freq_frame = ttk.Frame(check_frame)
        freq_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(freq_frame, text="Frecuencia:").pack(side=tk.LEFT)
        
        self.frequency_var = tk.StringVar()
        freq_combo = ttk.Combobox(
            freq_frame,
            textvariable=self.frequency_var,
            values=["6 horas", "12 horas", "24 horas", "48 horas", "7 días"],
            state="readonly",
            width=15
        )
        freq_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Descarga automática
        download_frame = ttk.LabelFrame(main_frame, text="Descarga Automática", padding=10)
        download_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.auto_download_var = tk.BooleanVar()
        auto_download_cb = ttk.Checkbutton(
            download_frame,
            text="Descargar actualizaciones automáticamente",
            variable=self.auto_download_var
        )
        auto_download_cb.pack(anchor=tk.W)
        
        # Instalación automática
        install_frame = ttk.LabelFrame(main_frame, text="Instalación Automática", padding=10)
        install_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.auto_install_var = tk.BooleanVar()
        auto_install_cb = ttk.Checkbutton(
            install_frame,
            text="Instalar actualizaciones automáticamente",
            variable=self.auto_install_var
        )
        auto_install_cb.pack(anchor=tk.W)
        
        ttk.Label(
            install_frame,
            text="⚠️ Solo se instalarán automáticamente actualizaciones no críticas",
            font=('Segoe UI', 8),
            foreground='orange'
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # Opciones adicionales
        options_frame = ttk.LabelFrame(main_frame, text="Opciones Adicionales", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.backup_var = tk.BooleanVar()
        backup_cb = ttk.Checkbutton(
            options_frame,
            text="Crear respaldo antes de actualizar",
            variable=self.backup_var
        )
        backup_cb.pack(anchor=tk.W)
        
        self.prereleases_var = tk.BooleanVar()
        prereleases_cb = ttk.Checkbutton(
            options_frame,
            text="Incluir versiones beta/pre-lanzamiento",
            variable=self.prereleases_var
        )
        prereleases_cb.pack(anchor=tk.W, pady=(5, 0))
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="Cancelar",
            command=self._on_cancel
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="Guardar",
            command=self._on_save
        ).pack(side=tk.RIGHT)
        
        # Manejar cierre de ventana
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _load_current_settings(self):
        """Carga la configuración actual."""
        try:
            config = self.config_manager.get_config()
            update_config = config.get('updates', {})
            
            self.auto_check_var.set(update_config.get('auto_check', True))
            self.auto_download_var.set(update_config.get('auto_download', False))
            self.auto_install_var.set(update_config.get('auto_install', False))
            self.backup_var.set(update_config.get('backup_enabled', True))
            self.prereleases_var.set(update_config.get('allow_prereleases', False))
            
            # Frecuencia
            frequency_hours = update_config.get('check_frequency_hours', 24)
            frequency_map = {
                6: "6 horas",
                12: "12 horas",
                24: "24 horas",
                48: "48 horas",
                168: "7 días"
            }
            self.frequency_var.set(frequency_map.get(frequency_hours, "24 horas"))
            
        except Exception as e:
            # Valores por defecto
            self.auto_check_var.set(True)
            self.auto_download_var.set(False)
            self.auto_install_var.set(False)
            self.backup_var.set(True)
            self.prereleases_var.set(False)
            self.frequency_var.set("24 horas")
    
    def _on_save(self):
        """Guarda la configuración."""
        try:
            # Mapear frecuencia
            frequency_map = {
                "6 horas": 6,
                "12 horas": 12,
                "24 horas": 24,
                "48 horas": 48,
                "7 días": 168
            }
            
            update_config = {
                'auto_check': self.auto_check_var.get(),
                'auto_download': self.auto_download_var.get(),
                'auto_install': self.auto_install_var.get(),
                'backup_enabled': self.backup_var.get(),
                'allow_prereleases': self.prereleases_var.get(),
                'check_frequency_hours': frequency_map.get(self.frequency_var.get(), 24)
            }
            
            # Guardar configuración
            config = self.config_manager.get_config()
            config['updates'] = update_config
            self.config_manager.save_config(config)
            
            self.result = True
            self.dialog.destroy()
            
            messagebox.showinfo(
                "Configuración Guardada",
                "La configuración de actualizaciones se ha guardado correctamente."
            )
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo guardar la configuración:\n{e}"
            )
    
    def _on_cancel(self):
        """Cancela los cambios."""
        self.result = False
        self.dialog.destroy()