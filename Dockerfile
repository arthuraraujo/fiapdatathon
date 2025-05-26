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

# Instalar dependências em ambiente virtual
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependências (usando lock se existir)
RUN uv sync --no-dev || (uv pip install --system -r pyproject.toml && uv pip install --system -e .)
# RUN uv sync --frozen --no-dev || uv pip install -e .

# === STAGE 2: Production ===
FROM base AS production

# Copiar venv da stage anterior
COPY --from=deps /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar apenas gunicorn no ambiente final
RUN pip install --no-cache-dir gunicorn==21.2.0

# Criar diretórios necessários
RUN mkdir -p logs models data/processed data/raw

# Criar usuário não-root para segurança
RUN useradd --create-home --shell /bin/bash app
USER app

# Copiar código da aplicação
COPY --chown=app:app datathon_decision/ ./datathon_decision/
COPY --chown=app:app pyproject.toml ./

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5050/api/health || exit 1

# Labels para metadados
LABEL org.opencontainers.image.title="Datathon Decision API"
LABEL org.opencontainers.image.description="ML API for recruitment decisions"
LABEL org.opencontainers.image.source="https://github.com/arthuraraujo/datathon"

# Expor porta
EXPOSE 5050

# Comando otimizado para produção
CMD ["gunicorn", \
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