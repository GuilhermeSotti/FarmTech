import argparse
import pandas as pd
import pickle
import os
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
import joblib

MODEL_PATH = os.getenv("MODEL_PATH", "ml/model.pkl")
ROOT = Path(__file__).resolve().parents[2]

def train_model(data_path="db/data_samples/sensors.csv"):
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    if df.empty:
        print("No data available for training")
        return
    
    X = df[['umidade', 'nutriente']].fillna(0)
    y = df['umidade'].shift(-1).fillna(0)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    
    score = model.score(X_test, y_test)
    print(f"Model trained. R² Score: {score:.4f}")
    
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model saved to {MODEL_PATH}")

def train_from_csv(csv_path: str, target_col: str, model_out: str = "models/model.joblib"):
    df = pd.read_csv(csv_path)

    df = df.dropna(subset=[target_col])
    X = df.select_dtypes(include="number").drop(columns=[target_col], errors="ignore")
    y = df[target_col]
    if len(y) < 2:
        raise ValueError("Dados insuficientes para treinar (menos de 2 amostras).")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    r2 = r2_score(y_test, preds) if len(y_test) >= 2 else None
    mse = mean_squared_error(y_test, preds) if len(y_test) >= 2 else None
    Path(model_out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_out)
    return {"r2": r2, "mse": mse, "model_path": model_out}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", default="training", help="Phase name")
    args = parser.parse_args()
    
    train_model()
