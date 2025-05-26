#!/usr/bin/env python3
"""
Script para verificar se os arquivos necessários para treinamento existem.
"""

import os
import sys
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """Verifica se um arquivo existe e mostra informações sobre ele."""
    path = Path(filepath)
    
    if path.exists():
        size = path.stat().st_size
        size_mb = size / (1024 * 1024)
        print(f"✅ {description}: {filepath}")
        print(f"   📦 Size: {size:,} bytes ({size_mb:.2f} MB)")
        return True
    else:
        print(f"❌ {description}: {filepath} (NOT FOUND)")
        return False


def check_directory_contents(directory: str, description: str):
    """Lista o conteúdo de um diretório."""
    path = Path(directory)
    
    print(f"\n📁 {description}: {directory}")
    
    if not path.exists():
        print("   ❌ Directory does not exist")
        return
    
    files = list(path.iterdir())
    if not files:
        print("   📭 Directory is empty")
        return
        
    print(f"   📊 Found {len(files)} items:")
    for file_path in sorted(files):
        if file_path.is_file():
            size = file_path.stat().st_size
            size_mb = size / (1024 * 1024)
            print(f"     📄 {file_path.name} ({size:,} bytes, {size_mb:.2f} MB)")
        else:
            print(f"     📁 {file_path.name}/ (directory)")


def main():
    """Função principal para verificar arquivos de treinamento."""
    
    print("🔍 Checking training files and directories...")
    
    # Arquivos essenciais para o treinamento
    required_files = [
        ("datathon_decision/data/processed/train_data.joblib", "Training data"),
        ("datathon_decision/data/processed/val_data.joblib", "Validation data"),
    ]
    
    # Arquivos opcionais mas importantes
    optional_files = [
        ("datathon_decision/models/preprocessor_objects.joblib", "Preprocessor"),
        ("datathon_decision/models/training_columns.joblib", "Training columns"),
        ("datathon_decision/models/random_forest_model.joblib", "Trained model"),
    ]
    
    print("\n" + "="*60)
    print("🎯 REQUIRED FILES FOR TRAINING")
    print("="*60)
    
    missing_required = []
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            missing_required.append(filepath)
    
    print("\n" + "="*60)
    print("📋 OPTIONAL/OUTPUT FILES")
    print("="*60)
    
    for filepath, description in optional_files:
        check_file_exists(filepath, description)
    
    # Verificar diretórios
    print("\n" + "="*60)
    print("📁 DIRECTORY CONTENTS")
    print("="*60)
    
    directories_to_check = [
        ("datathon_decision/data/raw", "Raw data directory"),
        ("datathon_decision/data/processed", "Processed data directory"),
        ("datathon_decision/models", "Models directory"),
    ]
    
    for directory, description in directories_to_check:
        check_directory_contents(directory, description)
    
    # Resumo final
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    if missing_required:
        print(f"❌ Missing {len(missing_required)} required files:")
        for filepath in missing_required:
            print(f"   - {filepath}")
        print("\n💡 Training will fail. Please run preprocessing first.")
        return 1
    else:
        print("✅ All required files are present!")
        print("🚀 Training can proceed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())