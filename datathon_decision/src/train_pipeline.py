import joblib
from datathon_decision.src.config import PROCESSED_DATA_DIR
from datathon_decision.src.model_utils import train_model, evaluate_model
import os
import glob

print("🔍 Debug: Arquivos disponíveis")
print("Diretório processed:", os.path.exists("datathon_decision/data/processed"))
print("Arquivos em processed:")
if os.path.exists("datathon_decision/data/processed"):
    files = glob.glob("datathon_decision/data/processed/*")
    for f in files:
        print(f"  - {f}")
else:
    print("  (diretório não existe)")

print("\nDiretório models:", os.path.exists("datathon_decision/models"))
print("Arquivos em models:")
if os.path.exists("datathon_decision/models"):
    files = glob.glob("datathon_decision/models/*")
    for f in files:
        print(f"  - {f}")
else:
    print("  (diretório não existe)")

# Depois continue com o código normal
train_path = "datathon_decision/data/processed/train_data.joblib"
print(f"\n🎯 Procurando arquivo: {train_path}")
print(f"Existe? {os.path.exists(train_path)}")

if os.path.exists(train_path):
    print("✅ Arquivo encontrado, continuando...")
else:
    print("❌ Arquivo não encontrado!")
    exit(1)

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