import argparse
import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

MODEL_PATH = os.getenv("MODEL_PATH", "ml/model.pkl")

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", default="training", help="Phase name")
    args = parser.parse_args()
    
    train_model()
