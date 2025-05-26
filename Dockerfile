# Multi-stage Dockerfile otimizado para produção
FROM python:3.12-slim AS base

# Instalar dependências do sistema (apenas uma vez)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Instalar UV (versão específica para cache)
RUN pip install --no-cache-dir uv==0.4.18

WORKDIR /app

# === STAGE 1: Dependencies ===
FROM base AS deps

# Copiar apenas arquivos de dependências primeiro (melhor cache)
COPY pyproject.toml uv.lock* ./

RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# TENTATIVA DE INSTALAÇÃO MAIS FORTE:
RUN echo "Attempting to install packages into venv: /opt/venv" && \
    uv pip install flask flask-restx pandas scikit-learn joblib numpy python-dateutil && \
    echo "Listing /opt/venv/lib/python3.12/site-packages/ after install:" && \
    ls -l /opt/venv/lib/python3.12/site-packages/flask* # === STAGE 2: Production ===
FROM base AS production # Lembre-se do WORKDIR /app herdado do base

COPY --from=deps /opt/venv /opt/venv

# CORREÇÃO AQUI: Comentário movido para a linha anterior
# Mantém o PATH configurado para o venv
ENV PATH="/opt/venv/bin:$PATH"

# 1. GARANTIR QUE GUNICORN SEJA INSTALADO NO VENV USANDO O PIP DO VENV
RUN echo "Attempting to install gunicorn into venv: /opt/venv" && \
    /opt/venv/bin/pip install --no-cache-dir gunicorn==21.2.0 && \
    echo "Checking for gunicorn in venv:" && \
    ls -l /opt/venv/bin/gunicorn

RUN mkdir -p logs models data/processed data/raw
# Dê permissão ao 'app' user para os diretórios que ele possa precisar escrever
RUN chown -R app:app logs models data

RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /app # Definir WORKDIR após USER app

COPY --chown=app:app datathon_decision/ ./datathon_decision/
COPY --chown=app:app pyproject.toml ./ # Se o pyproject.toml for necessário em runtime

# DEBUGGING COMO USUÁRIO 'app' (ajustado para verificar o gunicorn do venv)
RUN echo "DEBUGGING AS USER $(whoami) IN $(pwd)" && \
    echo "PATH IS: $PATH" && \
    echo "WHICH PYTHON: $(which python)" && \
    echo "PYTHON VERSION: $(python --version)" && \
    echo "WHICH PIP (should be venv): $(which pip)" && \
    echo "LOCATION OF GUNICORN (from which): $(which gunicorn)" && \
    echo "LISTING /opt/venv/bin/gunicorn: " && ls -l /opt/venv/bin/gunicorn && \
    echo "VERSION OF /opt/venv/bin/gunicorn: " && /opt/venv/bin/gunicorn --version && \
    echo "TRYING TO IMPORT FLASK WITH PYTHON FROM VENV:" && \
    /opt/venv/bin/python -c "import flask; print('Flask version:', flask.__version__)"

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5050/api/health || exit 1

LABEL org.opencontainers.image.title="Datathon Decision API"
LABEL org.opencontainers.image.description="ML API for recruitment decisions"
LABEL org.opencontainers.image.source="https://github.com/arthuraraujo/fiapdatathon"

EXPOSE 5050

# 2. CHAMAR EXPLICITAMENTE O GUNICORN DO VENV NO CMD
CMD ["/opt/venv/bin/gunicorn", \
     "--bind", "0.0.0.0:5050", \
     "--workers", "2", \
     "--worker-class", "sync", \
     "--timeout", "30", \
     "--keep-alive", "2", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "datathon_decision.src.app:app"]