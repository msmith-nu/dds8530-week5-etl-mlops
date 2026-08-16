"""FastAPI service exposing /health, /predict, and /metrics."""

import joblib
from fastapi import FastAPI
import pandas as pd
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
from src import config

# load the model
model = joblib.load(config.MODEL_PATH)

# create the app
app = FastAPI(title="Major Earthquake Classifier")

# define what happens when GET asks about health
@app.get("/health")
def health():
    """Returns that status is ok and what model was used"""
    return {"status": "ok", "model_type": model.steps[-1][0]}

# define class for getting event features as input
class EventFeatures(BaseModel):
    depth: float
    latitude: float
    longitude: float
    nst: float
    gap: float
    dmin: float
    rms: float


@app.post("/predict")
def predict(event: EventFeatures):
    """Takes input event and predict probability"""

    # store the incoming event
    df = pd.DataFrame([event.model_dump()])[config.FEATURES]

    # calcualte probability with model
    prob = float(model.predict_proba(df)[0,1])

    # return probability and true or false
    return {"probability": prob, "is_significant": prob >= 0.5}

# use instrumentator to track metrics for the API
Instrumentator().instrument(app).expose(app)