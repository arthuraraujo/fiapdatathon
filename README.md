# Fase 5 - FIAP

## **Grupo 24:**

Nome: Arthur Francisco Araújo da Silva

Nick(Discord): afaraujo

RM: rm357855

---

---

## Datathon Decision - IA para Otimização de Recrutamento

Este projeto implementa uma solução baseada em Inteligência Artificial para otimizar o processo de recrutamento da Decision, aprimorando o "match" entre candidatos e vagas. Utiliza machine learning para prever a probabilidade de um candidato ser contratado para uma função específica, aprendendo com dados históricos de colocações bem-sucedidas e malsucedidas.

---

## Sumário

- [Justificativa do Problema](#justificativa-do-problema)
- [Abordagem da Solução](#abordagem-da-solução)
- [Arquitetura e Estrutura do Projeto](#arquitetura-e-estrutura-do-projeto)
- [Principais Features do Modelo de IA](#principais-features-do-modelo-de-ia)
- [Configuração e Instalação](#configuração-e-instalação)
- [Execução do Projeto](#execução-do-projeto)
- [Endpoints da API](#endpoints-da-api)
- [Testes](#testes)
- [Monitoramento e Logs](#monitoramento-e-logs)
- [Próximos Passos e Expansões](#próximos-passos-e-expansões)
- [Troubleshooting](#troubleshooting)
- [Gerenciamento de Arquivos Grandes](#gerenciamento-de-arquivos-grandes)
- [Boas Práticas de Versionamento e Deploy](#boas-práticas-de-versionamento-e-deploy)

---

## Justificativa do Problema

A Decision enfrenta desafios como:

- Encontrar o candidato ideal de forma eficiente.
- Falta de padronização nas entrevistas.
- Dificuldade em avaliar engajamento/motivação dos candidatos.
- Entrevistas técnicas/culturais apressadas ou omitidas, impactando a qualidade da seleção.

---

## Abordagem da Solução

1. **Insights Baseados em Dados:** Análise de `Jobs.json` (vagas), `Prospects.json` (candidaturas/status) e `Applicants.json` (perfis/CVs).
2. **Engenharia de Features:** Criação de features ricas, incluindo:
   - Níveis profissional, acadêmico e de idiomas normalizados.
   - Contagem de habilidades técnicas chave (Java, Python, SAP, SQL, AWS).
   - Indicadores booleanos (ex: vaga SAP).
   - Scores de match para níveis e áreas.
   - Proxies de fit cultural (experiência em multinacionais, startups, consultorias).
   - Proxies de engajamento (análise de comentários, taxa histórica de desistência, similaridade entre objetivo profissional e título da vaga).
3. **Modelo de Machine Learning:** RandomForestClassifier, com balanceamento de classes.
4. **API REST:** Exposição do modelo via Flask-RESTx, endpoints `/api/predict` e `/api/health`, documentação Swagger em `/docs`.
5. **Conteinerização:** Docker para deploy consistente.

---

## Arquitetura e Estrutura do Projeto

```
datathon-decision/
├── data/
│   ├── raw/              # Dados brutos (applicants.json, prospects.json, vagas.json)
│   └── processed/        # Dados processados (train_data.joblib, val_data.joblib)
├── datathon_decision/
│   ├── src/
│   │   ├── app.py            # API Flask
│   │   ├── config.py         # Configurações e constantes
│   │   ├── model_utils.py    # Treinamento, avaliação, predição
│   │   ├── preprocess_utils.py # ETL, merge, feature engineering, pré-processamento
│   │   └── train_pipeline.py # Orquestra o treinamento
│   └── tests/
│       └── test_preprocess_utils.py # Testes unitários
├── docs/                   # Documentação e exemplos de payload
├── logs/                   # Logs da API
├── models/                 # Modelo salvo, pré-processador, colunas de treino
├── .gitignore
├── .gitattributes          # Configuração do Git LFS
├── Dockerfile
├── pyproject.toml
├── README.md
└── test_api_examples.sh    # Teste automatizado do endpoint /predict
```

---

## Principais Features do Modelo de IA

- **Engenharia de Features Abrangente:** Informações de perfis, vagas e interações.
- **Correspondência de Níveis:** Profissional, acadêmico e idiomas.
- **Análise de Habilidades:** Contagem de skills técnicas chave.
- **Proxies de Fit Cultural:** Experiência em multinacionais, startups, consultorias.
- **Sinais de Engajamento:** Análise de comentários de recrutadores (sentimento negativo), taxa histórica de desistência.
- **Alinhamento de Objetivos:** Similaridade entre objetivo profissional e título da vaga.
- **Pré-processamento Robusto:** Lida com dados ausentes, One-Hot Encoding para categóricas.

---

## Configuração e Instalação

### Pré-requisitos

- Python 3.12
- [UV](https://github.com/astral-sh/uv)
- Docker Desktop
- Git LFS (para arquivos grandes de dados)

### Instalação do Git LFS

**macOS:**

```bash
# Usando Homebrew
brew install git-lfs

# Ou baixar diretamente de: https://git-lfs.github.io/
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install git-lfs
```

**Windows:**

```bash
# Usando chocolatey
choco install git-lfs

# Ou baixar diretamente de: https://git-lfs.github.io/
```

### Passos de Configuração

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/arthuraraujo/fiapdatathon.git
   cd datathon-decision
   ```

2. **Configure o Git LFS (primeiro uso):**

   ```bash
   # Verificar se está instalado
   git lfs version

   # Configurar LFS no repositório (se ainda não configurado)
   git lfs install

   # Baixar arquivos LFS (se já existirem no repositório)
   git lfs pull
   ```

3. **Crie e ative o ambiente virtual:**

   ```bash
   uv venv
   source .venv/bin/activate  # Linux/macOS
   # .venv\Scripts\activate    # Windows
   ```

4. **Instale as dependências:**

   ```bash
   uv pip install -r pyproject.toml
   # ou, se empacotado:
   uv pip install .
   ```

5. **Verificar arquivos de dados:**

   ```bash
   # Verificar se os arquivos JSON estão disponíveis
   ls -la data/raw/

   # Se não estiverem, eles serão baixados automaticamente pelo Git LFS
   # durante o clone ou com git lfs pull
   ```

---

## Execução do Projeto

### 1. Pré-processamento de Dados

```bash
uv run python -m datathon_decision.src.preprocess_utils data/raw/
```

- Saída: `data/processed/train_data.joblib`, `data/processed/val_data.joblib`, `models/preprocessor_objects.joblib`, `models/training_columns.joblib`

### 2. Treinamento do Modelo

```bash
uv run python -m datathon_decision.src.train_pipeline
```

- Saída: `models/random_forest_model.joblib`
- Métricas impressas no console (Acurácia, Precisão, Recall, F1, ROC AUC)

### 3. Executando a API Localmente

```bash
uv run python -m datathon_decision.src.app
```

- API: [http://localhost:5050](http://localhost:5050)
- Swagger: [http://localhost:5050/docs](http://localhost:5050/docs)

### 4. Executando com Docker

1. **Build da imagem:**
   ```bash
   docker build -t datathon-decision-api .
   ```
2. **Run do container:**
   ```bash
   docker run -p 5050:5050 -v "$(pwd)/logs:/app/logs" datathon-decision-api
   ```
   - O volume de logs é opcional.
   - API e Swagger disponíveis nos mesmos endpoints acima.

---

## Endpoints da API

Todos os endpoints são prefixados com `/api`.

### `GET /api/health`

- Verifica a saúde da API.
- Resposta:
  ```json
  { "status": "healthy" }
  ```

### `POST /api/predict`

- Recebe um payload JSON com informações de candidato e vaga.
- Exemplo de payload:
  ```json
  {
    "payload": {
      "situacao_candidado": "Analise",
      "perfil_vaga": {
        "nivel profissional": "Sênior",
        "nivel_academico": "Superior Completo",
        "nivel_ingles": "Avançado",
        "areas_atuacao": "TI - DEV",
        "competencia_tecnicas_e_comportamentais": "Java Python SQL"
      },
      "informacoes_basicas": {
        "vaga_sap": "Não",
        "titulo_vaga": "Dev Java Sr"
      },
      "informacoes_profissionais": {
        "nivel_profissional": "Sênior",
        "area_atuacao": "Desenvolvimento",
        "conhecimentos_tecnicos": "Java Spring",
        "objetivo_profissional": "Desenvolvedor Java"
      },
      "formacao_e_idiomas": {
        "nivel_academico": "Superior Completo",
        "nivel_ingles": "Avançado"
      },
      "cv_pt": "Experiencia com Java e Python",
      "comentario_prospect": "Candidato promissor",
      "data_candidatura_prospect": "01-01-2023",
      "ultima_atualizacao_prospect": "10-01-2023",
      "candidato_taxa_desistencia_historica_num": 0.1
    }
  }
  ```
- Resposta:
  ```json
  { "match_probability": 0.85 }
  ```

---

## Testes

### Testes Unitários

```bash
uv run pytest
```

- Testes em `datathon_decision/tests/test_preprocess_utils.py`

### Testes de Endpoint

```bash
bash test_api_examples.sh
# Para testar uma URL diferente:
# bash test_api_examples.sh http://sua-api-url/api/predict
```

- Requer `jq` instalado.
- Usa exemplos de `docs/payload_examples.json`.

---

## Monitoramento e Logs

- **Logs:** Todas as requisições, predições e erros são registrados em `logs/api.log` e no stdout (visível via `docker logs <container_id>`).
- **Monitoramento de Drift:** Os logs servem de base para monitoramento futuro de drift (distribuição das features, scores, etc). Não há painel automatizado implementado.

---

## Próximos Passos e Expansões

- **Deploy em Nuvem:** (Opcional) Adaptar para AWS, Google Cloud Run, Heroku, etc.
- **Monitoramento de Drift:** Implementar coleta de métricas, dashboard (ex: Streamlit/Dash), alertas.
- **Validação Avançada:** Persistir métricas, integrar MLflow.
- **Validação de Dados:** Adicionar schemas Pydantic para payloads.
- **Documentação Técnica:** Expandir docs/ARCHITECTURE.md, API_DOCUMENTATION.md, DEPLOYMENT_GUIDE.md.
- **Testes de Integração e Performance:** Expandir cobertura de testes.

---

## Troubleshooting

### Problemas Comuns

- **Porta em uso:** Altere a porta no Dockerfile/comando ou libere a 5050.
- **Swagger não aparece:** Verifique se a API está rodando e acesse `/docs`.
- **Problemas de dependências:** Use sempre UV e Python 3.12.
- **Logs não aparecem:** Verifique permissões da pasta `logs/` e o volume no Docker.

### ⚠️ Problemas com Git LFS - IMPORTANTE

**Problema mais comum: Arquivos JSON aparecem como "pointer files" ao invés do conteúdo real**

Se você ver algo como:

```
version https://git-lfs.github.com/spec/v1
oid sha256:55061c1e4c6ff820ff84e3b222c022a818eb145e6bb5dfd2d3d3487c3854decc
size 203538441
```

Isso significa que os arquivos LFS não foram baixados corretamente. **Soluções:**

1. **Verificar se o Git LFS está instalado:**

   ```bash
   git lfs version
   ```

   Se não estiver instalado, siga as [instruções de instalação](#instalação-do-git-lfs) acima.

2. **Configurar o Git LFS no repositório:**

   ```bash
   git lfs install
   ```

3. **Baixar os arquivos LFS:**

   ```bash
   git lfs pull
   ```

   Ou para baixar apenas os arquivos de dados:

   ```bash
   git lfs pull --include="datathon_decision/data/raw/*"
   ```

4. **Se ainda não funcionar, force o fetch:**

   ```bash
   git lfs fetch --all
   git lfs checkout
   ```

5. **Verificar se os arquivos foram baixados:**

   ```bash
   git lfs ls-files
   # Deve mostrar os arquivos JSON grandes

   # Verificar o conteúdo real (deve mostrar JSON, não pointer)
   head -5 data/raw/applicants.json
   ```

**Para clones futuros do repositório:**

```bash
git clone <url-do-repo>
cd <nome-do-repo>
git lfs pull  # Baixa os arquivos LFS após o clone
```

**Outros problemas de Git LFS:**

- **Erro "git lfs not found":** Instale o Git LFS conforme instruções acima.
- **Problemas de autenticação:** Configure suas credenciais do GitHub:
  ```bash
  git config --global credential.helper store
  # ou use token de acesso pessoal
  ```
- **Verificar configuração do LFS:**
  ```bash
  git lfs env  # Mostra configuração atual
  cat .gitattributes  # Mostra quais tipos de arquivo são rastreados
  ```

### Verificações de Git LFS

```bash
# Verificar status do LFS
git lfs env

# Listar arquivos rastreados pelo LFS
git lfs ls-files

# Verificar quais tipos de arquivo estão configurados
cat .gitattributes
```

---

## Gerenciamento de Arquivos Grandes

Este projeto utiliza **Git LFS (Large File Storage)** para gerenciar arquivos de dados grandes (>100MB) de forma eficiente.

### Arquivos Gerenciados pelo LFS

Os seguintes tipos de arquivo são automaticamente gerenciados pelo Git LFS:

- `data/raw/*.json` - Dados brutos de treinamento
- `*/data/raw/*.json` - Dados em subdiretórios

### Comandos Úteis do Git LFS

```bash
# Verificar arquivos LFS
git lfs ls-files

# Baixar todos os arquivos LFS
git lfs pull

# Verificar status dos arquivos LFS
git lfs status

# Ver informações do repositório LFS
git lfs env
```

### Para Desenvolvedores

**Adicionando novos arquivos grandes:**

```bash
# Configurar tracking para novos tipos de arquivo
git lfs track "*.pkl"
git lfs track "models/*.joblib"

# Adicionar configuração ao git
git add .gitattributes
git commit -m "Track new large files with LFS"

# Adicionar os arquivos normalmente
git add arquivo_grande.pkl
git commit -m "Add large model file"
git push
```

**Clonando o repositório:**

```bash
# Clone normal já baixa arquivos LFS automaticamente
git clone <url-do-repositorio>

# Se necessário, baixar arquivos LFS manualmente
cd <repositorio>
git lfs pull
```

---

## Boas Práticas de Versionamento e Deploy

### Versionamento

- **Arquivos grandes (>50MB):** Gerenciados automaticamente pelo Git LFS.
- **Dados sensíveis:** Nunca versionar credenciais, tokens ou dados pessoais.
- **Dados brutos:** Versionados via Git LFS em `data/raw/`.
- **Dados processados:** Não versionar `data/processed/` (são gerados dinamicamente).
- **Modelos treinados:** Não versionar `models/*.joblib` ou `models/*.pkl` (são gerados dinamicamente).

### Deploy

- **Desenvolvimento Local:**

  1. Clone o repositório (arquivos LFS baixam automaticamente)
  2. Treine o modelo localmente
  3. Execute a API para testes

- **Deploy em Produção:**

  1. Configure Git LFS no ambiente de CI/CD
  2. Treine o modelo no pipeline
  3. Construa a imagem Docker com modelo incluído
  4. Deploy da imagem

- **GitHub Actions:**
  ```yaml
  - name: Checkout with LFS
    uses: actions/checkout@v4
    with:
      lfs: true
  ```

### Compartilhamento de Dados

Para compartilhar dados ou modelos grandes entre ambientes:

- **Desenvolvimento:** Use Git LFS (incluído no repositório)
- **Produção:** Considere serviços externos (S3, Google Cloud Storage, etc) para arquivos muito grandes (>1GB)
