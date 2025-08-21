#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ventana Principal - Automatización de Compresión de Archivos

Este módulo contiene la interfaz gráfica principal de la aplicación,
incluyendo todas las pestañas, controles y funcionalidades de usuario.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
from typing import Optional, Dict, Any
import os

# Importar módulos del core
from core.config_manager import ConfigManager
from core.logger import CustomLogger
from core.compressor import CompressorEngine, CompressionConfig
from core.file_manager import FileManager
from core.updater import Updater, UpdateConfig, UpdateInfo
from utils.validators import validate_compression_config, PathValidator
from utils.helpers import FileUtils, TimeUtils, create_progress_bar
from gui.update_dialog import UpdateNotificationDialog, UpdateProgressDialog, UpdateSettingsDialog


class MainWindow:
    """Ventana principal de la aplicación."""
    
    def __init__(self):
        """Inicializa la ventana principal."""
        # Inicializar componentes del core
        self.config_manager = ConfigManager()
        self.logger = CustomLogger()
        self.compressor = CompressorEngine(self.config_manager, self.logger)
        self.file_manager = FileManager(self.logger)
        
        # Inicializar sistema de actualizaciones
        self.updater = None
        self.update_config = None
        self._init_updater()
        
        # Variables de estado
        self.current_profile = "default"
        self.is_processing = False
        self.processing_thread: Optional[threading.Thread] = None
        
        # Configurar callbacks
        self.compressor.set_progress_callback(self.update_progress)
        self.compressor.set_file_callback(self.update_file_status)
        self.logger.add_ui_callback(self.update_log_display)
        
        # Crear interfaz
        self.setup_ui()
        self.load_current_profile()
        
        # Verificar actualizaciones al inicio (en hilo separado)
        self._check_updates_on_startup()
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Ventana principal
        self.root = tk.Tk()
        self.root.title("Automatización de Compresión de Archivos v1.0")
        self.root.geometry("1024x768")
        self.root.minsize(800, 600)
        
        # Configurar estilo
        self.setup_styles()
        
        # Crear menú
        self.create_menu()
        
        # Crear notebook para pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Crear pestañas
        self.create_main_tab()
        self.create_config_tab()
        self.create_progress_tab()
        self.create_profiles_tab()
        
        # Barra de estado
        self.create_status_bar()
        
        # Configurar eventos
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_styles(self):
        """Configura los estilos de la interfaz."""
        try:
            from ttkthemes import ThemedTk, ThemedStyle
            # Si ttkthemes está disponible, usar tema moderno
            style = ThemedStyle(self.root)
            style.set_theme("arc")  # Tema moderno
        except ImportError:
            # Usar estilo por defecto si no está disponible
            style = ttk.Style()
        
        # Configurar colores personalizados
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Subtitle.TLabel', font=('Segoe UI', 10))
        style.configure('Success.TLabel', foreground='#4CAF50')
        style.configure('Error.TLabel', foreground='#F44336')
        style.configure('Warning.TLabel', foreground='#FF9800')
    
    def create_menu(self):
        """Crea la barra de menú."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Nuevo Perfil", command=self.new_profile)
        file_menu.add_command(label="Importar Perfil", command=self.import_profile)
        file_menu.add_command(label="Exportar Perfil", command=self.export_profile)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.on_closing)
        
        # Menú Herramientas
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
        tools_menu.add_command(label="Limpiar Logs", command=self.clean_logs)
        tools_menu.add_command(label="Verificar Sistema", command=self.check_system)
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Buscar Actualizaciones", command=self.check_for_updates_manual)
        help_menu.add_command(label="Configurar Actualizaciones", command=self.show_update_settings)
        help_menu.add_separator()
        help_menu.add_command(label="Acerca de", command=self.show_about)
    
    def create_main_tab(self):
        """Crea la pestaña principal."""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Principal")
        
        # Frame para selección de carpetas
        folders_frame = ttk.LabelFrame(main_frame, text="Carpetas", padding=10)
        folders_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Carpeta origen
        ttk.Label(folders_frame, text="Carpeta origen:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.source_var = tk.StringVar()
        source_entry = ttk.Entry(folders_frame, textvariable=self.source_var, width=50)
        source_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
        ttk.Button(folders_frame, text="Examinar", 
                  command=self.browse_source_folder).grid(row=0, column=2, padx=5, pady=2)
        
        # Carpeta de respaldo
        ttk.Label(folders_frame, text="Carpeta de respaldo:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.backup_var = tk.StringVar()
        backup_entry = ttk.Entry(folders_frame, textvariable=self.backup_var, width=50)
        backup_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)
        ttk.Button(folders_frame, text="Examinar", 
                  command=self.browse_backup_folder).grid(row=1, column=2, padx=5, pady=2)
        
        folders_frame.columnconfigure(1, weight=1)
        
        # Frame para opciones básicas
        options_frame = ttk.LabelFrame(main_frame, text="Opciones Básicas", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Incluir subcarpetas
        self.include_subfolders_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Incluir subcarpetas", 
                       variable=self.include_subfolders_var).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # Nivel de compresión
        ttk.Label(options_frame, text="Nivel de compresión:").grid(row=0, column=1, padx=20, pady=2)
        self.compression_level_var = tk.IntVar(value=6)
        compression_scale = ttk.Scale(options_frame, from_=0, to=9, 
                                    variable=self.compression_level_var, orient=tk.HORIZONTAL)
        compression_scale.grid(row=0, column=2, padx=5, pady=2, sticky=tk.EW)
        self.compression_label = ttk.Label(options_frame, text="6 (Normal)")
        self.compression_label.grid(row=0, column=3, padx=5, pady=2)
        
        # Actualizar etiqueta de compresión
        def update_compression_label(event=None):
            level = int(self.compression_level_var.get())
            labels = {0: "0 (Sin compresión)", 1: "1 (Rápido)", 6: "6 (Normal)", 9: "9 (Máximo)"}
            self.compression_label.config(text=labels.get(level, f"{level}"))
        
        compression_scale.config(command=update_compression_label)
        
        options_frame.columnconfigure(2, weight=1)
        
        # Frame para controles de proceso
        control_frame = ttk.LabelFrame(main_frame, text="Control de Proceso", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Botones de control
        self.start_button = ttk.Button(control_frame, text="Iniciar Compresión", 
                                      command=self.start_compression, style='Accent.TButton')
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = ttk.Button(control_frame, text="Pausar", 
                                      command=self.pause_compression, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Detener", 
                                     command=self.stop_compression, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Información de archivos
        info_frame = ttk.LabelFrame(main_frame, text="Información", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.info_text = tk.Text(info_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.config(yscrollcommand=info_scrollbar.set)
        
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_config_tab(self):
        """Crea la pestaña de configuración."""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="Configuración")
        
        # Frame para patrones de nomenclatura
        naming_frame = ttk.LabelFrame(config_frame, text="Nomenclatura de Archivos", padding=10)
        naming_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(naming_frame, text="Patrón de nomenclatura:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.naming_pattern_var = tk.StringVar(value="fecha_archivo")
        patterns = list(self.config_manager.get_naming_patterns().keys())
        pattern_combo = ttk.Combobox(naming_frame, textvariable=self.naming_pattern_var, 
                                   values=patterns, state="readonly")
        pattern_combo.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
        pattern_combo.bind('<<ComboboxSelected>>', self.on_pattern_change)
        
        # Patrón personalizado
        ttk.Label(naming_frame, text="Patrón personalizado:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.custom_pattern_var = tk.StringVar()
        self.custom_pattern_entry = ttk.Entry(naming_frame, textvariable=self.custom_pattern_var, 
                                            state=tk.DISABLED)
        self.custom_pattern_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)
        
        # Vista previa
        ttk.Label(naming_frame, text="Vista previa:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.preview_label = ttk.Label(naming_frame, text="2024-01-15_documento.pdf.zip", 
                                     style='Subtitle.TLabel')
        self.preview_label.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        
        naming_frame.columnconfigure(1, weight=1)
        
        # Frame para filtros de archivo
        filters_frame = ttk.LabelFrame(config_frame, text="Filtros de Archivo", padding=10)
        filters_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filters_frame, text="Tipos de archivo:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.file_filter_var = tk.StringVar(value="todos")
        filter_presets = self.config_manager.config_data.get('file_filters_presets', {})
        filter_combo = ttk.Combobox(filters_frame, textvariable=self.file_filter_var,
                                  values=list(filter_presets.keys()), state="readonly")
        filter_combo.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
        
        # Filtros personalizados
        ttk.Label(filters_frame, text="Filtros personalizados:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.custom_filters_var = tk.StringVar(value="*.pdf, *.jpg, *.docx")
        ttk.Entry(filters_frame, textvariable=self.custom_filters_var).grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)
        
        filters_frame.columnconfigure(1, weight=1)
        
        # Frame para manejo de conflictos
        conflicts_frame = ttk.LabelFrame(config_frame, text="Manejo de Conflictos", padding=10)
        conflicts_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(conflicts_frame, text="Cuando el archivo ZIP ya existe:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.conflict_resolution_var = tk.StringVar(value="rename")
        resolutions = list(self.config_manager.get_conflict_resolutions().keys())
        ttk.Combobox(conflicts_frame, textvariable=self.conflict_resolution_var,
                    values=resolutions, state="readonly").grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
        
        conflicts_frame.columnconfigure(1, weight=1)
        
        # Frame para opciones avanzadas
        advanced_frame = ttk.LabelFrame(config_frame, text="Opciones Avanzadas", padding=10)
        advanced_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.verify_integrity_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Verificar integridad de archivos ZIP",
                       variable=self.verify_integrity_var).pack(anchor=tk.W, pady=2)
        
        self.auto_backup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Mover archivos originales a respaldo automáticamente",
                       variable=self.auto_backup_var).pack(anchor=tk.W, pady=2)
    
    def create_progress_tab(self):
        """Crea la pestaña de progreso y logging."""
        progress_frame = ttk.Frame(self.notebook)
        self.notebook.add(progress_frame, text="Progreso")
        
        # Frame para barra de progreso
        progress_info_frame = ttk.LabelFrame(progress_frame, text="Progreso Actual", padding=10)
        progress_info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_info_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Etiquetas de información
        info_subframe = ttk.Frame(progress_info_frame)
        info_subframe.pack(fill=tk.X, pady=5)
        
        self.current_file_label = ttk.Label(info_subframe, text="Archivo actual: -")
        self.current_file_label.pack(anchor=tk.W)
        
        self.progress_label = ttk.Label(info_subframe, text="Progreso: 0/0 (0%)")
        self.progress_label.pack(anchor=tk.W)
        
        self.time_label = ttk.Label(info_subframe, text="Tiempo transcurrido: 0s")
        self.time_label.pack(anchor=tk.W)
        
        self.eta_label = ttk.Label(info_subframe, text="Tiempo estimado restante: -")
        self.eta_label.pack(anchor=tk.W)
        
        # Frame para estadísticas
        stats_frame = ttk.LabelFrame(progress_frame, text="Estadísticas", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        stats_subframe = ttk.Frame(stats_frame)
        stats_subframe.pack(fill=tk.X)
        
        # Columna izquierda
        left_stats = ttk.Frame(stats_subframe)
        left_stats.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.processed_label = ttk.Label(left_stats, text="Procesados: 0", style='Success.TLabel')
        self.processed_label.pack(anchor=tk.W)
        
        self.failed_label = ttk.Label(left_stats, text="Errores: 0", style='Error.TLabel')
        self.failed_label.pack(anchor=tk.W)
        
        self.skipped_label = ttk.Label(left_stats, text="Omitidos: 0", style='Warning.TLabel')
        self.skipped_label.pack(anchor=tk.W)
        
        # Columna derecha
        right_stats = ttk.Frame(stats_subframe)
        right_stats.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.compression_ratio_label = ttk.Label(right_stats, text="Ratio de compresión: 0%")
        self.compression_ratio_label.pack(anchor=tk.W)
        
        self.space_saved_label = ttk.Label(right_stats, text="Espacio ahorrado: 0 B")
        self.space_saved_label.pack(anchor=tk.W)
        
        self.success_rate_label = ttk.Label(right_stats, text="Tasa de éxito: 0%")
        self.success_rate_label.pack(anchor=tk.W)
        
        # Frame para log en tiempo real
        log_frame = ttk.LabelFrame(progress_frame, text="Log en Tiempo Real", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Crear widget de texto para log
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_text_frame, height=15, wrap=tk.WORD, state=tk.DISABLED,
                               font=('Consolas', 9))
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configurar colores para diferentes tipos de log
        self.log_text.tag_configure('INFO', foreground='#2196F3')
        self.log_text.tag_configure('SUCCESS', foreground='#4CAF50')
        self.log_text.tag_configure('WARNING', foreground='#FF9800')
        self.log_text.tag_configure('ERROR', foreground='#F44336')
        
        # Botones de control de log
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(log_controls, text="Limpiar Log", 
                  command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_controls, text="Exportar Log", 
                  command=self.export_log).pack(side=tk.LEFT, padx=5)
    
    def create_profiles_tab(self):
        """Crea la pestaña de gestión de perfiles."""
        profiles_frame = ttk.Frame(self.notebook)
        self.notebook.add(profiles_frame, text="Perfiles")
        
        # Frame para selección de perfil
        selection_frame = ttk.LabelFrame(profiles_frame, text="Perfil Actual", padding=10)
        selection_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(selection_frame, text="Perfil activo:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.current_profile_var = tk.StringVar(value=self.current_profile)
        self.profile_combo = ttk.Combobox(selection_frame, textvariable=self.current_profile_var,
                                        state="readonly")
        self.profile_combo.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
        self.profile_combo.bind('<<ComboboxSelected>>', self.on_profile_change)
        
        ttk.Button(selection_frame, text="Cargar", 
                  command=self.load_selected_profile).grid(row=0, column=2, padx=5, pady=2)
        
        selection_frame.columnconfigure(1, weight=1)
        
        # Frame para gestión de perfiles
        management_frame = ttk.LabelFrame(profiles_frame, text="Gestión de Perfiles", padding=10)
        management_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Botones de gestión
        buttons_frame = ttk.Frame(management_frame)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(buttons_frame, text="Nuevo Perfil", 
                  command=self.new_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Guardar Actual", 
                  command=self.save_current_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Eliminar", 
                  command=self.delete_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Duplicar", 
                  command=self.duplicate_profile).pack(side=tk.LEFT, padx=5)
        
        # Lista de perfiles con detalles
        list_frame = ttk.LabelFrame(profiles_frame, text="Perfiles Disponibles", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Crear Treeview para mostrar perfiles
        columns = ('Nombre', 'Patrón', 'Carpeta Respaldo', 'Subcarpetas', 'Última Modificación')
        self.profiles_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.profiles_tree.heading(col, text=col)
            self.profiles_tree.column(col, width=150)
        
        # Scrollbar para la lista
        profiles_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                         command=self.profiles_tree.yview)
        self.profiles_tree.config(yscrollcommand=profiles_scrollbar.set)
        
        self.profiles_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        profiles_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Actualizar lista de perfiles
        self.update_profiles_list()
    
    def create_status_bar(self):
        """Crea la barra de estado."""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_bar, text="Listo")
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Información del sistema
        self.system_label = ttk.Label(self.status_bar, text="")
        self.system_label.pack(side=tk.RIGHT, padx=5, pady=2)
        
        self.update_system_info()
    
    # Métodos de eventos y callbacks
    def browse_source_folder(self):
        """Abre diálogo para seleccionar carpeta origen."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta origen")
        if folder:
            self.source_var.set(folder)
            self.update_file_info()
    
    def browse_backup_folder(self):
        """Abre diálogo para seleccionar carpeta de respaldo."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de respaldo")
        if folder:
            self.backup_var.set(folder)
    
    def on_pattern_change(self, event=None):
        """Maneja el cambio de patrón de nomenclatura."""
        pattern = self.naming_pattern_var.get()
        if pattern == 'personalizado':
            self.custom_pattern_entry.config(state=tk.NORMAL)
        else:
            self.custom_pattern_entry.config(state=tk.DISABLED)
        
        self.update_preview()
    
    def update_preview(self):
        """Actualiza la vista previa del nombre de archivo."""
        pattern = self.naming_pattern_var.get()
        if pattern == 'personalizado':
            custom = self.custom_pattern_var.get()
            if custom:
                try:
                    from datetime import datetime
                    preview = custom.format(
                        fecha=datetime.now().strftime('%Y-%m-%d'),
                        nombre_original='documento',
                        contador=1
                    ) + '.zip'
                    self.preview_label.config(text=preview)
                except:
                    self.preview_label.config(text='Patrón inválido')
            else:
                self.preview_label.config(text='Especifique patrón personalizado')
        else:
            patterns = self.config_manager.get_naming_patterns()
            if pattern in patterns:
                try:
                    from datetime import datetime
                    preview = patterns[pattern].format(
                        fecha=datetime.now().strftime('%Y-%m-%d'),
                        nombre_original='documento',
                        contador=1
                    ) + '.zip'
                    self.preview_label.config(text=preview)
                except:
                    self.preview_label.config(text='Error en vista previa')
    
    def update_file_info(self):
        """Actualiza la información de archivos en la carpeta seleccionada."""
        source_folder = self.source_var.get()
        if not source_folder or not Path(source_folder).exists():
            self.update_info_display("Seleccione una carpeta válida")
            return
        
        try:
            # Escanear archivos
            files = self.file_manager.scan_directory(
                Path(source_folder),
                self.include_subfolders_var.get(),
                ['*']  # Todos los archivos por ahora
            )
            
            # Calcular estadísticas
            stats = self.file_manager.get_file_statistics(files)
            
            info_text = f"""Información de la carpeta seleccionada:

