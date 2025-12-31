from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import pymysql
from database import HOST, USER, PORT, PASSWORD, DATABASE

# Liste des tables à construire
COD_BANQUE = []
CODE_DECLARANT = []
CODE_NATURE_COLIS = []
CODE_OPERATEUR = []
CODE_PORT_CHARG = []
IDEN_MOY_TRANSP_ARRIVE = []
PROVENANCE  = []
list_table = ["COD_BANQUE", "CODE_DECLARANT", "CODE_NATURE_COLIS", "CODE_OPERATEUR",
              "CODE_PORT_CHARG", "IDEN_MOY_TRANSP_ARRIVE", "PROVENANCE"]
list_table_name = [COD_BANQUE, CODE_DECLARANT, CODE_NATURE_COLIS, CODE_OPERATEUR,
                   CODE_PORT_CHARG, IDEN_MOY_TRANSP_ARRIVE, PROVENANCE]

def create_list(table_i):
    # Define the SQL query to select all records
    query = f"SELECT * FROM {list_table[table_i]}"

    # Execute the query
    cursor.execute(query)

    # Fetch all the results
    result = cursor.fetchall()
    list_table_name[table_i] = [row[1] for row in result]

    return  list_table_name[table_i]

try:
    # Establish a connection
    conn = pymysql.connect(
        host=HOST,
        user=USER,
        port=PORT,
        password=PASSWORD,
        database=DATABASE
        )

    if conn.open:
        print("Connection to MySQL database established successfully.")
        
    # Create a cursor object
    cursor = conn.cursor()

    for table_i in range(len(list_table_name)):
        list_table_name[table_i] = create_list(table_i)
        
except pymysql.MySQLError as e:
    print(f"Error connecting to MySQL database: {e}")

finally:
    # Close the cursor and connection (important cleanup step)
    if 'cursor' in locals() and cursor is not None:
        cursor.close()
    if 'conn' in locals() and conn is not None:
        conn.close()


# Load model
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
def get_metadata():
    return METADATA

@app.post("/predict")
def predict(data: PredictionInput):

    features = pd.DataFrame(list([data.CODE_DECLARANT.upper(), 
                                 data.CODE_OPERATEUR.upper(), 
                                 data.PROVENANCE.upper(),
                                 data.CODE_NATURE_COLIS.upper(), 
                                 data.CODE_PORT_CHARG.upper(), 
                                 data.IDEN_MOY_TRANSP_ARRIVE.upper(), 
                                 data.COD_BANQUE.upper()]), 
                            index=features_imports).T
    
    pre_prediction = model.predict(features)
    prediction_class = class_names[int(pre_prediction[0])]
    probability = round(max(model.predict_proba(features)[0]), 2)
    prediction = prediction_class if (probability > 0.7) & (prediction_class in ['EXC', 'FDE', 'FDV']) else "NON_FRAUDE"

    return {
        "prediction": prediction,
        "probability": probability
    }
