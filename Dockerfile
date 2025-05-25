# Dockerfile para produção - Datathon Decision API
FROM python:3.12-slim

# Instala dependências do sistema
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Instala UV e Gunicorn
RUN pip install uv gunicorn

# Cria diretório de trabalho
WORKDIR /app

# Copia apenas o necessário para produção
COPY datathon_decision/ /app/datathon_decision/
COPY pyproject.toml /app/

# Garante que o diretório de logs exista e seja gravável
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Instala dependências do projeto
RUN uv pip install --system --no-cache-dir -r pyproject.toml || true

# Expondo a porta da API
EXPOSE 5050

# Comando para rodar a API Flask em produção com Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5050", "datathon_decision.src.app:app"]