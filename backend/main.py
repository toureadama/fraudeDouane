import logging
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import joblib
import pandas as pd
import pymysql
from datetime import datetime
import secrets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#Database connection details (replace with your own)
HOST = secrets.HOST
USER = secrets.USER
PORT = secrets.PORT
PASSWORD = secrets.PASSWORD 
DATABASE = secrets.DATABASE

# Tables to fetch
TABLES = [
    "COD_BANQUE", "CODE_DECLARANT", "CODE_NATURE_COLIS", "CODE_OPERATEUR",
    "CODE_PORT_CHARG", "IDEN_MOY_TRANSP_ARRIVE", "PROVENANCE"
]

# Ordered feature names expected by the model
FEATURES_IMPORTS = ['CODE_DECLARANT', 'CODE_OPERATEUR', 'PROVENANCE', 'CODE_NATURE_COLIS',
                    'CODE_PORT_CHARG', 'IDEN_MOY_TRANSP_ARRIVE', 'COD_BANQUE']

CLASS_NAMES = ['EXC', 'FDE', 'FDV', 'NON_FRAUDE']

# Name of table to store predictions and input data
PREDICTIONS_TABLE = "PREDICTIONS"

# Globals to be populated on startup
METADATA: Dict[str, List[str]] = {}
model: Optional[Any] = None

app = FastAPI(title="Fraud Detection API")

# CORS (frontend React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def fetch_table_values(table_name: str) -> List[str]:
    """
    Query the DB and return the second column values for the given table.
    Fallback to an empty list on any error.
    """
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(host=HOST, user=USER, port=PORT, password=PASSWORD, database=DATABASE)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM `{table_name}`")
        rows = cursor.fetchall()
        values = [row[1] for row in rows if len(row) > 1]
        return values
    except Exception as e:
        logger.exception("Error fetching values for table %s: %s", table_name, e)
        return []
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception:
            pass