Total de archivos: {stats['total_files']}
Tamaño total: {FileUtils.format_file_size(stats['total_size'])}
Tamaño promedio: {FileUtils.format_file_size(stats['average_size'])}

Tipos de archivo encontrados:
"""
            
            for ext, count in stats['extensions'].items():
                info_text += f"  {ext}: {count} archivo(s)\n"
            
            if stats['largest_file']:
                info_text += f"\nArchivo más grande: {stats['largest_file']['name']} ({FileUtils.format_file_size(stats['largest_file']['size'])})"
            
            if stats['smallest_file']:
                info_text += f"\nArchivo más pequeño: {stats['smallest_file']['name']} ({FileUtils.format_file_size(stats['smallest_file']['size'])})"
            
            self.update_info_display(info_text)
            
        except Exception as e:
            self.update_info_display(f"Error al analizar carpeta: {e}")
    
    def update_info_display(self, text: str):
        """Actualiza el display de información."""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, text)
        self.info_text.config(state=tk.DISABLED)
    
    def start_compression(self):
        """Inicia el proceso de compresión."""
        if self.is_processing:
            return
        
        # Validar configuración
        config = self.get_current_config()
        errors = validate_compression_config(config)
        
        if errors:
            messagebox.showerror("Error de Configuración", "\n".join(errors))
            return
        
        # Cambiar estado de la UI
        self.is_processing = True
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Procesando...")
        
        # Limpiar log y estadísticas
        self.clear_log()
        self.reset_statistics()
        
        # Cambiar a pestaña de progreso
        self.notebook.select(2)  # Índice de la pestaña de progreso
        
        # Iniciar proceso en hilo separado
        compression_config = CompressionConfig(**config)
        self.processing_thread = threading.Thread(
            target=self.run_compression,
            args=(compression_config,),
            daemon=True
        )
        self.processing_thread.start()
    
    def run_compression(self, config: CompressionConfig):
        """Ejecuta el proceso de compresión en hilo separado."""
        try:
            result = self.compressor.compress_files(config)
            
            # Actualizar UI en hilo principal
            self.root.after(0, self.on_compression_complete, result)
            
        except Exception as e:
            self.root.after(0, self.on_compression_error, str(e))
    
    def pause_compression(self):
        """Pausa o reanuda el proceso de compresión."""
        if self.compressor.is_paused:
            self.compressor.resume()
            self.pause_button.config(text="Pausar")
            self.status_label.config(text="Procesando...")
        else:
            self.compressor.pause()
            self.pause_button.config(text="Reanudar")
            self.status_label.config(text="Pausado")
    
    def stop_compression(self):
        """Detiene el proceso de compresión."""
        self.compressor.stop()
        self.status_label.config(text="Deteniendo...")
    
    def on_compression_complete(self, result):
        """Maneja la finalización del proceso de compresión."""
        self.is_processing = False
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="Pausar")
        self.stop_button.config(state=tk.DISABLED)
        
        # Actualizar estadísticas finales desde el compressor
        final_stats = self.compressor.get_last_session_stats()
        if final_stats:
            self.update_statistics_display(final_stats)
        
        if result.success:
            self.status_label.config(text="Proceso completado exitosamente")
            # Usar estadísticas del logger si están disponibles, sino usar las del result
            processed_count = final_stats.get('processed_files', result.processed_files) if final_stats else result.processed_files
            failed_count = final_stats.get('failed_files', result.failed_files) if final_stats else result.failed_files
            
            messagebox.showinfo("Proceso Completado", 
                              f"Compresión completada:\n\n"
                              f"Archivos procesados: {processed_count}\n"
                              f"Errores: {failed_count}\n"
                              f"Tiempo: {TimeUtils.format_duration(result.execution_time)}\n"
                              f"Espacio ahorrado: {FileUtils.format_file_size(result.total_size_saved)}")
        else:
            self.status_label.config(text="Proceso completado con errores")
            failed_count = final_stats.get('failed_files', result.failed_files) if final_stats else result.failed_files
            messagebox.showwarning("Proceso Completado con Errores",
                                 f"El proceso se completó pero hubo {failed_count} errores.\n\n"
                                 f"Revise el log para más detalles.")
    
    def on_compression_error(self, error_msg: str):
        """Maneja errores críticos en el proceso de compresión."""
        self.is_processing = False
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="Pausar")
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Error en el proceso")
        
        messagebox.showerror("Error Crítico", f"Error en el proceso de compresión:\n\n{error_msg}")
    
    def update_progress(self, current: int, total: int, current_file: str):
        """Actualiza la barra de progreso y información."""
        if total > 0:
            percentage = (current / total) * 100
            self.progress_var.set(percentage)
            self.progress_label.config(text=f"Progreso: {current}/{total} ({percentage:.1f}%)")
        
        self.current_file_label.config(text=f"Archivo actual: {current_file}")
        
        # Actualizar estadísticas de sesión
        stats = self.logger.get_session_stats()
        if stats:
            self.update_statistics_display(stats)
    
    def update_file_status(self, operation: str, filename: str, status: str):
        """Actualiza el estado de procesamiento de archivos."""
        # Este método se llama desde el compressor para notificar el estado de cada archivo
        pass
    
    def update_log_display(self, level: str, message: str, file_path: str):
        """Actualiza el display de log en tiempo real."""
        # Verificar que log_text esté disponible
        if not hasattr(self, 'log_text') or not self.log_text:
            return
            
        timestamp = TimeUtils.format_timestamp()
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        try:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, log_entry, level)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        except Exception as e:
            # Si hay error, simplemente ignorar para no bloquear la aplicación
            pass
    
    def update_statistics_display(self, stats: Dict[str, Any]):
        """Actualiza el display de estadísticas."""
        self.processed_label.config(text=f"Procesados: {stats.get('processed_files', 0)}")
        self.failed_label.config(text=f"Errores: {stats.get('failed_files', 0)}")
        self.skipped_label.config(text=f"Omitidos: {stats.get('skipped_files', 0)}")
        
        self.compression_ratio_label.config(text=f"Ratio de compresión: {stats.get('compression_ratio', 0):.1f}%")
        self.space_saved_label.config(text=f"Espacio ahorrado: {FileUtils.format_file_size(stats.get('space_saved', 0))}")
        self.success_rate_label.config(text=f"Tasa de éxito: {stats.get('success_rate', 0):.1f}%")
        
        # Actualizar tiempo
        duration = stats.get('duration', '0s')
        self.time_label.config(text=f"Tiempo transcurrido: {duration}")
    
    def reset_statistics(self):
        """Reinicia las estadísticas mostradas."""
        self.progress_var.set(0)
        self.current_file_label.config(text="Archivo actual: -")
        self.progress_label.config(text="Progreso: 0/0 (0%)")
        self.time_label.config(text="Tiempo transcurrido: 0s")
        self.eta_label.config(text="Tiempo estimado restante: -")
        
        self.processed_label.config(text="Procesados: 0")
        self.failed_label.config(text="Errores: 0")
        self.skipped_label.config(text="Omitidos: 0")
        self.compression_ratio_label.config(text="Ratio de compresión: 0%")
        self.space_saved_label.config(text="Espacio ahorrado: 0 B")
        self.success_rate_label.config(text="Tasa de éxito: 0%")
    
    def clear_log(self):
        """Limpia el display de log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def export_log(self):
        """Exporta el log actual a un archivo."""
        filename = filedialog.asksaveasfilename(
            title="Exportar Log",
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        
        if filename:
            try:
                log_content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                messagebox.showinfo("Exportación Exitosa", f"Log exportado a: {filename}")
            except Exception as e:
                messagebox.showerror("Error de Exportación", f"Error al exportar log: {e}")
    
    def get_current_config(self) -> Dict[str, Any]:
        """Obtiene la configuración actual de la UI."""
        # Obtener filtros de archivo
        filter_preset = self.file_filter_var.get()
        if filter_preset == 'personalizado':
            filters = [f.strip() for f in self.custom_filters_var.get().split(',')]
        else:
            presets = self.config_manager.config_data.get('file_filters_presets', {})
            filters = presets.get(filter_preset, ['*'])
        
        return {
            'source_folder': self.source_var.get(),
            'backup_folder': self.backup_var.get(),
            'naming_pattern': self.naming_pattern_var.get(),
            'custom_pattern': self.custom_pattern_var.get(),
            'include_subfolders': self.include_subfolders_var.get(),
            'file_filters': filters,
            'compression_level': int(self.compression_level_var.get()),
            'conflict_resolution': self.conflict_resolution_var.get(),
            'verify_integrity': self.verify_integrity_var.get()
        }
    
    def load_current_profile(self):
        """Carga el perfil actual en la UI."""
        profile = self.config_manager.get_profile(self.current_profile)
        if not profile:
            return
        
        # Cargar valores en la UI
        self.backup_var.set(profile.get('backup_folder', ''))
        self.naming_pattern_var.set(profile.get('naming_pattern', 'fecha_archivo'))
        self.include_subfolders_var.set(profile.get('include_subfolders', False))
        self.compression_level_var.set(profile.get('compression_level', 6))
        self.conflict_resolution_var.set(profile.get('conflict_resolution', 'rename'))
        
        # Actualizar vista previa
        self.on_pattern_change()
        self.update_preview()
        
        # Actualizar lista de perfiles
        self.update_profiles_combo()
    
    def update_profiles_combo(self):
        """Actualiza el combo de perfiles."""
        profiles = self.config_manager.list_profiles()
        self.profile_combo['values'] = profiles
        if self.current_profile not in profiles:
            self.current_profile = 'default'
        self.current_profile_var.set(self.current_profile)
    
    def update_profiles_list(self):
        """Actualiza la lista de perfiles en el TreeView."""
        # Limpiar lista actual
        for item in self.profiles_tree.get_children():
            self.profiles_tree.delete(item)
        
        # Agregar perfiles
        profiles = self.config_manager.list_profiles()
        for profile_name in profiles:
            profile = self.config_manager.get_profile(profile_name)
            if profile:
                self.profiles_tree.insert('', tk.END, values=(
                    profile_name,
                    profile.get('naming_pattern', '-'),
                    profile.get('backup_folder', '-'),
                    'Sí' if profile.get('include_subfolders', False) else 'No',
                    profile.get('last_modified', '-')[:19] if profile.get('last_modified') else '-'
                ))
    
    def on_profile_change(self, event=None):
        """Maneja el cambio de perfil seleccionado."""
        pass  # Se maneja en load_selected_profile
    
    def load_selected_profile(self):
        """Carga el perfil seleccionado."""
        selected_profile = self.current_profile_var.get()
        if selected_profile and selected_profile != self.current_profile:
            self.current_profile = selected_profile
            self.load_current_profile()
            self.status_label.config(text=f"Perfil cargado: {selected_profile}")
    
    def save_current_profile(self):
        """Guarda la configuración actual como perfil."""
        config = self.get_current_config()
        
        # Remover claves que no van en el perfil
        profile_config = {k: v for k, v in config.items() 
                         if k not in ['source_folder']}
        
        if self.config_manager.save_profile(self.current_profile, profile_config):
            self.update_profiles_list()
            self.status_label.config(text=f"Perfil guardado: {self.current_profile}")
            messagebox.showinfo("Perfil Guardado", f"Perfil '{self.current_profile}' guardado exitosamente")
        else:
            messagebox.showerror("Error", "Error al guardar el perfil")
    
    def new_profile(self):
        """Crea un nuevo perfil."""
        from tkinter import simpledialog
        
        name = simpledialog.askstring("Nuevo Perfil", "Nombre del nuevo perfil:")
        if name:
            from utils.validators import InputValidator
            valid, error = InputValidator.validate_profile_name(name)
            if not valid:
                messagebox.showerror("Nombre Inválido", error)
                return
            
            # Verificar si ya existe
            if name in self.config_manager.list_profiles():
                messagebox.showerror("Error", "Ya existe un perfil con ese nombre")
                return
            
            # Crear perfil con configuración actual
            config = self.get_current_config()
            profile_config = {k: v for k, v in config.items() 
                             if k not in ['source_folder']}
            
            if self.config_manager.save_profile(name, profile_config):
                self.current_profile = name
                self.update_profiles_combo()
                self.update_profiles_list()
                self.status_label.config(text=f"Nuevo perfil creado: {name}")
                messagebox.showinfo("Perfil Creado", f"Perfil '{name}' creado exitosamente")
            else:
                messagebox.showerror("Error", "Error al crear el perfil")
    
    def delete_profile(self):
        """Elimina el perfil seleccionado."""
        if self.current_profile == 'default':
            messagebox.showerror("Error", "No se puede eliminar el perfil por defecto")
            return
        
        if messagebox.askyesno("Confirmar Eliminación", 
                              f"¿Está seguro de eliminar el perfil '{self.current_profile}'?"):
            if self.config_manager.delete_profile(self.current_profile):
                self.current_profile = 'default'
                self.load_current_profile()
                self.update_profiles_list()
                self.status_label.config(text="Perfil eliminado")
                messagebox.showinfo("Perfil Eliminado", "Perfil eliminado exitosamente")
            else:
                messagebox.showerror("Error", "Error al eliminar el perfil")
    
    def duplicate_profile(self):
        """Duplica el perfil actual."""
        from tkinter import simpledialog
        
        name = simpledialog.askstring("Duplicar Perfil", 
                                     f"Nombre para la copia de '{self.current_profile}':")
        if name:
            from utils.validators import InputValidator
            valid, error = InputValidator.validate_profile_name(name)
            if not valid:
                messagebox.showerror("Nombre Inválido", error)
                return
            
            # Verificar si ya existe
            if name in self.config_manager.list_profiles():
                messagebox.showerror("Error", "Ya existe un perfil con ese nombre")
                return
            
            # Obtener configuración del perfil actual
            current_config = self.config_manager.get_profile(self.current_profile)
            if current_config and self.config_manager.save_profile(name, current_config):
                self.update_profiles_combo()
                self.update_profiles_list()
                self.status_label.config(text=f"Perfil duplicado: {name}")
                messagebox.showinfo("Perfil Duplicado", f"Perfil duplicado como '{name}'")
            else:
                messagebox.showerror("Error", "Error al duplicar el perfil")
    
    def import_profile(self):
        """Importa un perfil desde archivo."""
        filename = filedialog.askopenfilename(
            title="Importar Perfil",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        
        if filename:
            imported_name = self.config_manager.import_profile(filename)
            if imported_name:
                self.update_profiles_combo()
                self.update_profiles_list()
                self.status_label.config(text=f"Perfil importado: {imported_name}")
                messagebox.showinfo("Importación Exitosa", f"Perfil importado como '{imported_name}'")
            else:
                messagebox.showerror("Error de Importación", "Error al importar el perfil")
    
    def export_profile(self):
        """Exporta el perfil actual a archivo."""
        filename = filedialog.asksaveasfilename(
            title="Exportar Perfil",
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        
        if filename:
            if self.config_manager.export_profile(self.current_profile, filename):
                self.status_label.config(text=f"Perfil exportado: {self.current_profile}")
                messagebox.showinfo("Exportación Exitosa", f"Perfil exportado a: {filename}")
            else:
                messagebox.showerror("Error de Exportación", "Error al exportar el perfil")
    
    def clean_logs(self):
        """Limpia logs antiguos."""
        if messagebox.askyesno("Limpiar Logs", "¿Desea limpiar los archivos de log antiguos?"):
            self.logger.cleanup_old_logs()
            messagebox.showinfo("Logs Limpiados", "Archivos de log antiguos eliminados")
    
    def check_system(self):
        """Verifica el estado del sistema."""
        from utils.helpers import get_system_info
        
        info = get_system_info()
        info_text = "Información del Sistema:\n\n"
        
        for key, value in info.items():
            info_text += f"{key.replace('_', ' ').title()}: {value}\n"
        
        messagebox.showinfo("Información del Sistema", info_text)
    
    def show_about(self):
        """Muestra información sobre la aplicación."""
        about_text = """Automatización de Compresión de Archivos v1.0

Desarrollado para automatizar el proceso de compresión de archivos
con nomenclatura personalizable y gestión inteligente de respaldos.

Desarollado por: Jheron Guzman

Características:
• Compresión individual de archivos
• Patrones de nomenclatura configurables
• Sistema de logging avanzado
• Gestión de perfiles
• Interfaz gráfica intuitiva

© 2024 - Automatización de Facturas y Documentos PDF"""


        
        messagebox.showinfo("Acerca de", about_text)
    
    def update_system_info(self):
        """Actualiza la información del sistema en la barra de estado."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent()
            self.system_label.config(text=f"CPU: {cpu}% | RAM: {memory.percent}%")
        except ImportError:
            self.system_label.config(text="Sistema: OK")
        
        # Programar próxima actualización
        self.root.after(5000, self.update_system_info)
    
    # Métodos del sistema de actualizaciones
    def _init_updater(self):
        """Inicializa el sistema de actualizaciones."""
        try:
            config = self.config_manager.get_config()
            update_settings = config.get('updates', {})
            
            self.update_config = UpdateConfig(
                update_server_url=update_settings.get('update_server_url', 'https://api.github.com/repos/Doberman156/AutoCompresor/releases'),
                check_frequency_hours=update_settings.get('check_frequency_hours', 24),
                auto_download=update_settings.get('auto_download', False),
                auto_install=update_settings.get('auto_install', False),
                backup_enabled=update_settings.get('backup_enabled', True),
                verify_signatures=update_settings.get('verify_signatures', True),
                allow_prereleases=update_settings.get('allow_prereleases', False)
            )
            
            self.updater = Updater(self.update_config, self.logger)
            
        except Exception as e:
            self.logger.log_operation('ERROR', f'Error al inicializar sistema de actualizaciones: {e}')
            self.updater = None
    
    def _check_updates_on_startup(self):
        """Verifica actualizaciones al inicio de la aplicación."""
        if not self.updater:
            return
        
        config = self.config_manager.get_config()
        update_settings = config.get('updates', {})
        
        if not update_settings.get('auto_check', True):
            return
        
        # Verificar en hilo separado para no bloquear la UI
        def check_updates():
            try:
                # Esperar un poco para que la UI se cargue completamente
                import time
                time.sleep(2)
                
                update_info = self.updater.check_for_updates()
                if update_info:
                    # Mostrar notificación en el hilo principal
                    self.root.after(0, lambda: self._show_update_notification(update_info))
                    
            except Exception as e:
                self.logger.log_operation('WARNING', f'Error al verificar actualizaciones: {e}')
        
        update_thread = threading.Thread(target=check_updates, daemon=True)
        update_thread.start()
    
    def _show_update_notification(self, update_info: UpdateInfo):
        """Muestra la notificación de actualización disponible."""
        try:
            dialog = UpdateNotificationDialog(
                self.root,
                update_info,
                on_update=lambda: self._start_update_process(update_info),
                on_dismiss=lambda: self._dismiss_update(update_info)
            )
            
            result = dialog.show()
            
            if result == 'later':
                # Recordar para verificar más tarde
                self.logger.log_operation('INFO', f'Actualización v{update_info.version} pospuesta')
            
        except Exception as e:
            self.logger.log_operation('ERROR', f'Error al mostrar notificación de actualización: {e}')
    
    def _start_update_process(self, update_info: UpdateInfo):
        """Inicia el proceso de actualización."""
        try:
            progress_dialog = UpdateProgressDialog(self.root, update_info)
            success = progress_dialog.show(self.updater)
            
            if success:
                self.logger.log_operation('INFO', f'Actualización v{update_info.version} completada')
            else:
                self.logger.log_operation('WARNING', f'Actualización v{update_info.version} cancelada o falló')
                
        except Exception as e:
            self.logger.log_operation('ERROR', f'Error durante proceso de actualización: {e}')
            messagebox.showerror(
                "Error de Actualización",
                f"Error durante la actualización:\n{e}"
            )
    
    def _dismiss_update(self, update_info: UpdateInfo):
        """Marca una actualización como omitida."""
        try:
            config = self.config_manager.get_config()
            update_settings = config.get('updates', {})
            dismissed = update_settings.get('dismissed_versions', [])
            
            if update_info.version not in dismissed:
                dismissed.append(update_info.version)
                update_settings['dismissed_versions'] = dismissed
                config['updates'] = update_settings
                self.config_manager.save_config(config)
                
                self.logger.log_operation('INFO', f'Actualización v{update_info.version} omitida')
                
        except Exception as e:
            self.logger.log_operation('ERROR', f'Error al omitir actualización: {e}')
    
    def check_for_updates_manual(self):
        """Verifica actualizaciones manualmente desde el menú."""
        if not self.updater:
            messagebox.showerror(
                "Error",
                "Sistema de actualizaciones no disponible"
            )
            return
        
        def check_updates():
            try:
                # Mostrar mensaje de verificación
                self.root.after(0, lambda: self.status_label.config(text="Verificando actualizaciones..."))
                
                update_info = self.updater.check_for_updates(force=True)
                
                if update_info:
                    # Mostrar notificación
                    self.root.after(0, lambda: self._show_update_notification(update_info))
                else:
                    # No hay actualizaciones
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Sin Actualizaciones",
                        "Su aplicación está actualizada a la última versión."
                    ))
                
                self.root.after(0, lambda: self.status_label.config(text="Listo"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Error al verificar actualizaciones:\n{e}"
                ))
                self.root.after(0, lambda: self.status_label.config(text="Error en verificación"))
        
        # Ejecutar en hilo separado
        update_thread = threading.Thread(target=check_updates, daemon=True)
        update_thread.start()
    
    def show_update_settings(self):
        """Muestra el diálogo de configuración de actualizaciones."""
        try:
            dialog = UpdateSettingsDialog(self.root, self.config_manager)
            if dialog.show():
                # Recargar configuración de actualizaciones
                self._init_updater()
                self.status_label.config(text="Configuración de actualizaciones guardada")
                
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al mostrar configuración de actualizaciones:\n{e}"
            )
    
    def on_closing(self):
        """Maneja el cierre de la aplicación."""
        if self.is_processing:
            if messagebox.askyesno("Proceso en Curso", 
                                  "Hay un proceso de compresión en curso. ¿Desea detenerlo y salir?"):
                self.compressor.stop()
                # Esperar un momento para que se detenga
                self.root.after(1000, self.force_close)
            return
        
        # Guardar configuración actual
        self.save_current_profile()
        
        # Cerrar logger
        self.logger.shutdown()
        
        # Cerrar aplicación
        self.root.destroy()
    
    def force_close(self):
        """Fuerza el cierre de la aplicación."""
        self.logger.shutdown()
        self.root.destroy()
    
    def run(self):
        """Ejecuta la aplicación."""
        self.root.mainloop()


if __name__ == "__main__":
    app = MainWindow()
    app.run()