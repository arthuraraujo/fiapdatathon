import pandas as pd
import json
import os
import sys
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
import joblib
import re
from datetime import datetime

try:
    # Garantindo que todas as constantes necessárias do config.py sejam importadas
    from datathon_decision.src.config import (
        CATEGORICAL_FEATURES, NUMERICAL_FEATURES, KEY_TECH_SKILLS,
        PROFESSIONAL_LEVEL_MAP, LANGUAGE_LEVEL_MAP, ACADEMIC_LEVEL_MAP,
        COMPANY_TYPE_KEYWORDS, NEGATIVE_COMMENT_KEYWORDS,
        TARGET_VARIABLE, POSITIVE_CLASS,
        PREPROCESSOR_PATH, TRAINING_COLUMNS_PATH,
        RAW_DATA_DIR as DEFAULT_RAW_DATA_DIR, 
        PROCESSED_DATA_DIR as DEFAULT_PROCESSED_DATA_DIR,
        MODELS_DIR as DEFAULT_MODELS_DIR,
        TEST_SIZE, RANDOM_STATE # Garantindo que TEST_SIZE e RANDOM_STATE estão aqui
    )
except ModuleNotFoundError as e:
    print(f"AVISO CRÍTICO: Falha ao importar 'config' (datathon_decision.src.config). Detalhes: {e}")
    print("Verifique seu PYTHONPATH, a estrutura do projeto ou como o script está sendo executado.")
    print("As constantes de config.py podem não estar disponíveis, causando mais erros.")
    raise # Interrompe a execução se o config não puder ser importado


def load_data(data_dir):
    """Carrega os dados JSON de um diretório especificado."""
    jobs_path = os.path.join(data_dir, 'vagas.json')
    prospects_path = os.path.join(data_dir, 'prospects.json')
    applicants_path = os.path.join(data_dir, 'applicants.json')

    try:
        with open(jobs_path, 'r', encoding='utf-8') as f:
            jobs_data = json.load(f)
        with open(prospects_path, 'r', encoding='utf-8') as f:
            prospects_data = json.load(f)
        with open(applicants_path, 'r', encoding='utf-8') as f:
            applicants_data = json.load(f)
    except FileNotFoundError as e:
        print(f"Erro: Um dos arquivos de dados não foi encontrado em '{data_dir}'. Detalhes: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Erro: Falha ao decodificar JSON em um dos arquivos. Detalhes: {e}")
        raise

    df_jobs = pd.DataFrame.from_dict(jobs_data, orient='index')
    df_jobs.index.name = 'vaga_id'
    df_jobs.reset_index(inplace=True)

    df_applicants = pd.DataFrame.from_dict(applicants_data, orient='index')
    df_applicants.index.name = 'codigo_profissional'
    df_applicants.reset_index(inplace=True)
    df_applicants['codigo_profissional'] = df_applicants['codigo_profissional'].astype(str)

    prospect_list = []
    for job_id, details in prospects_data.items():
        for prospect in details.get('prospects', []):
            prospect_entry = {
                'vaga_id': str(job_id),
                'titulo_vaga_prospect': details.get('titulo'),
                'modalidade_prospect': details.get('modalidade'),
                'nome_candidato_prospect': prospect.get('nome'),
                'codigo_candidato_prospect': str(prospect.get('codigo')),
                'situacao_candidado': prospect.get('situacao_candidado'),
                'data_candidatura_prospect': prospect.get('data_candidatura'),
                'ultima_atualizacao_prospect': prospect.get('ultima_atualizacao'),
                'comentario_prospect': prospect.get('comentario'),
                'recrutador_prospect': prospect.get('recrutador')
            }
            prospect_list.append(prospect_entry)
    df_prospects = pd.DataFrame(prospect_list)
    return df_jobs, df_prospects, df_applicants

