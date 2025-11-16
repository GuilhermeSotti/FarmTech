import pickle
import os
import json
from datetime import datetime

MODEL_PATH = os.getenv("MODEL_PATH", "ml/model.pkl")

def load_model():
    if not os.path.exists(MODEL_PATH):
        print(f"Model not found at {MODEL_PATH}. Train first.")
        return None
    with open(MODEL_PATH, 'rb') as f:
        return pickle.load(f)

def predict(umidade, nutriente):
    model = load_model()
    if model is None:
        return None
    prediction = model.predict([[umidade, nutriente]])[0]
    return prediction

if __name__ == '__main__':
    result = predict(45.0, 12.0)
    if result:
        output = {
            "timestamp": datetime.now().isoformat(),
            "input": {"umidade": 45.0, "nutriente": 12.0},
            "prediction": float(result)
        }
        print(json.dumps(output, indent=2))
