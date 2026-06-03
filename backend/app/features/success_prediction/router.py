from fastapi import APIRouter, HTTPException
from backend.app.features.success_prediction.schemas import StartupInputSchema, PredictionResponseSchema
from backend.app.features.success_prediction.preprocess import clean_and_scale_input
from backend.app.features.success_prediction.predict import execute_prediction

router = APIRouter()

@router.post("/validate", response_model=PredictionResponseSchema)
async def validate_startup_success(payload: StartupInputSchema):
    try:
        input_data = payload.dict()
        processed_data = clean_and_scale_input(input_data)
        probability = execute_prediction(processed_data)
        label = "Success" if probability >= 0.5 else "Failure"
        
        return PredictionResponseSchema(
            success_probability=round(probability, 4),
            prediction_label=label,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")