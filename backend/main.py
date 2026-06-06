from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from backend.model import predict_personality, predict_multitask_scores, predict_review_analysis
except ModuleNotFoundError:
    from model import predict_personality, predict_multitask_scores, predict_review_analysis

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Backend đang chạy"}

class InputData(BaseModel):
    text: str

@app.post("/predict")
def predict_api(data: InputData):
    # Return raw logits for personality traits
    result = predict_personality(data.text, return_logits=True)
    return result

@app.post("/multitask-predict")
def multitask_predict_api(data: InputData):
    """Predict sentiment and helpfulness using PhoBERT multitask model."""
    result = predict_multitask_scores(data.text)
    return result


@app.post("/analyze-review")
def analyze_review_api(data: InputData):
    """Predict personality, multitask scores, and cluster for a review."""
    result = predict_review_analysis(data.text)
    return result
 