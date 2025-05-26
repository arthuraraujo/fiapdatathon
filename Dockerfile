# Multi-stage Dockerfile ultra-otimizado para apenas 512MB RAM
FROM python:3.12-slim AS base

# Instalar apenas o essencial
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Instalar UV
RUN pip install --no-cache-dir uv==0.4.18

WORKDIR /app

# === STAGE 1: Dependencies ===
FROM base AS deps

COPY pyproject.toml uv.lock* ./

RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" 

# Instalar dependências com versões mais leves quando possível
RUN uv pip install --no-cache-dir \
    flask==2.3.3 \
    flask-restx==1.2.0 \
    pandas==2.0.3 \
    scikit-learn==1.3.0 \
    joblib==1.3.2 \
    numpy==1.24.4 \
    python-dateutil==2.8.2 \
    gunicorn==21.2.0

# === STAGE 2: Production ===
FROM base AS production

COPY --from=deps /opt/venv /opt/venv

# Configurações críticas para 512MB
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=random
# Limitar uso de memória do Python
ENV MALLOC_TRIM_THRESHOLD_=100000
ENV MALLOC_MMAP_THRESHOLD_=100000
# Configurações para otimizar garbage collection
ENV PYTHONGC=1

RUN mkdir -p logs models data/processed data/raw

RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app logs models data

USER app
WORKDIR /app

COPY --chown=app:app datathon_decision/ ./datathon_decision/
COPY --chown=app:app pyproject.toml ./

# Pré-compilar bytecode para economizar RAM na inicialização
RUN python -m compileall -q datathon_decision/

# Teste básico de importação
RUN python -c "
import sys
import os
print('Testing basic imports...')
try:
    import flask
    print(f'✅ Flask: {flask.__version__}')
    import pandas as pd
    print(f'✅ Pandas: {pd.__version__}')
    # Não importar o app completo aqui para economizar memória
    print('✅ Basic imports successful')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

# Health check com timeout maior
HEALTHCHECK --interval=60s --timeout=30s --start-period=60s --retries=2 \
    CMD curl -f http://localhost:5050/api/health || exit 1

LABEL org.opencontainers.image.title="Datathon Decision API"
LABEL org.opencontainers.image.description="ML API for recruitment decisions"

EXPOSE 5050

# Configuração ULTRA-CONSERVADORA para 512MB
CMD ["/opt/venv/bin/gunicorn", \
     "--bind", "0.0.0.0:5050", \
     "--workers", "1", \
     "--worker-class", "sync", \
     "--timeout", "300", \
     "--graceful-timeout", "60", \
     "--keep-alive", "2", \
     "--max-requests", "50", \
     "--max-requests-jitter", "10", \
     "--worker-tmp-dir", "/dev/shm", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "warning", \
     "--limit-request-line", "2048", \
     "--limit-request-fields", "50", \
     "--limit-request-field-size", "2048", \
     "datathon_decision.src.app:app"]