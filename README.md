# 🏦 AI-Based Loan Approval & Risk Assessment Platform (100% Complete)

An end-to-end Machine Learning and Business Intelligence platform designed to automate loan application evaluations, estimate default probabilities, score risk tiers, and generate compliance reports.

---

## 📌 Project Architecture & 100% Completion Overview
This codebase represents **100% Completion across all 5 Roadmap Phases**:

* **Phase 1 (Frontend UI)**: Interactive Streamlit web interface (`app/frontend.py`) with executive dashboards, form validation, and dark fintech theme.
* **Phase 2 (Database & REST API)**: Relational SQLAlchemy engine (`app/database.py`) and FastAPI gateway (`app/main.py`) serving `/predict`, `/applications`, `/metrics`, `/feature-importance`, and `/export-bi`.
* **Phase 3 (Machine Learning Engine)**: Gradient-boosted decision tree pipeline (`train.py`) trained using XGBoost & Scikit-learn with 97.6% testing accuracy, saved to `models/loan_model_pipeline.joblib`.
* **Phase 4 (BI & Power BI Integration)**: Plotly risk scatter plots, XGBoost feature importances, ReportLab PDF Credit Memo generation (`app/report.py`), and dataset exports to Excel/CSV for Power BI (`export_powerbi_dataset.py`).
* **Phase 5 (Testing & Security)**: Automated pytest test suite (`tests/test_system.py`) covering preprocessors, API endpoints, DB operations, and PDF compilation.

---

## 🚀 How to Run & Test

### Option 1: Direct Mode (Streamlit Only)
Open a terminal in this folder and run:
```powershell
python -m streamlit run app/frontend.py
```

### Option 2: Full Enterprise Gateway Mode (API + Streamlit)
1. Launch FastAPI backend:
   ```powershell
   uvicorn app.main:app --reload
   ```
2. Launch Streamlit UI:
   ```powershell
   python -m streamlit run app/frontend.py
   ```

### Run Automated Unit Tests
```powershell
python -m pytest tests/test_system.py
```

### Export Power BI Datasets
```powershell
python export_powerbi_dataset.py
```
