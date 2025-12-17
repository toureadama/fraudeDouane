from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
import asyncio
from douane_feat import COD_BANQUE, CODE_DECLARANT, CODE_NATURE_COLIS, CODE_OPERATEUR, CODE_PORT_CHARG, IDEN_MOY_TRANSP_ARRIVE, PROVENANCE


#model = joblib.load("C:/Users/HP 820 G3/Desktop/DOUANES CI/ANALYSE CONTENTIEUX/models/fraud_detection_model.pkl")
model = joblib.load("fraud_detection_model.pkl")


features_imports = ['CODE_DECLARANT', 'CODE_OPERATEUR', 'PROVENANCE', 'CODE_NATURE_COLIS',
                    'CODE_PORT_CHARG', 'IDEN_MOY_TRANSP_ARRIVE', 'COD_BANQUE']

class_names = ['EXC', 'FDE', 'FDV', 'NON_FRAUDE']

app = FastAPI(title="Fraud Detection API")

# CORS (frontend React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Mock metadata (à remplacer par DB ou fichier) ----------
METADATA = {
    "CODE_DECLARANT": CODE_DECLARANT,
    "CODE_OPERATEUR": CODE_OPERATEUR,
    "PROVENANCE": PROVENANCE,
    "CODE_NATURE_COLIS": CODE_NATURE_COLIS,
    "CODE_PORT_CHARG": CODE_PORT_CHARG,
    "IDEN_MOY_TRANSP_ARRIVE": IDEN_MOY_TRANSP_ARRIVE,
    "COD_BANQUE": COD_BANQUE
}

# --------- Input schema ----------
class PredictionInput(BaseModel):
    CODE_DECLARANT: str
    CODE_OPERATEUR: str
    PROVENANCE: str
    CODE_NATURE_COLIS: str
    CODE_PORT_CHARG: str
    IDEN_MOY_TRANSP_ARRIVE: str
    COD_BANQUE: str

# --------- Ouput schema ----------
class PredictionResponse(BaseModel):
    prediction: str
    probability: float

# --------- Routes ----------
@app.get("/")
def read_root():
    return {"message": "Fraud Detection API is running."}

@app.get("/metadata")
async def get_metadata():
    return METADATA

@app.post("/predict")
def predict(data: PredictionInput):

    features = pd.DataFrame(list([data.CODE_DECLARANT, 
                                 data.CODE_OPERATEUR, 
                                 data.PROVENANCE,
                                 data.CODE_NATURE_COLIS, 
                                 data.CODE_PORT_CHARG, 
                                 data.IDEN_MOY_TRANSP_ARRIVE, 
                                 data.COD_BANQUE]), 
                            index=features_imports).T
    
    pre_prediction = model.predict(features)
    prediction_class = class_names[int(pre_prediction[0])]
    probability = round(max(model.predict_proba(features)[0]), 2)
    prediction = prediction_class if (probability > 0.7) & (prediction_class in ['EXC', 'FDE', 'FDV']) else "NON_FRAUDE"

    return {
        "prediction": prediction,
        "probability": probability
    }
