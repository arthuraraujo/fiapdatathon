#!/usr/bin/env python3
"""
Script para gerar dashboard HTML com métricas do modelo.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def load_metrics(metrics_file: str = 'metrics.json') -> dict:
    """Carrega métricas do arquivo JSON."""
    try:
        with open(metrics_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  Arquivo {metrics_file} não encontrado")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON: {e}")
        return {}


def generate_dashboard_html(metrics: dict, commit_sha: str, branch: str, run_id: str, repo: str) -> str:
    """Gera HTML do dashboard."""
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    commit_short = commit_sha[:8] if commit_sha else 'unknown'
    
    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Model Metrics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
        }}
        .header h1 {{
            margin: 0;
            color: #2c3e50;
            font-size: 2.5em;
        }}
        .header .subtitle {{
            color: #7f8c8d;
            margin-top: 10px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .metric-card {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px; 
            border-radius: 15px; 
            text-align: center;
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            transition: transform 0.3s ease;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
        }}
        .metric-card h3 {{
            margin: 0 0 10px 0;
            font-size: 1em;
            opacity: 0.9;
        }}
        .metric-value {{ 
            font-size: 2.2em; 
            font-weight: bold; 
            margin: 0;
        }}
        .info-section {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }}
        .info-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .info-label {{
            font-weight: 600;
            color: #495057;
        }}
        .info-value {{
            color: #6c757d;
            font-family: 'Monaco', 'Menlo', monospace;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            margin: 5px;
        }}
        .status-high {{ background: #d4edda; color: #155724; }}
        .status-medium {{ background: #fff3cd; color: #856404; }}
        .status-low {{ background: #f8d7da; color: #721c24; }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            color: #6c757d;
        }}
        .link-button {{
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            margin: 5px;
            transition: background 0.3s ease;
        }}
        .link-button:hover {{
            background: #0056b3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Model Performance Dashboard</h1>
            <div class="subtitle">
                <strong>Datathon Decision ML Pipeline</strong><br>
                Last Updated: {current_time}
            </div>
        </div>
'''
    
    if metrics:
        # Cards de métricas principais
        html += '''
        <h2>📊 Current Model Performance</h2>
        <div class="metrics-grid">'''
        
        metric_configs = [
            ('accuracy', 'Accuracy', '%'),
            ('precision', 'Precision', '%'),
            ('recall', 'Recall', '%'),
            ('f1_score', 'F1 Score', '%'),
            ('roc_auc', 'ROC AUC', '')
        ]
        
        for key, label, unit in metric_configs:
            value = metrics.get(key)
            if value is not None:
                if unit == '%':
                    display_value = f"{value*100:.1f}%"
                else:
                    display_value = f"{value:.3f}"
                html += f'''
            <div class="metric-card">
                <h3>{label}</h3>
                <div class="metric-value">{display_value}</div>
            </div>'''
            
        html += '</div>'
        
        # Seção de informações
        html += f'''
        <div class="info-section">
            <h3>📈 Training Information</h3>
            <div class="info-grid">
                <div>
                    <div class="info-item">
                        <span class="info-label">Training Samples:</span>
                        <span class="info-value">{metrics.get('train_samples', 'N/A'):,}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Features Count:</span>
                        <span class="info-value">{metrics.get('features_count', 'N/A')}</span>
                    </div>
                </div>
                <div>
                    <div class="info-item">
                        <span class="info-label">Commit:</span>
                        <span class="info-value">{commit_short}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Branch:</span>
                        <span class="info-value">{branch}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Timestamp:</span>
                        <span class="info-value">{metrics.get('timestamp', 'N/A')}</span>
                    </div>
                </div>
            </div>
        </div>
        '''
        
        # Status badges
        accuracy = metrics.get('accuracy', 0)
        f1_score = metrics.get('f1_score', 0)
        
        html += '<div style="text-align: center; margin: 20px 0;">'
        
        if accuracy > 0.9:
            html += '<span class="status-badge status-high">🟢 High Accuracy</span>'
        elif accuracy > 0.8:
            html += '<span class="status-badge status-medium">🟡 Medium Accuracy</span>'
        else:
            html += '<span class="status-badge status-low">🔴 Low Accuracy</span>'
            
        if f1_score > 0.3:
            html += '<span class="status-badge status-high">🟢 Good F1 Score</span>'
        else:
            html += '<span class="status-badge status-medium">🟡 F1 Needs Improvement</span>'
            
        html += '</div>'
    
    else:
        html += '''
        <div class="info-section">
            <h3>⚠️ No Metrics Available</h3>
            <p>No metrics were found. Please check if the training completed successfully.</p>
        </div>
        '''
    
    # Links úteis
    html += f'''
        <div class="info-section">
            <h3>🔗 Quick Links</h3>
            <div style="text-align: center;">
                <a href="https://github.com/{repo}/actions/runs/{run_id}" class="link-button">
                    📋 View Full Build Log
                </a>
                <a href="https://github.com/{repo}/commits/{branch}" class="link-button">
                    📝 Recent Commits
                </a>
                <a href="https://github.com/{repo}" class="link-button">
                    🏠 Repository
                </a>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated automatically by GitHub Actions 🤖</p>
            <p>Datathon Decision ML Pipeline</p>
        </div>
    </div>
</body>
</html>
'''
    
    return html


def main():
    """Função principal."""    
    if len(sys.argv) < 5:
        print("Uso: python generate_dashboard.py <commit_sha> <branch> <run_id> <repo>")
        sys.exit(1)
    
    commit_sha = sys.argv[1]
    branch = sys.argv[2] 
    run_id = sys.argv[3]
    repo = sys.argv[4]
    
    print(f"🎨 Gerando dashboard...")
    print(f"📝 Commit: {commit_sha[:8]}")
    print(f"🌿 Branch: {branch}")
    
    metrics = load_metrics()
    html = generate_dashboard_html(metrics, commit_sha, branch, run_id, repo)
    
    try:
        with open('dashboard.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ Dashboard HTML gerado: dashboard.html")
    except Exception as e:
        print(f"❌ Erro ao gerar dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()