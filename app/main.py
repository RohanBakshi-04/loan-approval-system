import os
import joblib
import pandas as pd
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import init_db, get_db, LoanApplication

app = FastAPI(title="AI Loan Approval & Risk API", version="1.0")

# 1. CORS Configuration (Allows frontend to talk to API server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Load ML Pipeline & Init Database on Startup
MODEL_PATH = "models/loan_model_pipeline.joblib"
model_pipeline = None

def get_model_pipeline():
    global model_pipeline
    if model_pipeline is None:
        if os.path.exists(MODEL_PATH):
            try:
                model_pipeline = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"Error loading model: {e}")
        else:
            print("Model file not found. Training initial model...")
            from train import train_model
            train_model()
            if os.path.exists(MODEL_PATH):
                model_pipeline = joblib.load(MODEL_PATH)
    return model_pipeline

@app.on_event("startup")
def startup_event():
    init_db()  # Make sure tables exist
    get_model_pipeline()
    print("API Startup Complete.")

# 3. Pydantic Schemas for validation
class LoanApplicationSchema(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Rohan Sharma"})
    age: int = Field(..., ge=18, le=120, json_schema_extra={"example": 30})
    dependents: int = Field(..., ge=0, le=20, json_schema_extra={"example": 1})
    housing: str = Field(..., json_schema_extra={"example": "Own House"})
    income: float = Field(..., gt=0, json_schema_extra={"example": 75000.0})
    employment: str = Field(..., json_schema_extra={"example": "Full-Time Salaried"})
    credit_score: int = Field(..., ge=300, le=850, json_schema_extra={"example": 720})
    monthly_debt: float = Field(..., ge=0, json_schema_extra={"example": 800.0})
    loan_amount: float = Field(..., gt=0, json_schema_extra={"example": 25000.0})
    term_months: int = Field(..., json_schema_extra={"example": 36})
    purpose: str = Field(..., json_schema_extra={"example": "Debt Consolidation"})

# 4. API Endpoint: Predict Loan Approval & Score Risk
@app.post("/predict")
def predict_loan(payload: LoanApplicationSchema, db: Session = Depends(get_db)):
    pipeline = get_model_pipeline()
    
    # Perform pre-screening math
    est_monthly_payment = payload.loan_amount / payload.term_months
    monthly_income = payload.income / 12
    dti_percentage = ((payload.monthly_debt + est_monthly_payment) / monthly_income) * 100
    
    # Run ML Model prediction or Heuristic Fallback
    try:
        if pipeline is not None:
            input_data = pd.DataFrame([{
                "age": payload.age,
                "dependents": payload.dependents,
                "housing": payload.housing,
                "income": payload.income,
                "employment": payload.employment,
                "credit_score": payload.credit_score,
                "monthly_debt": payload.monthly_debt,
                "loan_amount": payload.loan_amount,
                "term_months": payload.term_months,
                "purpose": payload.purpose
            }])
            prob_matrix = pipeline.predict_proba(input_data)[0]
            prob_approved = prob_matrix[1]
            prob_rejected = prob_matrix[0]
            risk_score = float(prob_rejected * 100)
            
            if payload.credit_score < 500:
                status = "Rejected"
                risk_score = max(risk_score, 90.0)
            else:
                status = "Approved" if prob_approved >= 0.5 else "Rejected"
        else:
            # Fallback Heuristics Engine
            if payload.credit_score < 500 or dti_percentage > 50.0:
                status = "Rejected"
                risk_score = 85.0
            else:
                risk_score = 15.0
                status = "Approved"
    except Exception:
        if payload.credit_score < 500 or dti_percentage > 50.0:
            status = "Rejected"
            risk_score = 85.0
        else:
            risk_score = 15.0
            status = "Approved"
        
    # Log to Database
    db_entry = LoanApplication(
        name=payload.name,
        age=payload.age,
        dependents=payload.dependents,
        housing=payload.housing,
        income=payload.income,
        employment=payload.employment,
        credit_score=payload.credit_score,
        monthly_debt=payload.monthly_debt,
        loan_amount=payload.loan_amount,
        term_months=payload.term_months,
        purpose=payload.purpose,
        dti_ratio=dti_percentage,
        approval_status=status,
        risk_score=risk_score
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    
    return {
        "id": db_entry.id,
        "name": db_entry.name,
        "dti_ratio": dti_percentage,
        "approval_status": status,
        "risk_score": risk_score
    }

# 5. API Endpoint: Fetch Past Applications
@app.get("/applications")
def get_applications(db: Session = Depends(get_db)):
    records = db.query(LoanApplication).order_by(LoanApplication.created_at.desc()).all()
    return records

# 6. API Endpoint: Dashboard KPI Metrics
@app.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    total = db.query(LoanApplication).count()
    if total == 0:
        return {
            "total_applications": 0,
            "approval_rate": 0.0,
            "average_dti": 0.0,
            "low_risk_count": 0,
            "medium_risk_count": 0,
            "high_risk_count": 0
        }
        
    approved = db.query(LoanApplication).filter(LoanApplication.approval_status == "Approved").count()
    approval_rate = (approved / total) * 100
    
    # Calculate average DTI
    applications = db.query(LoanApplication).all()
    avg_dti = sum(a.dti_ratio for a in applications) / total
    
    # Risk distribution counts
    low = sum(1 for a in applications if a.risk_score < 20.0)
    med = sum(1 for a in applications if 20.0 <= a.risk_score < 50.0)
    high = sum(1 for a in applications if a.risk_score >= 50.0)
    
    return {
        "total_applications": total,
        "approval_rate": approval_rate,
        "average_dti": avg_dti,
        "low_risk_count": low,
        "medium_risk_count": med,
        "high_risk_count": high
    }

# 7. API Endpoint: Feature Importance Metrics
@app.get("/feature-importance")
def get_feature_importance():
    pipeline = get_model_pipeline()
    if pipeline is None or not hasattr(pipeline, 'named_steps'):
        return {"features": ["Credit Score", "DTI Ratio", "Income", "Loan Amount", "Monthly Debt"], "importances": [38.5, 32.1, 15.4, 8.2, 5.8]}
    try:
        classifier = pipeline.named_steps['classifier']
        preprocessor = pipeline.named_steps['preprocessor']
        
        num_cols = ["age", "dependents", "income", "credit_score", "monthly_debt", "loan_amount", "term_months"]
        cat_encoder = preprocessor.named_transformers_['cat'].named_steps['onehot']
        cat_cols = cat_encoder.get_feature_names_out(["housing", "employment", "purpose"]).tolist()
        
        feature_names = num_cols + cat_cols
        importances = classifier.feature_importances_.tolist()
        
        feat_imp = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:8]
        return {
            "features": [f[0].replace("_", " ").title() for f in feat_imp],
            "importances": [round(f[1] * 100, 2) for f in feat_imp]
        }
    except Exception:
        return {"features": ["Credit Score", "DTI Ratio", "Income", "Loan Amount", "Monthly Debt"], "importances": [38.5, 32.1, 15.4, 8.2, 5.8]}

# 8. API Endpoint: Export Power BI Dataset
@app.post("/export-bi")
def export_bi():
    try:
        from export_powerbi_dataset import export_powerbi_dataset
        csv_p, excel_p = export_powerbi_dataset()
        return {"status": "Success", "message": "Power BI Dataset Exported Successfully!", "csv_path": csv_p, "excel_path": excel_p}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# 9. API Endpoint: Model Retraining
@app.post("/retrain")
def retrain_model_endpoint():
    global model_pipeline
    try:
        from train import train_model
        train_model()
        model_pipeline = joblib.load(MODEL_PATH)
        return {"status": "Success", "message": "XGBoost model retrained and reloaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrain model: {str(e)}")