def merge_data(df_jobs, df_prospects, df_applicants):
    """Mescla os dataframes de jobs, prospects e applicants."""
    desistencias = df_prospects[df_prospects['situacao_candidado'] == 'Desistiu']
    contagem_desistencias = desistencias.groupby('codigo_candidato_prospect').size().rename('num_desistencias')
    contagem_total_prospeccoes = df_prospects.groupby('codigo_candidato_prospect').size().rename('num_total_prospeccoes')

    historico_candidato_stats = pd.concat([contagem_desistencias, contagem_total_prospeccoes], axis=1).reset_index()
    historico_candidato_stats['num_desistencias'] = historico_candidato_stats['num_desistencias'].fillna(0)
    historico_candidato_stats['num_total_prospeccoes'] = historico_candidato_stats['num_total_prospeccoes'].fillna(0).apply(lambda x: x if x > 0 else 1)
    historico_candidato_stats['candidato_taxa_desistencia_historica_num'] = (
        historico_candidato_stats['num_desistencias'] / historico_candidato_stats['num_total_prospeccoes']
    ).fillna(0)

    df_applicants = pd.merge(df_applicants,
                               historico_candidato_stats[['codigo_candidato_prospect', 'candidato_taxa_desistencia_historica_num']],
                               left_on='codigo_profissional',
                               right_on='codigo_candidato_prospect',
                               how='left')
    df_applicants['candidato_taxa_desistencia_historica_num'] = df_applicants['candidato_taxa_desistencia_historica_num'].fillna(0)
    df_applicants.drop(columns=['codigo_candidato_prospect'], inplace=True, errors='ignore')

    df_merged = pd.merge(df_prospects, df_jobs, on='vaga_id', how='left')
    df_merged = pd.merge(df_merged, df_applicants,
                         left_on='codigo_candidato_prospect',
                         right_on='codigo_profissional',
                         how='left')
    return df_merged

def safe_get(data_dict, key, default="DESCONHECIDO"):
    if not isinstance(data_dict, dict):
        return default
    value = data_dict.get(key)
    return value if pd.notna(value) and value != '' else default

