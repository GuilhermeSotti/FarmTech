from sklearn.ensemble import RandomForestClassifier
import numpy as np

class CropPredictor:
    def __init__(self):
        self.model = RandomForestClassifier()
        
    def train(self, training_data: list[dict]) -> float:
        X = np.array([[d['temperature'], d['humidity'], d['soil_moisture']] 
                     for d in training_data])
        y = np.array([d['crop_yield'] for d in training_data])
        
        self.model.fit(X, y)
        return self.model.score(X, y)
    
    def predict(self, data: dict) -> float:
        features = np.array([[
            data['temperature'],
            data['humidity'],
            data['soil_moisture']
        ]])
        return float(self.model.predict(features)[0])
