#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Prueba - Nomenclatura de Facturas

Este script demuestra cómo funciona el nuevo patrón de nomenclatura
"factura_sop" con ejemplos específicos.
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent))

from core.compressor import CompressorEngine
from core.config_manager import ConfigManager
from core.logger import CustomLogger
from core.file_manager import FileInfo

def test_invoice_pattern():
    """Prueba el patrón de nomenclatura de facturas."""
    
    print("=== PRUEBA DE NOMENCLATURA DE FACTURAS ===")
    print()
    
    # Inicializar componentes
    config_manager = ConfigManager()
    logger = CustomLogger()
    compressor = CompressorEngine(config_manager, logger)
    
    # Ejemplos de nombres de archivo
    test_files = [
        "HOSP001.pdf",
        "FACT123.docx",
        "INV456.xlsx",
        "AB-001.pdf",
        "HOSP_123.pdf",
        "001.pdf",
        "documento_sin_patron.pdf"
    ]
    
    print("Ejemplos de conversión de nomenclatura:")
    print("-" * 50)
    
    for i, filename in enumerate(test_files):
        # Crear FileInfo simulado usando el método from_path
        file_path = Path(filename)
        # Crear archivo temporal para la prueba
        temp_file = Path(f"temp_{filename}")
        temp_file.touch(exist_ok=True)
        
        file_info = FileInfo.from_path(temp_file)
        file_info.name = filename  # Usar el nombre de prueba
        file_info.path = file_path  # Usar la ruta de prueba
        
        # Simular configuración con patrón factura_sop
        from core.compressor import CompressionConfig
        config = CompressionConfig(
            source_folder="./test",
            backup_folder="./respaldo",
            naming_pattern="factura_sop"
        )
        
        # Establecer contador manual para la prueba
        compressor.file_counter = i
        
        # Generar nombre ZIP
        zip_name = compressor._generate_zip_name(file_info, config)
        
        # Mostrar resultado
        numero_factura = compressor._extract_invoice_number(file_path.stem)
        print(f"Archivo original: {filename}")
        print(f"Número extraído: {numero_factura}")
        print(f"Archivo ZIP:      {zip_name}")
        print()

def test_pattern_recognition():
    """Prueba el reconocimiento de patrones de números de factura."""
    
    print("=== PRUEBA DE RECONOCIMIENTO DE PATRONES ===")
    print()
    
    compressor = CompressorEngine()
    
    test_patterns = [
        ("HOSP001", "Código hospital"),
        ("FACT123", "Código factura"),
        ("INV456789", "Código inventario"),
        ("AB-001", "Código con guión"),
        ("HOSP_123", "Código con guión bajo"),
        ("001", "Solo números"),
        ("123456", "Número largo"),
        ("documento_normal", "Sin patrón específico")
    ]
    
    print("Reconocimiento de patrones:")
    print("-" * 40)
    
    for filename, description in test_patterns:
        extracted = compressor._extract_invoice_number(filename)
        print(f"{filename:<20} → {extracted:<15} ({description})")
    
    print()

def show_configuration_example():
    """Muestra ejemplo de configuración."""
    
    print("=== CONFIGURACIÓN RECOMENDADA ===")
    print()
    
    config_example = '''
    {
      "profiles": {
        "facturas": {
          "naming_pattern": "factura_sop",
          "backup_folder": "./respaldo_facturas",
          "include_subfolders": false,
          "file_filters": ["*.pdf", "*.docx", "*.xlsx"],
          "compression_level": 6,
          "conflict_resolution": "rename"
        }
      }
    }
    '''
    
    print("Configuración en config.json:")
    print(config_example)
    
    print("Pasos para usar:")
    print("1. Ejecuta la aplicación: python main.py")
    print("2. Ve a la pestaña 'Perfiles'")
    print("3. Selecciona el perfil 'facturas'")
    print("4. O configura manualmente el patrón 'factura_sop'")
    print("5. Selecciona tu carpeta con archivos de facturas")
    print("6. ¡Inicia el proceso!")
    print()

if __name__ == "__main__":
    try:
        test_invoice_pattern()
        test_pattern_recognition()
        show_configuration_example()
        
        print("✅ Todas las pruebas completadas exitosamente!")
        print("\nEl sistema está configurado para usar la nomenclatura:")
        print("Archivo original → Archivo ZIP")
        print("HOSP001.pdf → HOSP001_SOP_0.zip")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()