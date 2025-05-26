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
# Install all Python dependencies, including gunicorn, in this stage
RUN echo "Attempting to install packages (including gunicorn) into venv: /opt/venv" && \
    uv pip install --no-cache-dir flask flask-restx pandas scikit-learn joblib numpy python-dateutil gunicorn==21.2.0 && \
    echo "Listing /opt/venv/lib/python3.12/site-packages/ after install:" && \
    ls -l /opt/venv/lib/python3.12/site-packages/flask* && \
    echo "Verifying gunicorn installation in deps stage:" && \
    ls -l /opt/venv/bin/gunicorn && \
    /opt/venv/bin/gunicorn --version

# === STAGE 2: Production ===
# Lembre-se do WORKDIR /app herdado do base
FROM base AS production

COPY --from=deps /opt/venv /opt/venv

# Mantém o PATH configurado para o venv
ENV PATH="/opt/venv/bin:$PATH"

# Gunicorn is already installed from the deps stage.
# We can add a check to ensure it's present.
RUN echo "Checking for gunicorn in copied venv:" && \
    ls -l /opt/venv/bin/gunicorn && \
    /opt/venv/bin/gunicorn --version || (echo "Gunicorn not found in /opt/venv/bin after copy!"; exit 1)

RUN mkdir -p logs models data/processed data/raw

# 1. Create the 'app' user FIRST
RUN useradd --create-home --shell /bin/bash app

# 2. THEN, give permission to the 'app' user for the directories
RUN chown -R app:app logs models data

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
    echo "PIP VERSION: $(pip --version)" && \
    echo "LOCATION OF GUNICORN (from which): $(which gunicorn)" && \
    echo "LISTING /opt/venv/bin/gunicorn (as app user): " && ls -l /opt/venv/bin/gunicorn && \
    echo "VERSION OF /opt/venv/bin/gunicorn (as app user): " && /opt/venv/bin/gunicorn --version && \
    echo "TRYING TO IMPORT FLASK WITH PYTHON FROM VENV (as app user):" && \
    python -c "import flask; print('Flask version:', flask.__version__)"

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5050/api/health || exit 1

LABEL org.opencontainers.image.title="Datathon Decision API"
LABEL org.opencontainers.image.description="ML API for recruitment decisions"
LABEL org.opencontainers.image.source="https://github.com/arthuraraujo/fiapdatathon"

EXPOSE 5050

# 2. CHAMAR EXPLICITAMENTE O GUNICORN DO VENV NO CMD
# This is correct as PATH is set to include /opt/venv/bin,
# but being explicit with /opt/venv/bin/gunicorn is safer.
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