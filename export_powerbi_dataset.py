import os
import pandas as pd
from app.database import SessionLocal, LoanApplication, init_db

def export_powerbi_dataset():
    """
    Exports database records to Excel and CSV formats optimized for Power BI Desktop ingestion,
    adding calculated fields like Risk Category, DTI Tier, FICO Bracket, and Income Tier.
    """
    init_db()
    db = SessionLocal()
    
    records = db.query(LoanApplication).all()
    if not records:
        print("No database records found. Run application or train script first.")
        db.close()
        return
        
    data = []
    for r in records:
        # Derived BI Dimensions
        dti_tier = "<30% Low" if r.dti_ratio < 30 else ("30-50% Moderate" if r.dti_ratio <= 50 else ">50% High Risk")
        fico_bracket = "Poor (<580)" if r.credit_score < 580 else ("Fair (580-660)" if r.credit_score < 660 else ("Good (660-740)" if r.credit_score < 740 else "Excellent (740+)"))
        income_tier = "<$35k" if r.income < 35000 else ("$35k-$75k" if r.income <= 75000 else ("$75k-$125k" if r.income <= 125000 else ">$125k"))
        risk_tier = "Low Risk (<20%)" if r.risk_score < 20 else ("Medium Risk (20-50%)" if r.risk_score < 50 else "High Risk (>=50%)")
        
        data.append({
            "Application_ID": r.id,
            "Applicant_Name": r.name,
            "Age": r.age,
            "Dependents": r.dependents,
            "Housing_Status": r.housing,
            "Annual_Income": r.income,
            "Income_Tier": income_tier,
            "Employment_Status": r.employment,
            "Credit_Score": r.credit_score,
            "FICO_Bracket": fico_bracket,
            "Monthly_Debt": r.monthly_debt,
            "Requested_Loan_Amount": r.loan_amount,
            "Term_Months": r.term_months,
            "Loan_Purpose": r.purpose,
            "Calculated_DTI_Ratio": round(r.dti_ratio, 2),
            "DTI_Tier": dti_tier,
            "Approval_Status": r.approval_status,
            "Risk_Score_Pct": round(r.risk_score, 2),
            "Risk_Tier": risk_tier,
            "Created_Timestamp": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ""
        })
        
    db.close()
    
    df = pd.DataFrame(data)
    
    # Save CSV and Excel for Power BI
    csv_path = r"C:\Users\nrgam\OneDrive\Documents\Desktop\Internship project\loan_portfolio_powerbi.csv"
    excel_path = r"C:\Users\nrgam\OneDrive\Documents\Desktop\Internship project\loan_portfolio_powerbi.xlsx"
    
    df.to_csv(csv_path, index=False)
    df.to_excel(excel_path, index=False, engine='openpyxl')
    
    print(f"Power BI Dataset Exported Successfully!")
    print(f" - CSV: {csv_path}")
    print(f" - Excel: {excel_path}")
    return csv_path, excel_path

if __name__ == "__main__":
    export_powerbi_dataset()
