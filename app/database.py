import os
import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Database Connection URL Setup
# SQLite is used by default so it runs instantly. MySQL can be configured via environment variables.
DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_HOST = os.getenv("MYSQL_HOST")
DB_NAME = os.getenv("MYSQL_DATABASE")

if DB_USER and DB_PASSWORD and DB_HOST and DB_NAME:
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
else:
    DATABASE_URL = "sqlite:///loan_system.db"

# 2. Initialize SQLAlchemy Engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. Define Applications Table Model
class LoanApplication(Base):
    __tablename__ = "loan_applications"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    dependents = Column(Integer, nullable=False)
    housing = Column(String(50), nullable=False)
    income = Column(Float, nullable=False)
    employment = Column(String(50), nullable=False)
    credit_score = Column(Integer, nullable=False)
    monthly_debt = Column(Float, nullable=False)
    loan_amount = Column(Float, nullable=False)
    term_months = Column(Integer, nullable=False)
    purpose = Column(String(100), nullable=False)
    dti_ratio = Column(Float, nullable=False)
    
    # Heuristics metrics for Phase 2
    approval_status = Column(String(20), nullable=False) # Approved or Rejected
    risk_score = Column(Float, nullable=False)           # 0 to 100
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# 4. Create Tables Function
def init_db():
    Base.metadata.create_all(bind=engine)

# Helper function to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
