import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, roc_auc_score
import logging
import sys
import os

# Adicionando o diretório pai de 'src' ao sys.path para permitir importações relativas
# Isso é importante para 'from datathon_decision.src.config import ...' funcionar
# quando o script é executado como 'python -m datathon_decision.src.model_utils ...'
# ou se o diretório do projeto 'datathon-decision' não estiver no PYTHONPATH.
# A forma como você executa ('uv run python -m ...') geralmente lida com isso.
# Se 'datathon_decision' é a raiz do seu projeto e 'src' está dentro dele.

try:
    from datathon_decision.src.config import MODEL_PATH, PREPROCESSOR_PATH, TRAINING_COLUMNS_PATH
    # As funções de preprocess_utils são necessárias para o predict_pipeline
    from datathon_decision.src.preprocess_utils import engineer_features, preprocess_data_split_save 
except ModuleNotFoundError:
    print("AVISO CRÍTICO: Falha ao importar 'config' ou 'preprocess_utils' de 'datathon_decision.src'.")
    print("Verifique seu PYTHONPATH, a estrutura do projeto ou como o script está sendo executado.")
    print("O script pode não funcionar corretamente.")
    raise


logger = logging.getLogger(__name__)
# Configuração básica de logging se este script for executado diretamente
# Ou se o logger não for configurado pelo app Flask.
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', stream=sys.stdout)


def train_model(X_train, y_train):
    """Treina um modelo RandomForestClassifier e o salva."""
    logger.info(f"Iniciando treinamento do modelo com X_train shape: {X_train.shape}")
    # Adicionado class_weight='balanced' para ajudar com classes desbalanceadas
    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)
    joblib.dump(model, MODEL_PATH)
    logger.info(f"Modelo salvo em {MODEL_PATH}")
    return model

def evaluate_model(model, X_val, y_val):
    """Avalia o modelo e retorna um dicionário de métricas."""
    logger.info(f"Avaliando modelo no conjunto de validação X_val shape: {X_val.shape}")
    y_pred = model.predict(X_val)
    y_proba = None
    if hasattr(model, 'predict_proba'):
        y_proba = model.predict_proba(X_val)[:, 1] 
    
    acc = accuracy_score(y_val, y_pred)
    prec = precision_score(y_val, y_pred, zero_division=0)
    rec = recall_score(y_val, y_pred, zero_division=0)
    f1 = f1_score(y_val, y_pred, zero_division=0)
    
    roc_auc = None
    if y_proba is not None:
        roc_auc = roc_auc_score(y_val, y_proba)
        logger.info(f"Acurácia: {acc:.3f} | Precisão: {prec:.3f} | Recall: {rec:.3f} | F1: {f1:.3f} | ROC AUC: {roc_auc:.3f}")
    else:
        logger.info(f"Acurácia: {acc:.3f} | Precisão: {prec:.3f} | Recall: {rec:.3f} | F1: {f1:.3f} | (ROC AUC não disponível)")
        
    logger.info("\nClassification Report:\n" + classification_report(y_val, y_pred, zero_division=0))
    
    metrics_dict = {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1}
    if roc_auc is not None:
        metrics_dict["roc_auc"] = roc_auc
    return metrics_dict

def predict_pipeline(input_data_dict):
    """
    Recebe um dicionário (payload JSON), processa as features e retorna a probabilidade de match.
    Esta função é destinada a ser chamada pela API para uma única predição.
    """
    try:
        logger.info(f"Carregando artefatos para predição: MODEL_PATH='{MODEL_PATH}', PREPROCESSOR_PATH='{PREPROCESSOR_PATH}', TRAINING_COLUMNS_PATH='{TRAINING_COLUMNS_PATH}'")
        model = joblib.load(MODEL_PATH)
        ohe = joblib.load(PREPROCESSOR_PATH) # OneHotEncoder salvo
        training_cols = joblib.load(TRAINING_COLUMNS_PATH) # Lista de nomes de colunas pós-OHE
        logger.info(f"Modelo, OHE e colunas de treino ({len(training_cols)}) carregados.")
        # logger.debug(f"Colunas de treino carregadas: {training_cols[:10]}...")


        df_input = pd.DataFrame([input_data_dict])
        logger.info(f"DataFrame de entrada para engineer_features (1 linha): \n{df_input.to_string()}")

        X_features_engineered, _ = engineer_features(df_input) # y_target é None aqui
        logger.info(f"Features após engineer_features (antes de OHE e alinhamento): \n{X_features_engineered.to_string()}")
        logger.info(f"Shape de X_features_engineered: {X_features_engineered.shape}")
        logger.info(f"Colunas em X_features_engineered: {X_features_engineered.columns.tolist()}")


        X_processed_for_predict, _, _ = preprocess_data_split_save(
            df_features=X_features_engineered, 
            series_target=None,             # Target é None para predição
            out_dir_path=None,              # Não salva dados de treino/val
            fit_ohe=False,                  # Usa o encoder treinado
            ohe_encoder=ohe,                # Passa o encoder carregado
            training_cols_list=training_cols # Passa a lista de colunas para alinhamento
        )
        logger.info(f"Features após preprocess_data_split_save (OHE e alinhamento com training_cols): \n{X_processed_for_predict.head().to_string()}")
        logger.info(f"Shape de X_processed_for_predict: {X_processed_for_predict.shape}")
        logger.info(f"Colunas em X_processed_for_predict ({len(X_processed_for_predict.columns)}): {X_processed_for_predict.columns.tolist()[:10]}...")


        # Checagem final de consistência das colunas (preprocess_data_split_save já deveria ter feito isso)
        if list(X_processed_for_predict.columns) != training_cols:
            logger.warning("Desalinhamento de colunas detectado em predict_pipeline APÓS preprocess_data_split_save. Isso não deveria acontecer.")
            # Tentativa de realinhar como fallback, mas indica um problema na lógica de preprocess_data_split_save
            temp_df = pd.DataFrame(columns=training_cols, index=X_processed_for_predict.index)
            for col in training_cols:
                if col in X_processed_for_predict.columns:
                    temp_df[col] = X_processed_for_predict[col]
                else:
                    temp_df[col] = 0 # Assume que colunas OHE faltantes são 0
            X_processed_for_predict = temp_df[training_cols]
            logger.warning(f"Colunas realinhadas à força. Novo shape: {X_processed_for_predict.shape}")
        
        prob_positive_class_array = model.predict_proba(X_processed_for_predict)[:, 1]
        
        # Se X_processed_for_predict tiver apenas uma linha, prob_positive_class_array será um array com um elemento
        prediction_result = float(prob_positive_class_array[0])
        logger.info(f"Probabilidade predita (classe positiva): {prediction_result}")
        return prediction_result

    except FileNotFoundError as e:
        logger.error(f"Erro CRÍTICO em predict_pipeline: Arquivo de modelo/pré-processador não encontrado. {e}", exc_info=True)
        raise 
    except KeyError as e: 
        logger.error(f"Erro de Chave em predict_pipeline (payload de entrada inválido/inesperado para engineer_features): {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Erro inesperado em predict_pipeline: {e}", exc_info=True)
        raise