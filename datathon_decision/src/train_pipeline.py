import joblib
from datathon_decision.src.config import PROCESSED_DATA_DIR
from datathon_decision.src.model_utils import train_model, evaluate_model

if __name__ == "__main__":
    print("Carregando dados de treino e validação...")
    train_path = PROCESSED_DATA_DIR / "train_data.joblib"
    val_path = PROCESSED_DATA_DIR / "val_data.joblib"
    X_train, y_train = joblib.load(train_path)
    X_val, y_val = joblib.load(val_path)
    print(f"Shapes: X_train={X_train.shape}, y_train={y_train.shape}, X_val={X_val.shape}, y_val={y_val.shape}")

    print("Treinando modelo RandomForest...")
    model = train_model(X_train, y_train)

    print("Avaliando modelo no conjunto de validação...")
    metrics = evaluate_model(model, X_val, y_val)
    print("Métricas de validação:", metrics) 