#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para las nuevas funciones de padding numérico
"""

from utils.rename_operations import NumberingHelper

def test_padding_functions():
    """Prueba las funciones de padding y remove_padding"""
    
    print("=== PRUEBAS DE FUNCIONES DE PADDING NUMÉRICO ===")
    print()
    
    # Casos de prueba
    test_cases = [
        "RIPS_M7738.json",
        "documento123.pdf",
        "IMG_45.jpg",
        "archivo_001_backup.zip",
        "test_12_final_34.txt",
        "sin_numeros.docx"
    ]
    
    print("1. PRUEBA: Agregar ceros (padding a 6 dígitos)")
    print("-" * 50)
    for filename in test_cases:
        result = NumberingHelper.pad_numbers(filename, 6)
        print(f"{filename:<25} → {result}")
    
    print("\n2. PRUEBA: Quitar ceros (remove_padding)")
    print("-" * 50)
    padded_cases = [
        "RIPS_M007738.json",
        "documento000123.pdf",
        "IMG_000045.jpg",
        "archivo_000001_backup.zip",
        "test_000012_final_000034.txt",
        "sin_numeros.docx"
    ]
    
    for filename in padded_cases:
        result = NumberingHelper.remove_padding(filename)
        print(f"{filename:<30} → {result}")
    
    print("\n3. PRUEBA: Ciclo completo (agregar y quitar ceros)")
    print("-" * 50)
    for filename in test_cases:
        # Agregar ceros
        with_padding = NumberingHelper.pad_numbers(filename, 6)
        # Quitar ceros
        without_padding = NumberingHelper.remove_padding(with_padding)
        print(f"Original: {filename}")
        print(f"Con ceros: {with_padding}")
        print(f"Sin ceros: {without_padding}")
        print(f"¿Igual al original? {'✅ SÍ' if filename == without_padding else '❌ NO'}")
        print()
    
    print("\n4. PRUEBA: Casos especiales")
    print("-" * 50)
    special_cases = [
        "archivo_0.txt",  # Cero simple
        "test_00000.pdf", # Muchos ceros
        "file_0001_0002.zip", # Múltiples números con ceros
        "123456789.txt", # Número muy largo
        "0.json" # Solo cero
    ]
    
    for filename in special_cases:
        padded = NumberingHelper.pad_numbers(filename, 4)
        unpadded = NumberingHelper.remove_padding(padded)
        print(f"Original: {filename}")
        print(f"Padding a 4: {padded}")
        print(f"Remove padding: {unpadded}")
        print()

if __name__ == "__main__":
    test_padding_functions()