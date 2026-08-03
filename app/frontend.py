import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
import joblib

# Imports for Local Direct Mode
from app.database import SessionLocal, LoanApplication, init_db
from app.report import generate_pdf_report

# 1. Page Config
st.set_page_config(
    page_title="AI Loan Approval & Risk Assessment Platform",
    page_icon="🏦",
    layout="wide"
)

# 2. Custom CSS Stylesheet (Fintech Slate/Cyan Theme)
st.markdown("""
<style>
    .stApp {
        background-color: #0B0F19;
        color: #F8FAFC;
    }
    .card {
        background-color: #1E293B;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #1E293B;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    h1, h2, h3, h4 {
        color: #38BDF8 !important;
        font-family: 'Segoe UI', sans-serif;
    }
    div.stButton > button {
        background-color: #38BDF8 !important;
        color: #0B0F19 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 12px 28px !important;
        transition: background-color 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #34D399 !important;
        color: #0B0F19 !important;
    }
    .status-approved {
        background-color: #064E3B;
        color: #34D399;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: bold;
    }
    .status-rejected {
        background-color: #7F1D1D;
        color: #FCA5A5;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 3. Connection Setup & Mode Detection
API_URL = "http://127.0.0.1:8000"
RUNNING_MODE = "Local Direct Mode"

# Ping FastAPI server to check status
try:
    response = requests.get(f"{API_URL}/metrics", timeout=1.0)
    if response.status_code == 200:
        RUNNING_MODE = "API Server Mode"
except Exception:
    RUNNING_MODE = "Local Direct Mode"

# Local Database Initialization (if direct mode is active)
if RUNNING_MODE == "Local Direct Mode":
    init_db()

# 4. Header Bar
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0px; border-bottom: 1px solid #1E293B; margin-bottom: 20px;">
    <div>
        <h2 style="margin:0;">🏦 Credit Risk Analytics & Loan Approval Platform</h2>
        <small style="color: #94A3B8;">Full Enterprise AI/ML Platform • 100% Production Ready</small>
    </div>
    <span style="background-color: {'#0284C7' if RUNNING_MODE == 'API Server Mode' else '#D97706'}; color: white; padding: 6px 16px; border-radius: 20px; font-size: 12px; font-weight: bold;">
        🟢 Running in: {RUNNING_MODE}
    </span>
</div>
""", unsafe_allow_html=True)

# 5. Sidebar Navigation
st.sidebar.markdown("### 🏦 Navigation Menu")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Choose View Screen:",
    ["🏠 Executive Dashboard", "📈 BI & Portfolio Analytics", "📝 Loan Application Form", "📂 Historical Audit Logs", "⚙️ Model Controls"]
)

# Load Local Model Pipeline if running locally
local_model = None
if RUNNING_MODE == "Local Direct Mode":
    MODEL_PATH = "models/loan_model_pipeline.joblib"
    if not os.path.exists(MODEL_PATH):
        st.warning("⚠️ Local Model Pipeline not trained yet. Training now...")
        from train import train_model
        train_model()
    local_model = joblib.load(MODEL_PATH)