def normalize_text(text):
    if not isinstance(text, str):
        return "desconhecido"
    text = text.lower()
    text = re.sub(r'[^a-z0-9áéíóúãõâêîôûçàèìòùäëïöüñ\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text if text else "desconhecido"

def map_level(level_text, level_map):
    normalized = normalize_text(level_text)
    if not normalized or normalized == "desconhecido":
        return "0"
    for k_map, v_map in level_map.items():
        if k_map in normalized:
             return str(v_map)
    return "0"

def count_keywords(text, keywords_list):
    if not isinstance(text, str) or not keywords_list:
        return 0
    text_norm = normalize_text(text)
    if not text_norm or text_norm == "desconhecido":
        return 0
    count = 0
    for keyword in keywords_list:
        if normalize_text(keyword) in text_norm:
            count += 1
    return count

def compare_levels(level_vaga_numeric_str, level_candidato_numeric_str):
    if level_vaga_numeric_str == "0" or level_candidato_numeric_str == "0":
        return "DESCONHECIDO_LVL"
    try:
        level_vaga = int(level_vaga_numeric_str)
        level_candidato = int(level_candidato_numeric_str)
    except ValueError:
        return "ERRO_CONVERSAO_LVL"
    if level_candidato == level_vaga:
        return "EXATO"
    elif level_candidato > level_vaga:
        return "CANDIDATO_SUPERIOR"
    else:
        return "CANDIDATO_INFERIOR"

def diff_levels(level_vaga_numeric_str, level_candidato_numeric_str):
    if level_vaga_numeric_str == "0" or level_candidato_numeric_str == "0":
        return 0
    try:
        return abs(int(level_vaga_numeric_str) - int(level_candidato_numeric_str))
    except ValueError:
        return 0

def parse_date_robust(date_str):
    if not isinstance(date_str, str) or pd.isna(date_str):
        return None
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return None

def engineer_features(df_input):
    df = df_input.copy()

    if TARGET_VARIABLE in df.columns:
        df['target'] = df[TARGET_VARIABLE].apply(lambda x: 1 if x == POSITIVE_CLASS else 0)
        y_target_series = df['target']
    else:
        y_target_series = None

    df['vaga_nivel_profissional_raw'] = df['perfil_vaga'].apply(lambda x: safe_get(x, 'nivel profissional'))
    df['vaga_nivel_profissional_norm_cat'] = df['vaga_nivel_profissional_raw'].apply(lambda x: map_level(x, PROFESSIONAL_LEVEL_MAP))
    df['vaga_nivel_academico_raw'] = df['perfil_vaga'].apply(lambda x: safe_get(x, 'nivel_academico'))
    df['vaga_nivel_academico_norm_cat'] = df['vaga_nivel_academico_raw'].apply(lambda x: map_level(x, ACADEMIC_LEVEL_MAP))
    df['vaga_nivel_ingles_raw'] = df['perfil_vaga'].apply(lambda x: safe_get(x, 'nivel_ingles'))
    df['vaga_nivel_ingles_norm_cat'] = df['vaga_nivel_ingles_raw'].apply(lambda x: map_level(x, LANGUAGE_LEVEL_MAP))
    df['vaga_eh_sap_cat'] = df['informacoes_basicas'].apply(lambda x: 'SIM' if normalize_text(safe_get(x, 'vaga_sap')) == 'sim' else 'NAO')
    vaga_areas_raw = df['perfil_vaga'].apply(lambda x: safe_get(x, 'areas_atuacao', 'DESCONHECIDO'))
    df['vaga_area_atuacao_principal_cat'] = vaga_areas_raw.apply(lambda x: normalize_text(x.split('-')[0].split(',')[0] if isinstance(x, str) else 'DESCONHECIDO'))
    vaga_competencias_txt_series = df['perfil_vaga'].apply(lambda x: safe_get(x, 'competencia_tecnicas_e_comportamentais', '') + " " + safe_get(x, 'principais_atividades', ''))
    df['vaga_competencias_keywords_count_num'] = vaga_competencias_txt_series.apply(lambda x: count_keywords(x, KEY_TECH_SKILLS))
    df['vaga_requer_sap_cat'] = vaga_competencias_txt_series.apply(lambda x: 'SIM' if 'sap' in normalize_text(x) else 'NAO')

    df['candidato_nivel_profissional_raw'] = df['informacoes_profissionais'].apply(lambda x: safe_get(x, 'nivel_profissional'))
    df['candidato_nivel_profissional_norm_cat'] = df['candidato_nivel_profissional_raw'].apply(lambda x: map_level(x, PROFESSIONAL_LEVEL_MAP))
    df['candidato_nivel_academico_raw'] = df['formacao_e_idiomas'].apply(lambda x: safe_get(x, 'nivel_academico'))
    df['candidato_nivel_academico_norm_cat'] = df['candidato_nivel_academico_raw'].apply(lambda x: map_level(x, ACADEMIC_LEVEL_MAP))
    df['candidato_nivel_ingles_raw'] = df['formacao_e_idiomas'].apply(lambda x: safe_get(x, 'nivel_ingles'))
    df['candidato_nivel_ingles_norm_cat'] = df['candidato_nivel_ingles_raw'].apply(lambda x: map_level(x, LANGUAGE_LEVEL_MAP))
    candidato_areas_raw = df['informacoes_profissionais'].apply(lambda x: safe_get(x, 'area_atuacao', 'DESCONHECIDO'))
    df['candidato_area_atuacao_principal_cat'] = candidato_areas_raw.apply(lambda x: normalize_text(x.split(',')[0] if isinstance(x, str) else 'DESCONHECIDO'))
    candidato_conhecimentos_txt_series = df['informacoes_profissionais'].apply(lambda x: safe_get(x, 'conhecimentos_tecnicos', ''))
    df['candidato_conhecimentos_keywords_count_num'] = candidato_conhecimentos_txt_series.apply(lambda x: count_keywords(x, KEY_TECH_SKILLS))
    candidato_cv_txt_series = df['cv_pt'].fillna('').apply(normalize_text)
    df['candidato_cv_keywords_count_num'] = candidato_cv_txt_series.apply(lambda x: count_keywords(x, KEY_TECH_SKILLS))

    for company_type_key_cfg, keywords_list_cfg in COMPANY_TYPE_KEYWORDS.items():
        df[f'candidato_exp_{company_type_key_cfg}'] = candidato_cv_txt_series.apply(
            lambda cv_text: '1' if any(normalize_text(kw) in cv_text for kw in keywords_list_cfg) else '0'
        )
    df['candidato_tem_sap_cat'] = candidato_conhecimentos_txt_series.apply(lambda x: 'SIM' if 'sap' in normalize_text(x) else 'NAO')
    df['candidato_num_experiencias_num'] = df['informacoes_profissionais'].apply(lambda x: len(safe_get(x, 'experiencias', [])) if isinstance(safe_get(x, 'experiencias', []), list) else 0)
    df['candidato_num_certificacoes_num'] = df['informacoes_profissionais'].apply(lambda x: len(safe_get(x, 'certificacoes', '').split(',')) if isinstance(safe_get(x, 'certificacoes', ''), str) and safe_get(x, 'certificacoes', '') != "DESCONHECIDO" and safe_get(x, 'certificacoes', '') else 0)

    df['match_nivel_profissional_cat'] = df.apply(lambda row: compare_levels(row['vaga_nivel_profissional_norm_cat'], row['candidato_nivel_profissional_norm_cat']), axis=1)
    df['match_nivel_academico_cat'] = df.apply(lambda row: compare_levels(row['vaga_nivel_academico_norm_cat'], row['candidato_nivel_academico_norm_cat']), axis=1)
    df['match_nivel_ingles_cat'] = df.apply(lambda row: compare_levels(row['vaga_nivel_ingles_norm_cat'], row['candidato_nivel_ingles_norm_cat']), axis=1)
    df['match_area_atuacao_cat'] = (df['vaga_area_atuacao_principal_cat'] == df['candidato_area_atuacao_principal_cat']).astype(int).astype(str)
    
    df['diferenca_nivel_profissional_num'] = df.apply(lambda row: diff_levels(row['vaga_nivel_profissional_norm_cat'], row['candidato_nivel_profissional_norm_cat']), axis=1)
    df['diferenca_nivel_academico_num'] = df.apply(lambda row: diff_levels(row['vaga_nivel_academico_norm_cat'], row['candidato_nivel_academico_norm_cat']), axis=1)
    df['diferenca_nivel_ingles_num'] = df.apply(lambda row: diff_levels(row['vaga_nivel_ingles_norm_cat'], row['candidato_nivel_ingles_norm_cat']), axis=1)
    
    df['comentario_len_num'] = df['comentario_prospect'].fillna('').apply(len)
    df['data_candidatura_dt'] = df['data_candidatura_prospect'].apply(parse_date_robust)
    df['ultima_atualizacao_dt'] = df['ultima_atualizacao_prospect'].apply(parse_date_robust)
    df['tempo_no_processo_dias_num'] = (df['ultima_atualizacao_dt'] - df['data_candidatura_dt']).dt.days.fillna(-1)
    df['tempo_no_processo_dias_num'] = df['tempo_no_processo_dias_num'].apply(lambda x: x if x >= 0 else 0)

    comentario_prospect_norm = df['comentario_prospect'].fillna('').apply(normalize_text)
    df['prospect_comentario_negativo_cat'] = comentario_prospect_norm.apply(
        lambda c: '1' if any(kw in c for kw in NEGATIVE_COMMENT_KEYWORDS) else '0'
    )
    if 'candidato_taxa_desistencia_historica_num' not in df.columns:
        df['candidato_taxa_desistencia_historica_num'] = 0.0

    candidato_objetivo_txt_series = df['informacoes_profissionais'].apply(lambda x: normalize_text(safe_get(x, 'objetivo_profissional', '')))
    vaga_titulo_txt_series = df['informacoes_basicas'].apply(lambda x: normalize_text(safe_get(x, 'titulo_vaga', '')))

    def jaccard_similarity_local(text1_series_local, text2_series_local):
        scores = []
        for t1, t2 in zip(text1_series_local, text2_series_local):
            set1 = set(t1.split())
            set2 = set(t2.split())
            if not set1 or not set2:
                scores.append(0.0)
                continue
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            scores.append(intersection / union if union != 0 else 0.0)
        return scores
    df['match_objetivo_vaga_score_num'] = jaccard_similarity_local(candidato_objetivo_txt_series, vaga_titulo_txt_series)
    
    # Se 'candidato_numero_empregos_num' estiver em NUMERICAL_FEATURES e você quiser usar
    # 'candidato_num_experiencias_num' como sua fonte:
    if 'candidato_numero_empregos_num' in NUMERICAL_FEATURES:
         df['candidato_numero_empregos_num'] = df['candidato_num_experiencias_num']

    created_categorical_features = []
    for col_name in CATEGORICAL_FEATURES:
        if col_name not in df.columns:
            # print(f"AVISO EngineerFeatures: Cat Feature '{col_name}' não criada. Adicionando como 'DESCONHECIDO'.")
            df[col_name] = "DESCONHECIDO"
        df[col_name] = df[col_name].astype(str).fillna("DESCONHECIDO")
        created_categorical_features.append(col_name)

    created_numerical_features = []
    for col_name in NUMERICAL_FEATURES:
        if col_name not in df.columns:
            # print(f"AVISO EngineerFeatures: Num Feature '{col_name}' não criada. Adicionando como 0.")
            df[col_name] = 0
        df[col_name] = pd.to_numeric(df[col_name], errors='coerce').fillna(0)
        created_numerical_features.append(col_name)
        
    final_feature_columns = created_categorical_features + created_numerical_features
    
    # A coluna 'target' pode não existir em df se y_target_series for None (predição)
    # Retorna apenas as features selecionadas.
    return df[final_feature_columns], y_target_series


def preprocess_data_split_save(df_features, series_target, out_dir_path, fit_ohe=False, ohe_encoder=None, training_cols_list=None):
    X_to_process = df_features.copy()

    if not CATEGORICAL_FEATURES:
        if NUMERICAL_FEATURES:
            X_processed = X_to_process[NUMERICAL_FEATURES].copy()
        else:
            X_processed = pd.DataFrame(index=X_to_process.index)
        current_ohe_encoder = None
        final_column_names_for_output = NUMERICAL_FEATURES[:] if NUMERICAL_FEATURES else []
    else:
        for col in CATEGORICAL_FEATURES:
            if col not in X_to_process.columns:
                 # print(f"AVISO Preprocess: Cat Feature '{col}' para OHE não encontrada. Adicionando como 'DESCONHECIDO'.")
                 X_to_process[col] = "DESCONHECIDO"
            X_to_process[col] = X_to_process[col].astype(str).fillna('DESCONHECIDO')

        if fit_ohe:
            current_ohe_encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
            current_ohe_encoder.fit(X_to_process[CATEGORICAL_FEATURES])
            joblib.dump(current_ohe_encoder, PREPROCESSOR_PATH)
            print(f"Preprocessor (OHE) salvo em {PREPROCESSOR_PATH}")
        elif ohe_encoder is None:
            try:
                current_ohe_encoder = joblib.load(PREPROCESSOR_PATH)
                # print(f"Preprocessor (OHE) carregado de {PREPROCESSOR_PATH}")
            except FileNotFoundError:
                raise ValueError(f"Preprocessor não encontrado em {PREPROCESSOR_PATH}. Treine primeiro ou forneça o encoder.")
        else:
            current_ohe_encoder = ohe_encoder
        
        encoded_features = current_ohe_encoder.transform(X_to_process[CATEGORICAL_FEATURES])
        ohe_feature_names = current_ohe_encoder.get_feature_names_out(CATEGORICAL_FEATURES)
        encoded_df = pd.DataFrame(encoded_features, columns=ohe_feature_names, index=X_to_process.index)
        
        if NUMERICAL_FEATURES:
            for col in NUMERICAL_FEATURES:
                if col not in X_to_process.columns:
                    # print(f"AVISO Preprocess: Num Feature '{col}' não encontrada. Adicionando como 0.")
                    X_to_process[col] = 0
                X_to_process[col] = pd.to_numeric(X_to_process[col], errors='coerce').fillna(0)
            X_processed = pd.concat([X_to_process[NUMERICAL_FEATURES].reset_index(drop=True),
                                     encoded_df.reset_index(drop=True)], axis=1)
            final_column_names_for_output = NUMERICAL_FEATURES[:] + list(ohe_feature_names)
        else:
            X_processed = encoded_df
            final_column_names_for_output = list(ohe_feature_names)

    if not fit_ohe and training_cols_list:
        missing_cols = set(training_cols_list) - set(X_processed.columns)
        for c in missing_cols:
            X_processed[c] = 0
        extra_cols = set(X_processed.columns) - set(training_cols_list)
        if extra_cols:
            # print(f"AVISO Preprocess: Colunas extras encontradas e serão removidas: {extra_cols}")
            X_processed = X_processed.drop(columns=list(extra_cols))
        X_processed = X_processed[training_cols_list]
    elif fit_ohe:
        joblib.dump(final_column_names_for_output, TRAINING_COLUMNS_PATH)
        print(f"Lista de colunas de treino ({len(final_column_names_for_output)}) salva em {TRAINING_COLUMNS_PATH}")

    if series_target is not None:
        X_train, X_val, y_train, y_val = train_test_split(
            X_processed, series_target, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=series_target
        )
        os.makedirs(out_dir_path, exist_ok=True)
        joblib.dump((X_train, y_train), os.path.join(out_dir_path, 'train_data.joblib'))
        joblib.dump((X_val, y_val), os.path.join(out_dir_path, 'val_data.joblib'))
        # print(f"Dados de treino e validação salvos em {out_dir_path}")
        return X_train, X_val, y_train, y_val, final_column_names_for_output
    else:
        return X_processed, None, final_column_names_for_output


def run_preprocessing_pipeline(raw_data_input_dir, processed_data_output_dir, models_output_dir):
    print(f"Iniciando pipeline de pré-processamento...")
    print(f"Lendo dados brutos de: {raw_data_input_dir}")
    try:
        df_jobs, df_prospects, df_applicants = load_data(raw_data_input_dir)
    except Exception as e:
        msg = f"Falha ao carregar dados: {e}"
        print(msg)
        return False, msg, None

    if df_jobs is None or df_prospects is None or df_applicants is None:
        msg = "Falha ao carregar um ou mais arquivos de dados brutos (DataFrame resultante é None)."
        print(msg)
        return False, msg, None

    print("Mesclando dados...")
    df_merged = merge_data(df_jobs, df_prospects, df_applicants)
    if df_merged is None or df_merged.empty:
        msg = "Falha ao mesclar os dados ou resultado vazio."
        print(msg)
        return False, msg, None

    print("Realizando engenharia de features...")
    try:
        X_engineered_features, y_target_series = engineer_features(df_merged)
    except Exception as e:
        msg = f"Erro durante a engenharia de features: {e}"
        print(msg)
        return False, msg, None

    print("Pré-processando dados (OHE, split) e salvando...")
    try:
        os.makedirs(processed_data_output_dir, exist_ok=True)
        os.makedirs(models_output_dir, exist_ok=True) 
        X_train, X_val, y_train, y_val, training_cols = preprocess_data_split_save(
            X_engineered_features, y_target_series,
            out_dir_path=processed_data_output_dir,
            fit_ohe=True
        )
        msg = (f"Pipeline de pré-processamento concluído. "
               f"Dados de treino/validação salvos em '{processed_data_output_dir}'. "
               f"Pré-processador salvo em '{PREPROCESSOR_PATH}'. "
               f"Colunas de treino salvas em '{TRAINING_COLUMNS_PATH}'. "
               f"Shapes: X_train: {X_train.shape}, X_val: {X_val.shape}")
        # print(msg) # Removido para não duplicar com o print do __main__
        return True, msg, training_cols # Retornar training_cols para o __main__ poder imprimir
    except Exception as e:
        msg = f"Erro durante o pré-processamento, split ou salvamento: {e}"
        print(msg)
        return False, msg, None

if __name__ == "__main__":
    raw_data_path_arg = DEFAULT_RAW_DATA_DIR
    if len(sys.argv) > 1:
        raw_data_path_arg = sys.argv[1]
    elif not os.path.isdir(DEFAULT_RAW_DATA_DIR) and not os.path.exists(DEFAULT_RAW_DATA_DIR): # Checa se é diretório ou arquivo
        # Ajuste para permitir que DEFAULT_RAW_DATA_DIR seja um arquivo se necessário, ou melhore a lógica de detecção
        print(f"AVISO: Diretório/caminho de dados brutos padrão '{DEFAULT_RAW_DATA_DIR}' não encontrado ou inválido.")
        # Determinar o nome do pacote dinamicamente para a mensagem de uso
        package_name = __package__ if __package__ else os.path.basename(os.path.dirname(__file__))
        if 'src' in package_name: # Heurística
            package_name = os.path.basename(os.path.dirname(os.path.dirname(__file__))) + '.' + package_name

        print(f"Uso: python -m {package_name}.preprocess_utils <caminho_para_dados_brutos>")
        print(f"Exemplo: python -m datathon_decision.src.preprocess_utils data/raw")
        sys.exit(1)

    os.makedirs(DEFAULT_PROCESSED_DATA_DIR, exist_ok=True)
    os.makedirs(DEFAULT_MODELS_DIR, exist_ok=True)

    success, message, training_cols_result = run_preprocessing_pipeline( # Capturar training_cols_result
        raw_data_input_dir=raw_data_path_arg,
        processed_data_output_dir=DEFAULT_PROCESSED_DATA_DIR,
        models_output_dir=DEFAULT_MODELS_DIR
    )
    print(message) # Imprime a mensagem detalhada retornada pela função
    if success and training_cols_result:
        print(f"Colunas de treinamento final ({len(training_cols_result)}): {training_cols_result[:10]}...")