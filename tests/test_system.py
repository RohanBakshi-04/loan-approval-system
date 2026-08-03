import os
import pytest
import pandas as pd
import joblib
from fastapi.testclient import TestClient

from app.database import init_db, SessionLocal, LoanApplication
from app.main import app
from app.report import generate_pdf_report
from types import SimpleNamespace

client = TestClient(app)

def test_database_initialization():
    """Verify database schema creation and table connection."""
    init_db()
    db = SessionLocal()
    count = db.query(LoanApplication).count()
    assert count >= 0
    db.close()

def test_model_pipeline_exists():
    """Verify trained XGBoost model pipeline file exists."""
    model_path = "models/loan_model_pipeline.joblib"
    if not os.path.exists(model_path):
        from train import train_model
        train_model()
    assert os.path.exists(model_path)
    
    pipeline = joblib.load(model_path)
    assert pipeline is not None

def test_api_predict_endpoint_approved():
    """Test API prediction endpoint with low-risk applicant parameters."""
    payload = {
        "name": "Test Approved Applicant",
        "age": 35,
        "dependents": 1,
        "housing": "Own House",
        "income": 120000.0,
        "employment": "Full-Time Salaried",
        "credit_score": 780,
        "monthly_debt": 400.0,
        "loan_amount": 20000.0,
        "term_months": 36,
        "purpose": "Home Improvement"
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["approval_status"] == "Approved"
    assert data["risk_score"] < 50.0

def test_api_predict_endpoint_rejected():
    """Test API prediction endpoint with high-risk applicant parameters."""
    payload = {
        "name": "Test Rejected Applicant",
        "age": 22,
        "dependents": 0,
        "housing": "Rented Apartment",
        "income": 20000.0,
        "employment": "Unemployed / Student",
        "credit_score": 450,
        "monthly_debt": 900.0,
        "loan_amount": 50000.0,
        "term_months": 12,
        "purpose": "Personal Expense"
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["approval_status"] == "Rejected"
    assert data["risk_score"] >= 50.0

def test_api_metrics_endpoint():
    """Test API dashboard metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_applications" in data
    assert "approval_rate" in data

def test_pdf_report_generation():
    """Test ReportLab PDF credit memo generator."""
    sample_app = SimpleNamespace(
        id=999,
        name="PDF Test Applicant",
        age=30,
        dependents=1,
        housing="Own House",
        employment="Full-Time Salaried",
        income=80000.0,
        loan_amount=25000.0,
        term_months=36,
        credit_score=720,
        dti_ratio=18.5,
        approval_status="Approved",
        risk_score=12.4
    )
    pdf_buffer = generate_pdf_report(sample_app)
    assert pdf_buffer is not None
    pdf_bytes = pdf_buffer.getvalue()
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