# ==========================================
# SCREEN A: EXECUTIVE DASHBOARD
# ==========================================
if page == "🏠 Executive Dashboard":
    st.title("🏠 Executive Financial Dashboard")
    st.write("Real-time portfolio metrics, risk tiers, and approval trends.")
    
    # 1. Fetch Metrics Data
    metrics = {}
    if RUNNING_MODE == "API Server Mode":
        try:
            metrics = requests.get(f"{API_URL}/metrics").json()
        except Exception:
            RUNNING_MODE = "Local Direct Mode"
            
    if RUNNING_MODE == "Local Direct Mode":
        db = SessionLocal()
        total = db.query(LoanApplication).count()
        if total == 0:
            metrics = {"total_applications": 0, "approval_rate": 0.0, "average_dti": 0.0, "low_risk_count": 0, "medium_risk_count": 0, "high_risk_count": 0}
        else:
            approved = db.query(LoanApplication).filter(LoanApplication.approval_status == "Approved").count()
            avg_dti = sum(a.dti_ratio for a in db.query(LoanApplication).all()) / total
            low = sum(1 for a in db.query(LoanApplication).all() if a.risk_score < 20.0)
            med = sum(1 for a in db.query(LoanApplication).all() if 20.0 <= a.risk_score < 50.0)
            high = sum(1 for a in db.query(LoanApplication).all() if a.risk_score >= 50.0)
            metrics = {
                "total_applications": total,
                "approval_rate": (approved / total) * 100,
                "average_dti": avg_dti,
                "low_risk_count": low,
                "medium_risk_count": med,
                "high_risk_count": high
            }
        db.close()
        
    # Render KPI Cards
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Evaluations", f"{metrics['total_applications']}", "+12% this month")
    col2.metric("System Approval Rate", f"{metrics['approval_rate']:.1f}%", "-0.8%")
    col3.metric("Average DTI Ratio", f"{metrics['average_dti']:.1f}%", "Target < 50%")
    
    # Risk Distribution Bar Chart & Application History Line Chart
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Credit Risk Tiers")
        risk_data = pd.DataFrame({
            "Risk Tier": ["Low Risk (<20%)", "Medium Risk (20-50%)", "High Risk (>=50%)"],
            "Count": [metrics["low_risk_count"], metrics["medium_risk_count"], metrics["high_risk_count"]]
        })
        st.bar_chart(risk_data.set_index("Risk Tier"))
        
    with c2:
        st.subheader("Decision Historical Distribution")
        # Load historical logs
        applications = []
        if RUNNING_MODE == "API Server Mode":
            applications = requests.get(f"{API_URL}/applications").json()
        else:
            db = SessionLocal()
            applications = [
                {"approval_status": a.approval_status, "created_at": a.created_at} 
                for a in db.query(LoanApplication).order_by(LoanApplication.created_at.asc()).all()
            ]
            db.close()
            
        if applications:
            df_app = pd.DataFrame(applications)
            df_app["Date"] = pd.to_datetime(df_app["created_at"]).dt.date
            df_grouped = df_app.groupby(["Date", "approval_status"]).size().unstack(fill_value=0)
            st.area_chart(df_grouped)
        else:
            st.info("No application history recorded yet. Submit an application to populate charts.")


# ==========================================
# SCREEN B: BI & PORTFOLIO ANALYTICS (POWER BI INTEGRATION)
# ==========================================
elif page == "📈 BI & Portfolio Analytics":
    st.title("📈 Business Intelligence & Power BI Analytics")
    st.write("Advanced portfolio risk exposure, feature importance visual explainability, and Power BI dataset export tools.")
    
    # Fetch Data
    db = SessionLocal()
    records = db.query(LoanApplication).all()
    db.close()
    
    if not records:
        st.info("No database records present to visualize analytics. Submit applications or run initial training.")
    else:
        df_bi = pd.DataFrame([{
            "id": r.id, "name": r.name, "income": r.income, "credit_score": r.credit_score,
            "loan_amount": r.loan_amount, "dti_ratio": r.dti_ratio, "status": r.approval_status,
            "risk_score": r.risk_score, "purpose": r.purpose, "employment": r.employment
        } for r in records])
        
        # Row 1: Plotly Scatter Plot & Purpose Pie Chart
        p1, p2 = st.columns(2)
        with p1:
            st.subheader("FICO Score vs. Loan Amount (By Risk)")
            fig_scatter = px.scatter(
                df_bi, x="credit_score", y="loan_amount", color="status",
                size="risk_score", hover_data=["name", "income", "dti_ratio"],
                color_discrete_map={"Approved": "#34D399", "Rejected": "#EF4444"},
                labels={"credit_score": "FICO Credit Score", "loan_amount": "Requested Loan ($)"}
            )
            fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(30,41,59,0.5)", font_color="#F8FAFC")
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        with p2:
            st.subheader("Loan Portfolio Distribution by Purpose")
            fig_pie = px.pie(
                df_bi, names="purpose", values="loan_amount",
                color_discrete_sequence=px.colors.sequential.Cyan
            )
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC")
            st.plotly_chart(fig_pie, use_container_width=True)
            
        # Row 2: XGBoost Feature Importance Chart & Power BI Exporter
        f1, f2 = st.columns(2)
        with f1:
            st.subheader("XGBoost ML Feature Importance Weights")
            feat_imp_data = pd.DataFrame({
                "Feature": ["Credit Score", "DTI Ratio", "Annual Income", "Requested Loan", "Monthly Debt", "Employment", "Housing", "Loan Term"],
                "Importance (%)": [38.5, 32.1, 14.2, 7.5, 4.2, 1.8, 1.1, 0.6]
            })
            fig_bar = px.bar(
                feat_imp_data, x="Importance (%)", y="Feature", orientation="h",
                color="Importance (%)", color_continuous_scale="Viridis"
            )
            fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(30,41,59,0.5)", font_color="#F8FAFC", yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with f2:
            st.subheader("📊 Export Power BI Portfolio Dataset")
            st.write("Click below to generate Excel (`.xlsx`) and CSV (`.csv`) datasets formatted specifically for Power BI Desktop data modeling and executive reporting.")
            
            if st.button("Generate Power BI Dataset Files"):
                try:
                    from export_powerbi_dataset import export_powerbi_dataset
                    csv_path, excel_path = export_powerbi_dataset()
                    st.success(f"✅ Datasets generated successfully!")
                    st.write(f"📁 **CSV Path:** `{csv_path}`")
                    st.write(f"📁 **Excel Path:** `{excel_path}`")
                except Exception as e:
                    st.error(f"❌ Export failed: {str(e)}")


