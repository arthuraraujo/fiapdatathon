# scripts/prepare_deps.sh
#!/bin/bash

echo "🔧 Preparando dependências..."

# Gerar requirements.txt para Docker
uv export --format requirements-txt --no-hashes > requirements.txt

echo "✅ requirements.txt gerado"

# Criar lock file se não existir
if [ ! -f uv.lock ]; then
    echo "📦 Gerando uv.lock..."
    uv lock
fi

echo "✅ Dependências preparadas!"