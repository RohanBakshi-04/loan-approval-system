import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
import joblib

def generate_synthetic_data(n_samples=5000):
    """
    Generates a synthetic financial dataset representing historical loan applicants,
    their credit metrics, and whether they ultimately defaulted.
    """
    np.random.seed(42)
    
    # 1. Personal & Demographic Features
    age = np.random.randint(18, 70, size=n_samples)
    dependents = np.random.randint(0, 5, size=n_samples)
    housing = np.random.choice(["Own House", "Rented Apartment", "Mortgage", "Other"], size=n_samples, p=[0.3, 0.4, 0.25, 0.05])
    
    # 2. Financial Metrics
    income = np.random.exponential(scale=50000, size=n_samples) + 15000
    income = np.clip(income, 15000, 300000) # clip to realistic range
    
    employment = np.random.choice(
        ["Full-Time Salaried", "Self-Employed", "Part-Time Employee", "Unemployed / Student"], 
        size=n_samples, 
        p=[0.6, 0.2, 0.15, 0.05]
    )
    
    credit_score = np.random.normal(loc=650, scale=80, size=n_samples).astype(int)
    credit_score = np.clip(credit_score, 300, 850)
    
    monthly_debt = np.random.exponential(scale=400, size=n_samples)
    monthly_debt = np.clip(monthly_debt, 0, income * 0.4) # debt limited by income
    
    # 3. Loan Request Properties
    loan_amount = np.random.exponential(scale=25000, size=n_samples) + 5000
    loan_amount = np.clip(loan_amount, 2000, 200000)
    
    term_months = np.random.choice([12, 24, 36, 60], size=n_samples, p=[0.1, 0.2, 0.5, 0.2])
    purpose = np.random.choice(
        ["Debt Consolidation", "Home Improvement", "Business Development", "Education", "Vehicle Purchase", "Personal Expense"], 
        size=n_samples
    )
    
    # 4. Generate Ground Truth Targets (Default Probability Rules)
    # Estimate monthly loan installment payment
    est_monthly_payment = loan_amount / term_months
    monthly_income = income / 12
    dti = ((monthly_debt + est_monthly_payment) / monthly_income)
    
    # Probability score built on financial indicators
    log_odds = (
        -2.0 
        + 4.0 * (dti - 0.35)
        - 0.015 * (credit_score - 600)
        - 0.00001 * (income - 50000)
        + 0.5 * (employment == "Unemployed / Student").astype(float)
        + 0.3 * (housing == "Rented Apartment").astype(float)
    )
    
    # Sigmoid function to convert log_odds to probability
    prob = 1 / (1 + np.exp(-log_odds))
    # Add random noise to make it realistic
    prob = np.clip(prob + np.random.normal(0, 0.05, n_samples), 0.0, 1.0)
    
    # Default outcome (1 = Defaulted / High Risk, 0 = Paid back / Low Risk)
    defaulted = (prob >= 0.5).astype(int)
    
    # Approve if not defaulted and credit score >= 500
    approved = ((defaulted == 0) & (credit_score >= 500)).astype(int)
    
    df = pd.DataFrame({
        "name": [f"Applicant_{i}" for i in range(n_samples)],
        "age": age,
        "dependents": dependents,
        "housing": housing,
        "income": income,
        "employment": employment,
        "credit_score": credit_score,
        "monthly_debt": monthly_debt,
        "loan_amount": loan_amount,
        "term_months": term_months,
        "purpose": purpose,
        "dti_ratio": dti * 100,
        "approved": approved
    })
    
    return df

def train_model():
    print("Generating synthetic banking dataset...")
    df = generate_synthetic_data(n_samples=5000)
    
    # Separate Features and Label
    X = df.drop(columns=["name", "approved", "dti_ratio"])
    y = df["approved"]
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Define columns
    num_cols = ["age", "dependents", "income", "credit_score", "monthly_debt", "loan_amount", "term_months"]
    cat_cols = ["housing", "employment", "purpose"]
    
    # Preprocessors
    num_transformer = Pipeline(steps=[
        ('scaler', StandardScaler())
    ])
    cat_transformer = Pipeline(steps=[
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])
    
    preprocessor = ColumnTransformer(transformers=[
        ('num', num_transformer, num_cols),
        ('cat', cat_transformer, cat_cols)
    ])
    
    # Build complete pipeline
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', XGBClassifier(
            n_estimators=100,
            learning_rate=0.08,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="logloss"
        ))
    ])
    
    print("Training XGBoost Classification model...")
    pipeline.fit(X_train, y_train)
    
    # Evaluate model
    train_acc = pipeline.score(X_train, y_train)
    test_acc = pipeline.score(X_test, y_test)
    print(f"Model Training Accuracy: {train_acc:.4f}")
    print(f"Model Testing Accuracy: {test_acc:.4f}")
    
    # Save objects
    os.makedirs("models", exist_ok=True)
    model_path = "models/loan_model_pipeline.joblib"
    joblib.dump(pipeline, model_path)
    print(f"Model pipeline successfully saved to {model_path}")
    
    # Save a copy of features to describe schema
    df_features_sample = X_train.iloc[0:1]
    df_features_sample.to_csv("models/features_schema.csv", index=False)

if __name__ == "__main__":
    train_model()