def ensure_predictions_table():
    """Create predictions table if it does not exist."""
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS `{PREDICTIONS_TABLE}` (
      id INT AUTO_INCREMENT PRIMARY KEY,
      datetime_utc DATETIME NOT NULL,
      ip_address VARCHAR(45),
      CODE_DECLARANT VARCHAR(255),
      CODE_OPERATEUR VARCHAR(255),
      PROVENANCE VARCHAR(255),
      CODE_NATURE_COLIS VARCHAR(255),
      CODE_PORT_CHARG VARCHAR(255),
      IDEN_MOY_TRANSP_ARRIVE VARCHAR(255),
      COD_BANQUE VARCHAR(255),
      prediction VARCHAR(50),
      probability FLOAT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(host=HOST, user=USER, port=PORT, password=PASSWORD, database=DATABASE)
        cursor = conn.cursor()
        cursor.execute(create_sql)
        conn.commit()
    except Exception as e:
        logger.exception("Failed to ensure predictions table exists: %s", e)
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception:
            pass


def log_prediction_to_db(payload: Dict[str, str], prediction: str, probability: float, ip_address: str):
    """Insert a prediction record into DB. Fail silently (log only) if insertion fails."""
    insert_sql = f"""
    INSERT INTO `{PREDICTIONS_TABLE}` (
      datetime_utc, ip_address,
      CODE_DECLARANT, CODE_OPERATEUR, PROVENANCE, CODE_NATURE_COLIS,
      CODE_PORT_CHARG, IDEN_MOY_TRANSP_ARRIVE, COD_BANQUE,
      prediction, probability
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        datetime.utcnow(),
        ip_address,
        payload.get("CODE_DECLARANT", ""),
        payload.get("CODE_OPERATEUR", ""),
        payload.get("PROVENANCE", ""),
        payload.get("CODE_NATURE_COLIS", ""),
        payload.get("CODE_PORT_CHARG", ""),
        payload.get("IDEN_MOY_TRANSP_ARRIVE", ""),
        payload.get("COD_BANQUE", ""),
        prediction,
        probability,
    )
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(host=HOST, user=USER, port=PORT, password=PASSWORD, database=DATABASE)
        cursor = conn.cursor()
        cursor.execute(insert_sql, params)
        conn.commit()
    except Exception as e:
        logger.exception("Failed to log prediction to DB: %s", e)
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception:
            pass


@app.on_event("startup")
def load_resources():
    global METADATA, model
    # Load metadata from DB
    logger.info("Loading metadata from DB...")
    metadata = {}
    for t in TABLES:
        metadata[t] = fetch_table_values(t)
    METADATA = metadata
    logger.info("Metadata loaded: %s", {k: len(v) for k, v in METADATA.items()})

    # Ensure predictions table exists
    ensure_predictions_table()

    # Load model
    try:
        logger.info("Loading model...")
        model = joblib.load("fraud_detection_model.pkl")
        logger.info("Model loaded.")
    except Exception as e:
        model = None
        logger.exception("Failed to load model: %s", e)


# --------- Input schema with normalization ----------
class PredictionInput(BaseModel):
    CODE_DECLARANT: str
    CODE_OPERATEUR: str
    PROVENANCE: str
    CODE_NATURE_COLIS: str
    CODE_PORT_CHARG: str
    IDEN_MOY_TRANSP_ARRIVE: str
    COD_BANQUE: str

    @validator("*", pre=True)
    def normalize(cls, v):
        if v is None:
            return ""
        return str(v).strip().upper()


# --------- Ouput schema ----------
class PredictionResponse(BaseModel):
    prediction: str
    probability: float


class PredictionLog(BaseModel):
    id: int
    datetime_utc: datetime
    ip_address: Optional[str]
    CODE_DECLARANT: Optional[str]
    CODE_OPERATEUR: Optional[str]
    PROVENANCE: Optional[str]
    CODE_NATURE_COLIS: Optional[str]
    CODE_PORT_CHARG: Optional[str]
    IDEN_MOY_TRANSP_ARRIVE: Optional[str]
    COD_BANQUE: Optional[str]
    prediction: Optional[str]
    probability: Optional[float]


class PagedLogs(BaseModel):
    total: int
    logs: List[PredictionLog]


# --------- Routes ----------
@app.get("/", response_model=Dict[str, str])
def read_root():
    return {"message": "Fraud Detection API is running."}


@app.get("/metadata", response_model=Dict[str, List[str]])
def get_metadata():
    return METADATA


@app.post("/predict", response_model=PredictionResponse)
def predict(data: PredictionInput, request: Request):
    global model
    if model is None:
        logger.error("Prediction requested but model is not loaded.")
        raise HTTPException(status_code=503, detail="Model not available.")

    # Build DataFrame ensuring correct ordering of features
    payload = {k: getattr(data, k) for k in FEATURES_IMPORTS}
    features = pd.DataFrame([payload], columns=FEATURES_IMPORTS)

    try:
        proba = model.predict_proba(features)[0]
        pred_idx = int(model.predict(features)[0])
        prediction_class = CLASS_NAMES[pred_idx]
        probability = float(round(max(proba), 2))
        prediction = prediction_class if (probability > 0.7 and prediction_class in ['EXC', 'FDE', 'FDV']) else "NON_FRAUDE"
    except Exception as e:
        logger.exception("Prediction error: %s", e)
        raise HTTPException(status_code=500, detail="Prediction failed.")

    # Get client IP (respect X-Forwarded-For if present)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
    else:
        client = request.client
        ip = client.host if client is not None else "unknown"

    # Log prediction (errors logged but do not affect response)
    try:
        log_prediction_to_db(payload, prediction, probability, ip)
    except Exception:
        logger.exception("Unexpected error while logging prediction.")

    return {"prediction": prediction, "probability": probability}


@app.get("/logs", response_model=PagedLogs)
def get_logs(page: int = 1, size: int = 20):
    """
    Return paginated logs ordered by newest first.
    page: 1-based page number
    size: page size
    """
    if page < 1 or size < 1:
        raise HTTPException(status_code=400, detail="page and size must be >= 1")

    offset = (page - 1) * size
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(host=HOST, user=USER, port=PORT, password=PASSWORD, database=DATABASE)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM `{PREDICTIONS_TABLE}`")
        total = cursor.fetchone()[0] or 0

        select_sql = f"""
        SELECT id, datetime_utc, ip_address,
               CODE_DECLARANT, CODE_OPERATEUR, PROVENANCE, CODE_NATURE_COLIS,
               CODE_PORT_CHARG, IDEN_MOY_TRANSP_ARRIVE, COD_BANQUE,
               prediction, probability
        FROM `{PREDICTIONS_TABLE}`
        ORDER BY id DESC
        LIMIT %s OFFSET %s
        """
        cursor.execute(select_sql, (size, offset))
        rows = cursor.fetchall()
        logs: List[Dict[str, Any]] = []
        for r in rows:
            logs.append({
                "id": r[0],
                "datetime_utc": r[1],
                "ip_address": r[2],
                "CODE_DECLARANT": r[3],
                "CODE_OPERATEUR": r[4],
                "PROVENANCE": r[5],
                "CODE_NATURE_COLIS": r[6],
                "CODE_PORT_CHARG": r[7],
                "IDEN_MOY_TRANSP_ARRIVE": r[8],
                "COD_BANQUE": r[9],
                "prediction": r[10],
                "probability": r[11],
            })
        return {"total": total, "logs": logs}
    except Exception as e:
        logger.exception("Failed to fetch logs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch logs.")
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception:
            pass
