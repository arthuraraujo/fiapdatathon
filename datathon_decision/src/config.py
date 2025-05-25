import pathlib

# Paths
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# Create dirs if they don't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Data files
APPLICANTS_FILE = RAW_DATA_DIR / "applicants.json"
JOBS_FILE = RAW_DATA_DIR / "vagas.json"
PROSPECTS_FILE = RAW_DATA_DIR / "prospects.json"

# Model and preprocessor files
MODEL_NAME = "random_forest_model.joblib"
PREPROCESSOR_NAME = "preprocessor_objects.joblib"
TRAINING_COLUMNS_NAME = "training_columns.joblib"
MODEL_PATH = MODELS_DIR / MODEL_NAME
PREPROCESSOR_PATH = MODELS_DIR / PREPROCESSOR_NAME
TRAINING_COLUMNS_PATH = MODELS_DIR / TRAINING_COLUMNS_NAME

# Target variable
TARGET_VARIABLE = "situacao_candidado"
POSITIVE_CLASS = "Contratado pela Decision"

# Feature Engineering
KEY_TECH_SKILLS = [
    "java", "python", "sap", "sql", "oracle", "aws", "abap", "cloud", "microservices", "api"
]

PROFESSIONAL_LEVEL_MAP = {
    "júnior": 1, "junior": 1, "jr": 1,
    "pleno": 2, "pl": 2,
    "sênior": 3, "senior": 3, "sr": 3,
    "especialista": 4, "lead": 4, "tech lead": 4, "consultor": 3,
    "analista": 2
}
LANGUAGE_LEVEL_MAP = {
    "nenhum": 0,
    "básico": 1, "basico": 1,
    "intermediário": 2, "intermediario": 2,
    "avançado": 3, "avancado": 3,
    "fluente": 4
}
ACADEMIC_LEVEL_MAP = {
    "ensino médio": 1, "ensino medio": 1,
    "técnico": 2, "tecnico": 2,
    "superior incompleto": 3,
    "ensino superior incompleto": 3,
    "superior completo": 4, "ensino superior completo": 4, "graduação": 4, "bacharel": 4,
    "pós-graduação": 5, "pos-graduacao": 5, "especialização": 5, "mba": 5,
    "mestrado": 6,
    "doutorado": 7
}

# Proxies de Fit Cultural
COMPANY_TYPE_KEYWORDS = {
    'multinacional_cat': ['multinacional', 'global', 'international', 'ltda', 's.a', 's/a'],
    'startup_cat': ['startup', 'inovação', 'fintech', 'agile'],
    'consultoria_cat': ['consultoria', 'consulting', 'kpmg', 'accenture', 'deloitte', 'pwc']
}

# Palavras-chave para comentários negativos (Engajamento)
NEGATIVE_COMMENT_KEYWORDS = [
    'desistiu', 'não responde', 'sem interesse', 'não tem interesse', 'recusou', 'não atende', 'não evoluir'
]

# Features categóricas (pré-OHE)
CATEGORICAL_FEATURES = [
    'vaga_nivel_profissional_norm_cat',
    'vaga_nivel_academico_norm_cat',
    'vaga_nivel_ingles_norm_cat',
    'vaga_eh_sap_cat',
    'vaga_area_atuacao_principal_cat',
    'candidato_nivel_profissional_norm_cat',
    'candidato_nivel_academico_norm_cat',
    'candidato_nivel_ingles_norm_cat',
    'candidato_area_atuacao_principal_cat',
    'match_nivel_profissional_cat',
    'match_nivel_academico_cat',
    'match_nivel_ingles_cat',
    'match_area_atuacao_cat',
    # Proxies culturais
    'candidato_exp_multinacional_cat',
    'candidato_exp_startup_cat',
    'candidato_exp_consultoria_cat',
    # Proxy engajamento
    'prospect_comentario_negativo_cat'
]

# Features numéricas
NUMERICAL_FEATURES = [
    'vaga_competencias_keywords_count_num',
    'candidato_conhecimentos_keywords_count_num',
    'candidato_cv_keywords_count_num',
    'comentario_len_num',
    # Proxies engajamento/cultural
    'candidato_taxa_desistencia_historica_num',
    'match_objetivo_vaga_score_num',
    'candidato_numero_empregos_num'
]

# Logging configuration
LOG_FILE = LOGS_DIR / "api_log.txt"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Outras constantes
RANDOM_STATE = 42
TEST_SIZE = 0.2 