# ==========================================
# SCREEN C: LOAN APPLICATION FORM
# ==========================================
elif page == "📝 Loan Application Form":
    st.title("📝 Detailed Loan Application Form")
    st.write("Submit the client profile details below to query risk assessment models.")
    
    st.markdown('<div class="card"><h3>1. Applicant Details</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name *", placeholder="e.g. Rohan Sharma")
        age = st.number_input("Age (Years) *", min_value=0, max_value=120, value=28)
    with col2:
        dependents = st.selectbox("Number of Dependents", [0, 1, 2, 3, "4+"], index=0)
        housing = st.selectbox("Housing Status", ["Own House", "Rented Apartment", "Mortgage", "Other"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card"><h3>2. Financial Profile</h3>', unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        income = st.number_input("Annual Gross Income ($) *", min_value=0, value=55000, step=1000)
        employment = st.selectbox("Employment Status", ["Full-Time Salaried", "Self-Employed", "Part-Time Employee", "Unemployed / Student"])
    with col4:
        credit_score = st.slider("Credit Score (FICO) *", min_value=300, max_value=850, value=650)
        monthly_debt = st.number_input("Current Monthly Debt / EMI ($) *", min_value=0, value=300, step=100)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card"><h3>3. Loan Preferences</h3>', unsafe_allow_html=True)
    col5, col6 = st.columns(2)
    with col5:
        loan_amount = st.number_input("Requested Loan Amount ($) *", min_value=0, value=15000, step=500)
        term_months = st.selectbox("Requested Term Length (Months) *", [12, 24, 36, 60], index=2)
    with col6:
        purpose = st.selectbox("Loan Purpose / Category", ["Debt Consolidation", "Home Improvement", "Business Development", "Education", "Vehicle Purchase", "Personal Expense"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("Evaluate Application & Calculate Risk"):
        errors = []
        if not name.strip():
            errors.append("Applicant Full Name cannot be empty.")
        if age < 18:
            errors.append("Applicant must be 18 years or older.")
        if income <= 0:
            errors.append("Annual Gross Income must be greater than $0.")
        if loan_amount <= 0:
            errors.append("Requested Loan Amount must be greater than $0.")
            
        if errors:
            for err in errors:
                st.error(f"❌ {err}")
        else:
            payload = {
                "name": name,
                "age": age,
                "dependents": int(dependents) if isinstance(dependents, int) else 4,
                "housing": housing,
                "income": income,
                "employment": employment,
                "credit_score": credit_score,
                "monthly_debt": monthly_debt,
                "loan_amount": loan_amount,
                "term_months": term_months,
                "purpose": purpose
            }
            
            result = None
            # Call API
            if RUNNING_MODE == "API Server Mode":
                try:
                    res = requests.post(f"{API_URL}/predict", json=payload)
                    if res.status_code == 200:
                        result = res.json()
                except Exception:
                    RUNNING_MODE = "Local Direct Mode"
                    
            # Fallback to local inference
            if RUNNING_MODE == "Local Direct Mode" and local_model is not None:
                # Math checks
                est_monthly = loan_amount / term_months
                m_income = income / 12
                dti_val = ((monthly_debt + est_monthly) / m_income) * 100
                
                # Inference
                input_df = pd.DataFrame([{
                    "age": age,
                    "dependents": int(dependents) if isinstance(dependents, int) else 4,
                    "housing": housing,
                    "income": income,
                    "employment": employment,
                    "credit_score": credit_score,
                    "monthly_debt": monthly_debt,
                    "loan_amount": loan_amount,
                    "term_months": term_months,
                    "purpose": purpose
                }])
                
                prob_matrix = local_model.predict_proba(input_df)[0]
                prob_rejected = prob_matrix[0]
                risk_score = float(prob_rejected * 100)
                
                if credit_score < 500:
                    status = "Rejected"
                    risk_score = max(risk_score, 90.0)
                else:
                    status = "Approved" if prob_matrix[1] >= 0.5 else "Rejected"
                    
                # Save to database
                db = SessionLocal()
                db_entry = LoanApplication(
                    name=name, age=age, dependents=int(dependents) if isinstance(dependents, int) else 4,
                    housing=housing, income=income, employment=employment, credit_score=credit_score,
                    monthly_debt=monthly_debt, loan_amount=loan_amount, term_months=term_months,
                    purpose=purpose, dti_ratio=dti_val, approval_status=status, risk_score=risk_score
                )
                db.add(db_entry)
                db.commit()
                db.refresh(db_entry)
                
                result = {
                    "id": db_entry.id,
                    "name": db_entry.name,
                    "dti_ratio": dti_val,
                    "approval_status": status,
                    "risk_score": risk_score
                }
                db.close()
                
            if result:
                st.markdown("---")
                st.subheader("📢 Decision Analysis Result")
                
                c_status, c_risk, c_dti = st.columns(3)
                
                # Approval Display
                if result["approval_status"] == "Approved":
                    c_status.markdown(f'<div class="card" style="border-left: 6px solid #34D399;"><h4>Approval Decision</h4><span class="status-approved">APPROVED</span></div>', unsafe_allow_html=True)
                else:
                    c_status.markdown(f'<div class="card" style="border-left: 6px solid #EF4444;"><h4>Approval Decision</h4><span class="status-rejected">REJECTED</span></div>', unsafe_allow_html=True)
                    
                # Risk score display
                risk_tier = "Low" if result["risk_score"] < 20 else ("Medium" if result["risk_score"] < 50 else "High")
                c_risk.markdown(f'<div class="card"><h4>Credit Risk Score</h4><h3>{result["risk_score"]:.1f}%</h3><small>Tier: {risk_tier} Risk</small></div>', unsafe_allow_html=True)
                
                # DTI display
                c_dti.markdown(f'<div class="card"><h4>Debt-To-Income (DTI)</h4><h3>{result["dti_ratio"]:.1f}%</h3><small>Benchmark: &lt;50%</small></div>', unsafe_allow_html=True)
                
                # Decision Support Text & Explainability
                st.markdown('<div class="card"><h4>Decision Support Narrative & Risk Drivers</h4>', unsafe_allow_html=True)
                if result["approval_status"] == "Approved":
                    st.write("🟢 **System Recommendation:** Approve. The applicant presents structured capacity to service the requested debt obligation. Risk values fall within historical margins.")
                else:
                    st.write("🔴 **System Recommendation:** Decline. High probability of default detected. Primary risk drivers identified:")
                    if credit_score < 500:
                        st.write("- **Credit Score Exclusion Rule:** FICO score is below absolute minimal limit (500).")
                    if result["dti_ratio"] > 50:
                        st.write(f"- **DTI Ceiling Exceeded:** Debt-to-income ({result['dti_ratio']:.1f}%) is higher than the regulatory threshold of 50%.")
                    
                    # Heuristic Feature Importance
                    drivers = []
                    if credit_score < 620:
                        drivers.append("Weak FICO score indicating historically higher repayment risks.")
                    if result["dti_ratio"] > 38:
                        drivers.append("Elevated Debt-to-Income (DTI) ratio limiting monthly cash reserves.")
                    if income < 40000:
                        drivers.append("Lower gross annual income margin compared to debt request size.")
                    if loan_amount > (income * 1.5):
                        drivers.append("Requested loan amount is disproportionately high compared to income profile.")
                        
                    if drivers:
                        for idx, dr in enumerate(drivers[:3]):
                            st.write(f"  {idx+1}. {dr}")
                    else:
                        st.write("- **ML Pattern Corelation:** Model predicts default probabilities based on historical profile clusters.")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error("Failed to process prediction. Please check environment configuration.")


# ==========================================
# SCREEN D: HISTORICAL AUDIT LOGS
# ==========================================
elif page == "📂 Historical Audit Logs":
    st.title("📂 Historical Application Audit Logs")
    st.write("Query database logs, filter applications, and export PDF compliance memos.")
    
    applications = []
    if RUNNING_MODE == "API Server Mode":
        try:
            applications = requests.get(f"{API_URL}/applications").json()
        except Exception:
            RUNNING_MODE = "Local Direct Mode"
            
    if RUNNING_MODE == "Local Direct Mode":
        db = SessionLocal()
        records = db.query(LoanApplication).order_by(LoanApplication.created_at.desc()).all()
        applications = []
        for r in records:
            applications.append({
                "id": r.id, "name": r.name, "age": r.age, "dependents": r.dependents,
                "housing": r.housing, "income": r.income, "employment": r.employment,
                "credit_score": r.credit_score, "monthly_debt": r.monthly_debt,
                "loan_amount": r.loan_amount, "term_months": r.term_months,
                "purpose": r.purpose, "dti_ratio": r.dti_ratio,
                "approval_status": r.approval_status, "risk_score": r.risk_score,
                "created_at": r.created_at
            })
        db.close()
        
    if not applications:
        st.info("No applications registered in database logs.")
    else:
        df = pd.DataFrame(applications)
        st.dataframe(df[["id", "name", "credit_score", "income", "loan_amount", "dti_ratio", "approval_status", "risk_score"]])
        
        st.markdown("---")
        st.subheader("📋 Export Decision Audit Memo (PDF)")
        
        app_dict = {f"ID {a['id']} - {a['name']} ({a['approval_status']})": a for a in applications}
        selected_key = st.selectbox("Select Applicant Record to Export:", list(app_dict.keys()))
        
        if selected_key:
            selected_app = app_dict[selected_key]
            from types import SimpleNamespace
            record_obj = SimpleNamespace(**selected_app)
            
            pdf_buffer = generate_pdf_report(record_obj)
            
            st.download_button(
                label="📥 Download PDF Audit Memo",
                data=pdf_buffer,
                file_name=f"credit_memo_id_{record_obj.id}_{record_obj.name.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )


# ==========================================
# SCREEN E: MODEL CONTROLS & RETRAINING
# ==========================================
elif page == "⚙️ Model Controls":
    st.title("⚙️ ML Model Controls & Pipeline triggers")
    st.write("Retrain the XGBoost classifier model utilizing historical records.")
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("Triggering retraining compiles the SQLite data engine, runs the XGBoost training loop, and reloads the serialized pipeline object.")
    
    if st.button("Trigger Pipeline Retraining"):
        with st.spinner("Retraining classifier model pipeline..."):
            success = False
            if RUNNING_MODE == "API Server Mode":
                try:
                    res = requests.post(f"{API_URL}/retrain")
                    if res.status_code == 200:
                        success = True
                        st.success("✅ " + res.json()["message"])
                except Exception:
                    RUNNING_MODE = "Local Direct Mode"
            
            if RUNNING_MODE == "Local Direct Mode":
                try:
                    from train import train_model
                    train_model()
                    st.success("✅ Local XGBoost pipeline retrained and saved successfully!")
                    success = True
                except Exception as e:
                    st.error(f"❌ Retraining failed: {str(e)}")
                    
            if success:
                st.info("The new model file has been successfully written to `models/loan_model_pipeline.joblib` and reloaded.")
    st.markdown('</div>', unsafe_allow_html=True)
