from fastapi import APIRouter, HTTPException
from app.models.fase2.predictor import CropPredictor

router = APIRouter(prefix="/model", tags=["model"])

@router.post("/train")
async def train_model(training_data: list[dict]):
    try:
        predictor = CropPredictor()
        accuracy = predictor.train(training_data)
        return {"message": "Model trained successfully", "accuracy": accuracy}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict")
async def predict(data: dict):
    try:
        predictor = CropPredictor()
        prediction = predictor.predict(data)
        return {"prediction": prediction}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
