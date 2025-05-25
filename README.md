# Datathon Decision - IA para Otimização de Recrutamento

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

### Passos

1. **Clone o repositório:**
   ```bash
   git clone <url-do-seu-repositorio>
   cd datathon-decision
   ```
2. **Crie e ative o ambiente virtual:**
   ```bash
   uv venv
   source .venv/bin/activate  # Linux/macOS
   # .venv\Scripts\activate    # Windows
   ```
3. **Instale as dependências:**
   ```bash
   uv pip install -r pyproject.toml
   # ou, se empacotado:
   uv pip install .
   ```
4. **Coloque os arquivos de dados:**
   - Crie `data/raw/`
   - Copie `applicants.json`, `prospects.json`, `vagas.json` para `data/raw/`

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

- **Porta em uso:** Altere a porta no Dockerfile/comando ou libere a 5050.
- **Swagger não aparece:** Verifique se a API está rodando e acesse `/docs`.
- **Problemas de dependências:** Use sempre UV e Python 3.12.
- **Logs não aparecem:** Verifique permissões da pasta `logs/` e o volume no Docker.

---

Para dúvidas, consulte a documentação Swagger em `/docs` ou abra uma issue no repositório.

---

## Boas Práticas de Versionamento e Deploy

- **Não versionar arquivos grandes (>50MB) ou sensíveis** no repositório.
- **Dados brutos:** O diretório `data/raw/` pode ser versionado para manter a estrutura, mas **não adicione arquivos grandes** (ex: mantenha apenas exemplos pequenos ou arquivos de schema).
- **Dados processados:** Não versionar `data/processed/`.
- **Modelos treinados:** Não versionar arquivos em `models/*.joblib` ou `models/*.pkl`.
- **Deploy:**
  - Treine o modelo localmente e coloque o arquivo resultante em `models/`.
  - Só então construa a imagem Docker, que irá empacotar o modelo junto com o código.
  - Para compartilhar dados/modelos, utilize serviços externos (S3, Google Drive, etc).

---

Para dúvidas, consulte a documentação Swagger em `/docs` ou abra uma issue no repositório. 