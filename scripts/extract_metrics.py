#!/usr/bin/env python3
"""
Script para extrair métricas do output de treinamento e salvar em JSON.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path


def extract_metrics_from_output(output_file: str, commit_sha: str, branch: str) -> dict:
    """Extrai métricas do arquivo de output do treinamento."""
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            output = f.read()
    except FileNotFoundError:
        print(f"❌ Arquivo {output_file} não encontrado")
        return {}
    
    # Extrair métricas usando regex
    metrics_patterns = {
        'accuracy': r'Acurácia: ([\d.]+)',
        'precision': r'Precisão: ([\d.]+)', 
        'recall': r'Recall: ([\d.]+)',
        'f1_score': r'F1: ([\d.]+)',
        'roc_auc': r'ROC AUC: ([\d.]+)'
    }
    
    extracted_metrics = {}
    for metric_name, pattern in metrics_patterns.items():
        match = re.search(pattern, output)
        if match:
            extracted_metrics[metric_name] = float(match.group(1))
            print(f"✅ {metric_name}: {match.group(1)}")
        else:
            print(f"⚠️  {metric_name}: não encontrado")
            extracted_metrics[metric_name] = None
    
    # Extrair informações de shapes
    shapes_match = re.search(r'Shapes: X_train=\((\d+), (\d+)\)', output)
    if shapes_match:
        train_samples = int(shapes_match.group(1))
        features_count = int(shapes_match.group(2))
        print(f"✅ Training samples: {train_samples:,}")
        print(f"✅ Features count: {features_count}")
    else:
        print("⚠️  Training shapes: não encontrado")
        train_samples = None
        features_count = None
    
    # Montar objeto final de métricas
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'commit_sha': commit_sha,
        'branch': branch,
        'train_samples': train_samples,
        'features_count': features_count,
        **extracted_metrics
    }
    
    return metrics


def save_metrics(metrics: dict, output_file: str = 'metrics.json'):
    """Salva métricas em arquivo JSON."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        print(f"📊 Métricas salvas em {output_file}")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar métricas: {e}")
        return False


def main():
    """Função principal."""
    if len(sys.argv) < 4:
        print("Uso: python extract_metrics.py <training_output.txt> <commit_sha> <branch>")
        sys.exit(1)
    
    output_file = sys.argv[1]
    commit_sha = sys.argv[2]
    branch = sys.argv[3]
    
    print(f"🔍 Extraindo métricas de: {output_file}")
    print(f"📝 Commit: {commit_sha[:8]}")
    print(f"🌿 Branch: {branch}")
    
    metrics = extract_metrics_from_output(output_file, commit_sha, branch)
    
    if metrics and any(v is not None for v in metrics.values()):
        success = save_metrics(metrics)
        if success:
            print("✅ Extração de métricas concluída com sucesso!")
        else:
            sys.exit(1)
    else:
        print("❌ Nenhuma métrica foi extraída")
        sys.exit(1)


if __name__ == "__main__":
    main()