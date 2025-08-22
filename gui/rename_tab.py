#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pestaña de Renombrado Masivo - Automatización de Compresión de Archivos

Este módulo contiene la interfaz gráfica para el renombrado masivo de archivos,
incluyendo operaciones, vista previa y aplicación de cambios.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
import os

# Importar módulos del core y utils
from core.renamer import FileRenamer, RenameOperation, FileRenamePreview
from utils.rename_operations import RenameTemplates, FileNameValidator, TextProcessor, NumberingHelper
from utils.helpers import FileUtils


class RenameTab:
    """Pestaña de renombrado masivo de archivos."""
    
    def __init__(self, parent_notebook, config_manager, logger):
        """Inicializa la pestaña de renombrado."""
        self.parent_notebook = parent_notebook
        self.config_manager = config_manager
        self.logger = logger
        
        # Inicializar renombrador
        self.renamer = FileRenamer(logger)
        
        # Variables de estado
        self.is_processing = False
        self.processing_thread: Optional[threading.Thread] = None
        self.current_preview: List[FileRenamePreview] = []
        
        # Variables de UI
        self.setup_variables()
        
        # Crear interfaz
        self.create_tab()
        
        # Cargar configuración
        self.load_settings()
    
    def setup_variables(self):
        """Configura las variables de la interfaz."""
        # Variables de carpeta y archivos
        self.source_folder_var = tk.StringVar()
        self.include_subfolders_var = tk.BooleanVar(value=False)
        self.file_filter_var = tk.StringVar(value="todos")
        
        # Variables de operaciones
        self.prefix_enabled_var = tk.BooleanVar()
        self.prefix_value_var = tk.StringVar()
        
        self.suffix_enabled_var = tk.BooleanVar()
        self.suffix_value_var = tk.StringVar()
        
        self.replace_enabled_var = tk.BooleanVar()
        self.replace_old_var = tk.StringVar()
        self.replace_new_var = tk.StringVar()
        
        self.remove_enabled_var = tk.BooleanVar()
        self.remove_value_var = tk.StringVar()
        
        self.numbering_enabled_var = tk.BooleanVar()
        self.numbering_start_var = tk.IntVar(value=1)
        self.numbering_padding_var = tk.IntVar(value=3)
        
        self.case_enabled_var = tk.BooleanVar()
        self.case_type_var = tk.StringVar(value="lower")
        
        # Variables de padding numérico
        self.padding_enabled_var = tk.BooleanVar()
        self.padding_length_var = tk.IntVar(value=6)
        self.remove_padding_enabled_var = tk.BooleanVar()
        
        # Variables de plantillas
        self.template_var = tk.StringVar(value="")
        
        # Variables de estadísticas
        self.total_files_var = tk.StringVar(value="0")
        self.valid_files_var = tk.StringVar(value="0")
        self.conflicts_var = tk.StringVar(value="0")
    
    def create_tab(self):
        """Crea la pestaña de renombrado."""
        # Frame principal
        self.rename_frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.rename_frame, text="📝 Renombrar")
        
        # Crear secciones
        self.create_file_selection_section()
        self.create_operations_section()
        self.create_preview_section()
        self.create_control_section()
    
    def create_file_selection_section(self):
        """Crea la sección de selección de archivos."""
        # Frame para selección de archivos
        files_frame = ttk.LabelFrame(self.rename_frame, text="📁 Selección de Archivos", padding=10)
        files_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Carpeta origen
        ttk.Label(files_frame, text="Carpeta con archivos a renombrar:").grid(row=0, column=0, sticky=tk.W, pady=2)
        source_entry = ttk.Entry(files_frame, textvariable=self.source_folder_var, width=50)
        source_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
        ttk.Button(files_frame, text="🔍 Examinar", 
                  command=self.browse_source_folder).grid(row=0, column=2, padx=5, pady=2)
        
        # BOTONES PRINCIPALES MOVIDOS AQUÍ PARA MAYOR VISIBILIDAD
        main_buttons_frame = ttk.Frame(files_frame)
        main_buttons_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(10, 5))
        
        self.rename_button = ttk.Button(main_buttons_frame, text="🚀 Aplicar Renombrado", 
                                      command=self.apply_rename, style='Accent.TButton')
        self.rename_button.pack(side=tk.LEFT, padx=5)
        
        self.dry_run_button = ttk.Button(main_buttons_frame, text="🧪 Simulación", 
                                       command=self.dry_run_rename)
        self.dry_run_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(main_buttons_frame, text="💾 Guardar Config", 
                  command=self.save_settings).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(main_buttons_frame, text="📋 Cargar Config", 
                  command=self.load_settings).pack(side=tk.LEFT, padx=5)
        
        # Opciones de selección
        options_subframe = ttk.Frame(files_frame)
        options_subframe.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        # Incluir subcarpetas
        ttk.Checkbutton(options_subframe, text="📂 Incluir subcarpetas", 
                       variable=self.include_subfolders_var,
                       command=self.on_folder_options_change).pack(side=tk.LEFT, padx=5)
        
        # Filtro de archivos
        ttk.Label(options_subframe, text="Filtro:").pack(side=tk.LEFT, padx=(20, 5))
        filter_presets = self.config_manager.config_data.get('file_filters_presets', {})
        filter_combo = ttk.Combobox(options_subframe, textvariable=self.file_filter_var,
                                  values=list(filter_presets.keys()), state="readonly", width=15)
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind('<<ComboboxSelected>>', self.on_folder_options_change)
        
        # Botón cargar archivos
        ttk.Button(options_subframe, text="📋 Cargar Archivos", 
                  command=self.load_files).pack(side=tk.RIGHT, padx=5)
        
        # Estadísticas de archivos
        stats_subframe = ttk.Frame(files_frame)
        stats_subframe.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        ttk.Label(stats_subframe, text="Total:").pack(side=tk.LEFT)
        ttk.Label(stats_subframe, textvariable=self.total_files_var, 
                 style='Success.TLabel').pack(side=tk.LEFT, padx=(2, 10))
        
        ttk.Label(stats_subframe, text="Válidos:").pack(side=tk.LEFT)
        ttk.Label(stats_subframe, textvariable=self.valid_files_var, 
                 style='Success.TLabel').pack(side=tk.LEFT, padx=(2, 10))
        
        ttk.Label(stats_subframe, text="Conflictos:").pack(side=tk.LEFT)
        ttk.Label(stats_subframe, textvariable=self.conflicts_var, 
                 style='Error.TLabel').pack(side=tk.LEFT, padx=(2, 10))
        
        # Barra de progreso compacta y estado
        progress_status_frame = ttk.Frame(files_frame)
        progress_status_frame.grid(row=4, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_status_frame, variable=self.progress_var, 
                                          maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 2))
        
        self.status_label = ttk.Label(progress_status_frame, text="Listo para renombrar archivos", 
                                     font=('TkDefaultFont', 8))
        self.status_label.pack()
        
        files_frame.columnconfigure(1, weight=1)
    
    def create_operations_section(self):
        """Crea la sección de operaciones de renombrado."""
        # Frame principal de operaciones
        ops_main_frame = ttk.LabelFrame(self.rename_frame, text="⚙️ Operaciones de Renombrado", padding=10)
        ops_main_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Frame para plantillas
        template_frame = ttk.Frame(ops_main_frame)
        template_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(template_frame, text="📋 Plantilla:").pack(side=tk.LEFT)
        templates = list(RenameTemplates.get_all_templates().keys())
        template_combo = ttk.Combobox(template_frame, textvariable=self.template_var,
                                    values=[""] + templates, state="readonly", width=20)
        template_combo.pack(side=tk.LEFT, padx=5)
        template_combo.bind('<<ComboboxSelected>>', self.on_template_change)
        
        ttk.Button(template_frame, text="🔄 Aplicar Plantilla", 
                  command=self.apply_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(template_frame, text="🧹 Limpiar Todo", 
                  command=self.clear_all_operations).pack(side=tk.LEFT, padx=5)
        
        # Notebook para operaciones
        self.ops_notebook = ttk.Notebook(ops_main_frame)
        self.ops_notebook.pack(fill=tk.X, pady=5)
        
        # Crear pestañas de operaciones
        self.create_basic_operations_tab()
        self.create_advanced_operations_tab()
        self.create_numbering_tab()
    
    def create_basic_operations_tab(self):
        """Crea la pestaña de operaciones básicas."""
        basic_frame = ttk.Frame(self.ops_notebook)
        self.ops_notebook.add(basic_frame, text="Básicas")
        
        # Prefijo
        prefix_frame = ttk.LabelFrame(basic_frame, text="Agregar Prefijo", padding=5)
        prefix_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Checkbutton(prefix_frame, text="Activar", 
                       variable=self.prefix_enabled_var,
                       command=self.update_preview).pack(side=tk.LEFT)
        ttk.Label(prefix_frame, text="Prefijo:").pack(side=tk.LEFT, padx=(10, 5))
        prefix_entry = ttk.Entry(prefix_frame, textvariable=self.prefix_value_var, width=20)
        prefix_entry.pack(side=tk.LEFT, padx=5)
        prefix_entry.bind('<KeyRelease>', lambda e: self.update_preview())
        
        # Sufijo
        suffix_frame = ttk.LabelFrame(basic_frame, text="Agregar Sufijo", padding=5)
        suffix_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Checkbutton(suffix_frame, text="Activar", 
                       variable=self.suffix_enabled_var,
                       command=self.update_preview).pack(side=tk.LEFT)
        ttk.Label(suffix_frame, text="Sufijo:").pack(side=tk.LEFT, padx=(10, 5))
        suffix_entry = ttk.Entry(suffix_frame, textvariable=self.suffix_value_var, width=20)
        suffix_entry.pack(side=tk.LEFT, padx=5)
        suffix_entry.bind('<KeyRelease>', lambda e: self.update_preview())
        
        # Reemplazar
        replace_frame = ttk.LabelFrame(basic_frame, text="Reemplazar Texto", padding=5)
        replace_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Checkbutton(replace_frame, text="Activar", 
                       variable=self.replace_enabled_var,
                       command=self.update_preview).pack(side=tk.LEFT)
        
        replace_subframe = ttk.Frame(replace_frame)
        replace_subframe.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(replace_subframe, text="Buscar:").grid(row=0, column=0, sticky=tk.W)
        replace_old_entry = ttk.Entry(replace_subframe, textvariable=self.replace_old_var, width=15)
        replace_old_entry.grid(row=0, column=1, padx=2)
        replace_old_entry.bind('<KeyRelease>', lambda e: self.update_preview())
        
        ttk.Label(replace_subframe, text="Reemplazar:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        replace_new_entry = ttk.Entry(replace_subframe, textvariable=self.replace_new_var, width=15)
        replace_new_entry.grid(row=0, column=3, padx=2)
        replace_new_entry.bind('<KeyRelease>', lambda e: self.update_preview())
        
        # Eliminar
        remove_frame = ttk.LabelFrame(basic_frame, text="Eliminar Texto", padding=5)
        remove_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Checkbutton(remove_frame, text="Activar", 
                       variable=self.remove_enabled_var,
                       command=self.update_preview).pack(side=tk.LEFT)
        ttk.Label(remove_frame, text="Eliminar:").pack(side=tk.LEFT, padx=(10, 5))
        remove_entry = ttk.Entry(remove_frame, textvariable=self.remove_value_var, width=20)
        remove_entry.pack(side=tk.LEFT, padx=5)
        remove_entry.bind('<KeyRelease>', lambda e: self.update_preview())
    
    def create_advanced_operations_tab(self):
        """Crea la pestaña de operaciones avanzadas."""
        advanced_frame = ttk.Frame(self.ops_notebook)
        self.ops_notebook.add(advanced_frame, text="Avanzadas")
        
        # Cambio de mayúsculas/minúsculas
        case_frame = ttk.LabelFrame(advanced_frame, text="Cambiar Mayúsculas/Minúsculas", padding=5)
        case_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Checkbutton(case_frame, text="Activar", 
                       variable=self.case_enabled_var,
                       command=self.update_preview).pack(side=tk.LEFT)
        
        ttk.Label(case_frame, text="Tipo:").pack(side=tk.LEFT, padx=(10, 5))
        case_options = ["lower", "upper", "title", "sentence"]
        case_combo = ttk.Combobox(case_frame, textvariable=self.case_type_var,
                                values=case_options, state="readonly", width=15)
        case_combo.pack(side=tk.LEFT, padx=5)
        case_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        # Control de Ceros Numéricos
        zeros_frame = ttk.LabelFrame(advanced_frame, text="Control de Ceros Numéricos", padding=5)
        zeros_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Agregar ceros (padding)
        add_zeros_frame = ttk.Frame(zeros_frame)
        add_zeros_frame.pack(fill=tk.X, pady=2)
        
        ttk.Checkbutton(add_zeros_frame, text="✅ Agregar ceros", 
                       variable=self.padding_enabled_var,
                       command=self.update_preview).pack(side=tk.LEFT)
        
        ttk.Label(add_zeros_frame, text="Longitud total:").pack(side=tk.LEFT, padx=(10, 5))
        padding_spinbox = ttk.Spinbox(add_zeros_frame, textvariable=self.padding_length_var,
                                    from_=2, to=10, width=8, command=self.update_preview)
        padding_spinbox.pack(side=tk.LEFT, padx=5)
        padding_spinbox.bind('<KeyRelease>', lambda e: self.update_preview())
        
        ttk.Label(add_zeros_frame, text="Ej: RIPS_M7738.json → RIPS_M007738.json", 
                 style='Subtitle.TLabel').pack(side=tk.LEFT, padx=(15, 0))
        
        # Quitar ceros
        remove_zeros_frame = ttk.Frame(zeros_frame)
        remove_zeros_frame.pack(fill=tk.X, pady=2)
        
        ttk.Checkbutton(remove_zeros_frame, text="❌ Quitar ceros", 
                       variable=self.remove_padding_enabled_var,
                       command=self.update_preview).pack(side=tk.LEFT)
        
        ttk.Label(remove_zeros_frame, text="Ej: RIPS_M007738.json → RIPS_M7738.json", 
                 style='Subtitle.TLabel').pack(side=tk.LEFT, padx=(15, 0))
        
        # Operaciones de texto
        text_ops_frame = ttk.LabelFrame(advanced_frame, text="Operaciones de Texto", padding=5)
        text_ops_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(text_ops_frame, text="🔤 Eliminar Acentos", 
                  command=self.remove_accents).pack(side=tk.LEFT, padx=2)
        ttk.Button(text_ops_frame, text="🐍 Snake_case", 
                  command=self.to_snake_case).pack(side=tk.LEFT, padx=2)
        ttk.Button(text_ops_frame, text="🔢 Sin Números", 
                  command=self.remove_numbers).pack(side=tk.LEFT, padx=2)
        ttk.Button(text_ops_frame, text="✨ Limpiar", 
                  command=self.sanitize_names).pack(side=tk.LEFT, padx=2)
    
    def create_numbering_tab(self):
        """Crea la pestaña de numeración."""
        numbering_frame = ttk.Frame(self.ops_notebook)
        self.ops_notebook.add(numbering_frame, text="Numeración")
        
        # Numeración automática
        auto_num_frame = ttk.LabelFrame(numbering_frame, text="Numeración Automática", padding=5)
        auto_num_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Checkbutton(auto_num_frame, text="Activar numeración", 
                       variable=self.numbering_enabled_var,
                       command=self.update_preview).pack(anchor=tk.W, pady=2)
        
        # Configuración de numeración
        num_config_frame = ttk.Frame(auto_num_frame)
        num_config_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(num_config_frame, text="Inicio:").grid(row=0, column=0, sticky=tk.W)
        start_spinbox = ttk.Spinbox(num_config_frame, textvariable=self.numbering_start_var,
                                  from_=1, to=9999, width=10, command=self.update_preview)
        start_spinbox.grid(row=0, column=1, padx=5)
        start_spinbox.bind('<KeyRelease>', lambda e: self.update_preview())
        
        ttk.Label(num_config_frame, text="Ceros:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        padding_spinbox = ttk.Spinbox(num_config_frame, textvariable=self.numbering_padding_var,
                                    from_=1, to=10, width=10, command=self.update_preview)
        padding_spinbox.grid(row=0, column=3, padx=5)
        padding_spinbox.bind('<KeyRelease>', lambda e: self.update_preview())
        
        # Vista previa de numeración
        preview_num_frame = ttk.Frame(auto_num_frame)
        preview_num_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(preview_num_frame, text="Vista previa:").pack(side=tk.LEFT)
        self.numbering_preview_label = ttk.Label(preview_num_frame, text="001_archivo.ext", 
                                               style='Subtitle.TLabel')
        self.numbering_preview_label.pack(side=tk.LEFT, padx=10)
    
    def create_preview_section(self):
        """Crea la sección de vista previa."""
        # Frame para vista previa
        preview_frame = ttk.LabelFrame(self.rename_frame, text="👁️ Vista Previa", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Controles de vista previa
        preview_controls = ttk.Frame(preview_frame)
        preview_controls.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(preview_controls, text="🔄 Actualizar Vista Previa", 
                  command=self.update_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(preview_controls, text="🔍 Verificar Conflictos", 
                  command=self.check_conflicts).pack(side=tk.LEFT, padx=5)
        
        # Treeview para vista previa
        preview_tree_frame = ttk.Frame(preview_frame)
        preview_tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configurar Treeview
        columns = ('original', 'new', 'status', 'size')
        self.preview_tree = ttk.Treeview(preview_tree_frame, columns=columns, show='headings', height=12)
        
        # Configurar columnas
        self.preview_tree.heading('original', text='Nombre Original')
        self.preview_tree.heading('new', text='Nuevo Nombre')
        self.preview_tree.heading('status', text='Estado')
        self.preview_tree.heading('size', text='Tamaño')
        
        self.preview_tree.column('original', width=200)
        self.preview_tree.column('new', width=200)
        self.preview_tree.column('status', width=100)
        self.preview_tree.column('size', width=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(preview_tree_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        h_scrollbar = ttk.Scrollbar(preview_tree_frame, orient=tk.HORIZONTAL, command=self.preview_tree.xview)
        self.preview_tree.config(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Empaquetar Treeview y scrollbars
        self.preview_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        preview_tree_frame.grid_rowconfigure(0, weight=1)
        preview_tree_frame.grid_columnconfigure(0, weight=1)
        
        # Configurar tags para colores
        self.preview_tree.tag_configure('success', foreground='#4CAF50')
        self.preview_tree.tag_configure('conflict', foreground='#F44336')
        self.preview_tree.tag_configure('warning', foreground='#FF9800')
    
    def create_control_section(self):
        """Sección de control integrada en selección de archivos - No se necesita sección separada."""
        # Los controles ahora están integrados en la sección de selección de archivos
        # para mejor visibilidad en ventanas minimizadas
        pass
    
    # Métodos de eventos y funcionalidad
    def browse_source_folder(self):
        """Abre el diálogo para seleccionar carpeta origen."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta con archivos a renombrar")
        if folder:
            self.source_folder_var.set(folder)
            self.load_files()
    
    def on_folder_options_change(self, event=None):
        """Maneja cambios en las opciones de carpeta."""
        if self.source_folder_var.get():
            self.load_files()
    
    def load_files(self):
        """Carga archivos desde la carpeta seleccionada."""
        folder = self.source_folder_var.get()
        if not folder or not os.path.exists(folder):
            self.update_file_stats(0, 0, 0)
            return
        
        try:
            # Obtener filtros
            filter_preset = self.file_filter_var.get()
            filter_presets = self.config_manager.config_data.get('file_filters_presets', {})
            file_filters = filter_presets.get(filter_preset, ['*'])
            
            # Cargar archivos
            count = self.renamer.load_files_from_folder(
                folder, 
                self.include_subfolders_var.get(), 
                file_filters
            )
            
            self.update_file_stats(count, count, 0)
            self.update_preview()
            
            self.logger.log_operation('INFO', f"Cargados {count} archivos desde {folder}")
            
        except Exception as e:
            self.logger.log_operation('ERROR', f"Error cargando archivos: {str(e)}")
            messagebox.showerror("Error", f"Error cargando archivos: {str(e)}")
    
    def update_file_stats(self, total: int, valid: int, conflicts: int):
        """Actualiza las estadísticas de archivos."""
        self.total_files_var.set(str(total))
        self.valid_files_var.set(str(valid))
        self.conflicts_var.set(str(conflicts))
    
    def on_template_change(self, event=None):
        """Maneja el cambio de plantilla."""
        template_name = self.template_var.get()
        if template_name:
            template = RenameTemplates.get_template(template_name)
            if template:
                # Mostrar descripción de la plantilla
                self.status_label.config(text=f"Plantilla: {template['description']}")
    
    def apply_template(self):
        """Aplica la plantilla seleccionada."""
        template_name = self.template_var.get()
        if not template_name:
            return
        
        template = RenameTemplates.get_template(template_name)
        if not template:
            return
        
        # Limpiar operaciones actuales
        self.clear_all_operations()
        
        # Aplicar operaciones de la plantilla
        for op_config in template['operations']:
            if op_config['type'] == 'prefix':
                self.prefix_enabled_var.set(op_config['enabled'])
                self.prefix_value_var.set(op_config.get('value', ''))
            elif op_config['type'] == 'suffix':
                self.suffix_enabled_var.set(op_config['enabled'])
                self.suffix_value_var.set(op_config.get('value', ''))
            elif op_config['type'] == 'replace':
                self.replace_enabled_var.set(op_config['enabled'])
                self.replace_old_var.set(op_config.get('old', ''))
                self.replace_new_var.set(op_config.get('new', ''))
            elif op_config['type'] == 'numbering':
                self.numbering_enabled_var.set(op_config['enabled'])
                self.numbering_start_var.set(op_config.get('start', 1))
                self.numbering_padding_var.set(op_config.get('padding', 3))
            elif op_config['type'] == 'case':
                self.case_enabled_var.set(op_config['enabled'])
                self.case_type_var.set(op_config.get('case_type', 'lower'))
        
        self.update_preview()
        self.logger.log_operation('INFO', f"Plantilla '{template_name}' aplicada")
    
    def clear_all_operations(self):
        """Limpia todas las operaciones."""
        # Desactivar todas las operaciones
        self.prefix_enabled_var.set(False)
        self.suffix_enabled_var.set(False)
        self.replace_enabled_var.set(False)
        self.remove_enabled_var.set(False)
        self.numbering_enabled_var.set(False)
        self.case_enabled_var.set(False)
        self.padding_enabled_var.set(False)
        self.remove_padding_enabled_var.set(False)
        
        # Limpiar valores
        self.prefix_value_var.set("")
        self.suffix_value_var.set("")
        self.replace_old_var.set("")
        self.replace_new_var.set("")
        self.remove_value_var.set("")
        
        # Resetear numeración
        self.numbering_start_var.set(1)
        self.numbering_padding_var.set(3)
        
        # Resetear caso
        self.case_type_var.set("lower")
        
        # Resetear padding numérico
        self.padding_length_var.set(6)
        
        self.update_preview()
    
    def update_operations(self):
        """Actualiza las operaciones del renombrador."""
        self.renamer.operations.clear()
        
        # Agregar operaciones habilitadas
        if self.prefix_enabled_var.get() and self.prefix_value_var.get():
            op = RenameOperation(
                operation_type='prefix',
                enabled=True,
                value=self.prefix_value_var.get(),
                position=len(self.renamer.operations)
            )
            self.renamer.add_operation(op)
        
        if self.suffix_enabled_var.get() and self.suffix_value_var.get():
            op = RenameOperation(
                operation_type='suffix',
                enabled=True,
                value=self.suffix_value_var.get(),
                position=len(self.renamer.operations)
            )
            self.renamer.add_operation(op)
        
        if self.replace_enabled_var.get() and self.replace_old_var.get():
            op = RenameOperation(
                operation_type='replace',
                enabled=True,
                old_value=self.replace_old_var.get(),
                value=self.replace_new_var.get(),
                position=len(self.renamer.operations)
            )
            self.renamer.add_operation(op)
        
        if self.remove_enabled_var.get() and self.remove_value_var.get():
            op = RenameOperation(
                operation_type='remove',
                enabled=True,
                value=self.remove_value_var.get(),
                position=len(self.renamer.operations)
            )
            self.renamer.add_operation(op)
        
        if self.numbering_enabled_var.get():
            op = RenameOperation(
                operation_type='numbering',
                enabled=True,
                start_number=self.numbering_start_var.get(),
                padding=self.numbering_padding_var.get(),
                position=len(self.renamer.operations)
            )
            self.renamer.add_operation(op)
        
        if self.case_enabled_var.get():
            op = RenameOperation(
                operation_type='case',
                enabled=True,
                case_type=self.case_type_var.get(),
                position=len(self.renamer.operations)
            )
            self.renamer.add_operation(op)
        
        if self.padding_enabled_var.get():
            op = RenameOperation(
                operation_type='padding',
                enabled=True,
                padding_length=self.padding_length_var.get(),
                position=len(self.renamer.operations)
            )
            self.renamer.add_operation(op)
        
        if self.remove_padding_enabled_var.get():
            op = RenameOperation(
                operation_type='remove_padding',
                enabled=True,
                position=len(self.renamer.operations)
            )
            self.renamer.add_operation(op)
    
    def update_preview(self):
        """Actualiza la vista previa de renombrado."""
        if not self.renamer.files:
            self.clear_preview()
            return
        
        try:
            # Actualizar operaciones
            self.update_operations()
            
            # Generar vista previa
            self.current_preview = self.renamer.generate_preview()
            
            # Actualizar vista previa de numeración
            if self.numbering_enabled_var.get():
                start = self.numbering_start_var.get()
                padding = self.numbering_padding_var.get()
                example = str(start).zfill(padding) + "_archivo.ext"
                self.numbering_preview_label.config(text=example)
            
            # Actualizar Treeview
            self.update_preview_tree()
            
            # Verificar conflictos
            conflicts = self.renamer.check_conflicts()
            total_conflicts = len(conflicts['duplicates']) + len(conflicts['existing_files']) + len(conflicts['invalid_names'])
            
            # Actualizar estadísticas
            valid_files = len([p for p in self.current_preview if not p.has_conflict])
            self.update_file_stats(len(self.current_preview), valid_files, total_conflicts)
            
        except Exception as e:
            self.logger.log_operation('ERROR', f"Error actualizando vista previa: {str(e)}")
    
    def update_preview_tree(self):
        """Actualiza el Treeview de vista previa."""
        # Limpiar árbol
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        # Agregar elementos
        for preview in self.current_preview:
            # Determinar estado y tag
            if preview.has_conflict:
                status = "⚠️ Conflicto"
                tag = 'conflict'
            elif preview.original_name == preview.new_name:
                status = "➖ Sin cambios"
                tag = 'warning'
            else:
                status = "✅ Listo"
                tag = 'success'
            
            # Formatear tamaño
            size_str = FileUtils.format_file_size(preview.size) if preview.size else "-"
            
            # Insertar elemento
            self.preview_tree.insert('', 'end', values=(
                preview.original_name,
                preview.new_name,
                status,
                size_str
            ), tags=(tag,))
    
    def clear_preview(self):
        """Limpia la vista previa."""
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        self.current_preview.clear()
    
    def check_conflicts(self):
        """Verifica y muestra conflictos."""
        if not self.current_preview:
            self.update_preview()
        
        conflicts = self.renamer.check_conflicts()
        
        # Crear mensaje de conflictos
        messages = []
        if conflicts['duplicates']:
            messages.append(f"Nombres duplicados: {len(conflicts['duplicates'])}")
        if conflicts['existing_files']:
            messages.append(f"Archivos existentes: {len(conflicts['existing_files'])}")
        if conflicts['invalid_names']:
            messages.append(f"Nombres inválidos: {len(conflicts['invalid_names'])}")
        
        if messages:
            messagebox.showwarning("Conflictos Detectados", "\n".join(messages))
        else:
            messagebox.showinfo("Sin Conflictos", "No se detectaron conflictos en el renombrado.")
    
    def apply_rename(self):
        """Aplica el renombrado a los archivos."""
        if not self.current_preview:
            messagebox.showwarning("Advertencia", "No hay archivos para renombrar.")
            return
        
        # Verificar conflictos
        conflicts = self.renamer.check_conflicts()
        total_conflicts = len(conflicts['duplicates']) + len(conflicts['existing_files']) + len(conflicts['invalid_names'])
        
        if total_conflicts > 0:
            if not messagebox.askyesno("Conflictos Detectados", 
                                     f"Se detectaron {total_conflicts} conflictos. ¿Continuar de todos modos?"):
                return
        
        # Confirmar operación
        valid_files = len([p for p in self.current_preview if not p.has_conflict and p.original_name != p.new_name])
        if not messagebox.askyesno("Confirmar Renombrado", 
                                 f"¿Renombrar {valid_files} archivos?"):
            return
        
        # Ejecutar renombrado en hilo separado
        self.is_processing = True
        self.rename_button.config(state='disabled')
        self.status_label.config(text="Renombrando archivos...")
        
        def rename_thread():
            try:
                results = self.renamer.apply_rename(dry_run=False)
                
                # Actualizar UI en hilo principal
                self.rename_frame.after(0, lambda: self.on_rename_complete(results))
                
            except Exception as e:
                self.rename_frame.after(0, lambda: self.on_rename_error(str(e)))
        
        self.processing_thread = threading.Thread(target=rename_thread, daemon=True)
        self.processing_thread.start()
    
    def dry_run_rename(self):
        """Ejecuta una simulación del renombrado."""
        if not self.current_preview:
            messagebox.showwarning("Advertencia", "No hay archivos para simular.")
            return
        
        try:
            results = self.renamer.apply_rename(dry_run=True)
            
            # Mostrar resultados
            message = f"Simulación completada:\n\n"
            message += f"Exitosos: {len(results['success'])}\n"
            message += f"Errores: {len(results['errors'])}\n"
            message += f"Omitidos: {len(results['skipped'])}"
            
            messagebox.showinfo("Simulación Completada", message)
            
        except Exception as e:
            messagebox.showerror("Error en Simulación", f"Error: {str(e)}")
    
    def on_rename_complete(self, results):
        """Maneja la finalización del renombrado."""
        self.is_processing = False
        self.rename_button.config(state='normal')
        
        # Mostrar resultados
        message = f"Renombrado completado:\n\n"
        message += f"Exitosos: {len(results['success'])}\n"
        message += f"Errores: {len(results['errors'])}\n"
        message += f"Omitidos: {len(results['skipped'])}"
        
        if results['errors']:
            messagebox.showwarning("Renombrado Completado con Errores", message)
        else:
            messagebox.showinfo("Renombrado Completado", message)
        
        # Recargar archivos para actualizar vista
        self.load_files()
        
        self.status_label.config(text="Renombrado completado")
        self.logger.log_operation('INFO', f"Renombrado completado: {len(results['success'])} exitosos")
    
    def on_rename_error(self, error_msg):
        """Maneja errores en el renombrado."""
        self.is_processing = False
        self.rename_button.config(state='normal')
        self.status_label.config(text="Error en renombrado")
        
        messagebox.showerror("Error", f"Error durante el renombrado: {error_msg}")
        self.logger.log_operation('ERROR', f"Error en renombrado: {error_msg}")
    
    # Operaciones de texto avanzadas
    def remove_accents(self):
        """Elimina acentos de los nombres de archivo."""
        self._apply_text_operation(TextProcessor.remove_accents)
    
    def to_snake_case(self):
        """Convierte nombres a snake_case."""
        self._apply_text_operation(TextProcessor.to_snake_case)
    
    def remove_numbers(self):
        """Elimina números de los nombres."""
        self._apply_text_operation(TextProcessor.remove_numbers)
    
    def sanitize_names(self):
        """Limpia nombres de archivo."""
        self._apply_text_operation(FileNameValidator.sanitize_filename)
    
    def _apply_text_operation(self, operation_func):
        """Aplica una operación de texto a los archivos cargados."""
        if not self.renamer.files:
            messagebox.showwarning("Advertencia", "No hay archivos cargados.")
            return
        
        try:
            # Aplicar operación a cada archivo
            modified_files = []
            for file_path in self.renamer.files:
                path = Path(file_path)
                name, ext = os.path.splitext(path.name)
                new_name = operation_func(name) + ext
                new_path = path.parent / new_name
                modified_files.append(str(new_path))
            
            # Actualizar lista de archivos
            self.renamer.files = modified_files
            self.update_preview()
            
            self.logger.log_operation('INFO', f"Operación de texto aplicada a {len(modified_files)} archivos")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error aplicando operación: {str(e)}")
    
    def save_settings(self):
        """Guarda la configuración actual."""
        try:
            settings = {
                'source_folder': self.source_folder_var.get(),
                'include_subfolders': self.include_subfolders_var.get(),
                'file_filter': self.file_filter_var.get(),
                'operations': {
                    'prefix': {
                        'enabled': self.prefix_enabled_var.get(),
                        'value': self.prefix_value_var.get()
                    },
                    'suffix': {
                        'enabled': self.suffix_enabled_var.get(),
                        'value': self.suffix_value_var.get()
                    },
                    'replace': {
                        'enabled': self.replace_enabled_var.get(),
                        'old': self.replace_old_var.get(),
                        'new': self.replace_new_var.get()
                    },
                    'remove': {
                        'enabled': self.remove_enabled_var.get(),
                        'value': self.remove_value_var.get()
                    },
                    'numbering': {
                        'enabled': self.numbering_enabled_var.get(),
                        'start': self.numbering_start_var.get(),
                        'padding': self.numbering_padding_var.get()
                    },
                    'case': {
                        'enabled': self.case_enabled_var.get(),
                        'type': self.case_type_var.get()
                    },
                    'padding': {
                        'enabled': self.padding_enabled_var.get(),
                        'length': self.padding_length_var.get()
                    },
                    'remove_padding': {
                        'enabled': self.remove_padding_enabled_var.get()
                    }
                }
            }
            
            # Guardar en configuración
            if 'renamer_settings' not in self.config_manager.config_data:
                self.config_manager.config_data['renamer_settings'] = {}
            
            self.config_manager.config_data['renamer_settings']['last_config'] = settings
            self.config_manager.save_config()
            
            messagebox.showinfo("Configuración Guardada", "La configuración se guardó correctamente.")
            self.logger.log_operation('INFO', "Configuración de renombrado guardada")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando configuración: {str(e)}")
    
    def load_settings(self):
        """Carga la configuración guardada."""
        try:
            renamer_settings = self.config_manager.config_data.get('renamer_settings', {})
            last_config = renamer_settings.get('last_config', {})
            
            if not last_config:
                return
            
            # Cargar configuración básica
            self.source_folder_var.set(last_config.get('source_folder', ''))
            self.include_subfolders_var.set(last_config.get('include_subfolders', False))
            self.file_filter_var.set(last_config.get('file_filter', 'todos'))
            
            # Cargar operaciones
            operations = last_config.get('operations', {})
            
            # Prefijo
            prefix_op = operations.get('prefix', {})
            self.prefix_enabled_var.set(prefix_op.get('enabled', False))
            self.prefix_value_var.set(prefix_op.get('value', ''))
            
            # Sufijo
            suffix_op = operations.get('suffix', {})
            self.suffix_enabled_var.set(suffix_op.get('enabled', False))
            self.suffix_value_var.set(suffix_op.get('value', ''))
            
            # Reemplazar
            replace_op = operations.get('replace', {})
            self.replace_enabled_var.set(replace_op.get('enabled', False))
            self.replace_old_var.set(replace_op.get('old', ''))
            self.replace_new_var.set(replace_op.get('new', ''))
            
            # Eliminar
            remove_op = operations.get('remove', {})
            self.remove_enabled_var.set(remove_op.get('enabled', False))
            self.remove_value_var.set(remove_op.get('value', ''))
            
            # Numeración
            numbering_op = operations.get('numbering', {})
            self.numbering_enabled_var.set(numbering_op.get('enabled', False))
            self.numbering_start_var.set(numbering_op.get('start', 1))
            self.numbering_padding_var.set(numbering_op.get('padding', 3))
            
            # Caso
            case_op = operations.get('case', {})
            self.case_enabled_var.set(case_op.get('enabled', False))
            self.case_type_var.set(case_op.get('type', 'lower'))
            
            # Padding numérico
            padding_op = operations.get('padding', {})
            self.padding_enabled_var.set(padding_op.get('enabled', False))
            self.padding_length_var.set(padding_op.get('length', 6))
            
            # Remove padding
            remove_padding_op = operations.get('remove_padding', {})
            self.remove_padding_enabled_var.set(remove_padding_op.get('enabled', False))
            
            # Cargar archivos si hay carpeta
            if self.source_folder_var.get():
                self.load_files()
            
            self.logger.log_operation('INFO', "Configuración de renombrado cargada")
            
        except Exception as e:
            self.logger.log_operation('ERROR', f"Error cargando configuración: {str(e)}")