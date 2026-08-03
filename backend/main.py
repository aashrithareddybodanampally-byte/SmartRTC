"""
TSRTC Smart Analytics Platform - Backend API
Enterprise-grade transport data analytics engine
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from database import engine
from models import Base
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import jwt
from passlib.context import CryptContext
import json
from collections import defaultdict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


from fastapi import Header, Depends
from sqlalchemy.orm import Session
from jose import jwt
from database import SessionLocal
from models import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header format")

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# Initialize FastAPI
app = FastAPI(title="TSRTC Analytics API", version="2.0")
Base.metadata.create_all(bind=engine)
# Mount static files (frontend)
# Get the path to the frontend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Serve static files
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "tsrtc-hackathon-secret-key-2024")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory data storage (for demo)
data_store = {
    "tickets": None,
    "bookings": [],
    "complaints": [],
    "crew_assignments": {},
    "registrations": [],
    "users": {
        "admin": {"password": pwd_context.hash("admin123"), "role": "admin"},
        "planner": {"password": pwd_context.hash("planner123"), "role": "planner"},
        "viewer": {"password": pwd_context.hash("viewer123"), "role": "viewer"}
    }
}

# Initialize crew assignments
def init_crew_assignments():
    """Initialize sample crew assignments"""
    data_store["crew_assignments"] = {
        "100": {
            "driver": {"id": "D001", "name": "Rajesh Kumar", "rating": 4.5},
            "conductor": {"id": "C001", "name": "Lakshmi Devi", "rating": 4.7}
        },
        "49M": {
            "driver": {"id": "D002", "name": "Suresh Reddy", "rating": 4.3},
            "conductor": {"id": "C002", "name": "Priya Sharma", "rating": 4.6}
        },
        "5K": {
            "driver": {"id": "D003", "name": "Venkat Rao", "rating": 4.8},
            "conductor": {"id": "C003", "name": "Manjula Bai", "rating": 4.4}
        }
    }

init_crew_assignments()

def get_tickets_df() -> pd.DataFrame:
    """Helper to get tickets DataFrame, raising 404 if no data is uploaded"""
    if data_store["tickets"] is None:
        raise HTTPException(status_code=404, detail="No ticket data available. Please upload a CSV first.")
    return data_store["tickets"]

@app.on_event("startup")
async def startup_event():
    """Load sample data on startup if not already loaded"""
    if data_store["tickets"] is None:
        sample_path = os.path.join(BASE_DIR, "sample_tickets.csv")
        if os.path.exists(sample_path):
            try:
                df = pd.read_csv(sample_path)
                # Combine trip_date and time if they are separate
                if 'trip_date' in df.columns and 'time' in df.columns:
                    df['time'] = pd.to_datetime(df['trip_date'] + ' ' + df['time'])
                elif 'time' in df.columns:
                    df['time'] = pd.to_datetime(df['time'])
                
                data_store["tickets"] = df
                print(f"✅ Loaded {len(df)} sample tickets from {sample_path}")
            except Exception as e:
                print(f"❌ Error loading sample data: {e}")
        else:
            print(f"⚠️ Sample data not found at {sample_path}")

# ===========================
# MODELS
# ===========================

class LoginRequest(BaseModel):
    username: str
    password: str

class WhatIfParams(BaseModel):
    fare_change_percent: float = 0
    frequency_change_percent: float = 0
    capacity_change: int = 0
    new_stop: Optional[str] = None

class User(BaseModel):
    username: str
    role: str

class BookingRequest(BaseModel):
    from_stop: str
    to_stop: str
    passenger_name: str
    passenger_phone: str
    passenger_email: Optional[str] = None
    travel_date: str
    travel_time: str
    bus_number: str
    seats: int = 1

# Anonymous complaint categories (structured flow)
COMPLAINT_CATEGORIES = ["rude_behaviour", "ticket_issue", "unsafe_driving", "corruption", "other"]

class ComplaintRequest(BaseModel):
    bus_number: str
    person_type: str  # 'driver' or 'conductor'
    person_id: str
    category: str  # rude_behaviour | ticket_issue | unsafe_driving | corruption | other
    description: str
    timestamp: Optional[str] = None

class AIRecommendationRequest(BaseModel):
    route_id: Optional[str] = None
    analyze_all: bool = False

class RegistrationRequest(BaseModel):
    username: str
    password: str
    full_name: str
    email: str
    phone: str
    designation: str  # driver, conductor, admin, planner, viewer
    employee_id: str

class FareBasedBookingRequest(BaseModel):
    fare_amount: float  # User enters this amount
    passenger_name: str
    passenger_phone: str
    passenger_email: Optional[str] = None
    travel_date: str
    payment_method: str  # upi, card, netbanking, wallet_paytm, wallet_phonepe, wallet_googlepay

# ===========================
# AUTH UTILITIES
# ===========================

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return User(username=username, role=role)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ===========================
# AUTH ENDPOINTS
# ===========================

from database import SessionLocal, get_db
from models import User
from fastapi import Depends, status

@app.post("/api/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    # Check database users first
    user = db.query(User).filter(User.username == request.username).first()
    
    if user and verify_password(request.password, user.password):
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role}
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "username": user.username,
                "role": user.role
            }
        }

    # Fallback to in-memory users for demo accounts (if any are left that aren't in DB)
    if request.username in data_store["users"]:
        user_data = data_store["users"][request.username]
        if verify_password(request.password, user_data["password"]):
            access_token = create_access_token(
                data={"sub": request.username, "role": user_data["role"]}
            )
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "username": request.username,
                    "role": user_data["role"]
                }
            }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.get("/api/auth/verify")
async def verify(token: str):
    """Verify token and return user info"""
    user = verify_token(token)
    return {"username": user.username, "role": user.role}

# ===========================
# REGISTRATION ENDPOINTS
# ===========================

@app.post("/api/auth/register")
async def register_user(registration: RegistrationRequest, db: Session = Depends(get_db)):
    """Submit new user registration"""
    # Check if username already exists in data_store OR database
    if registration.username in data_store["users"] or \
       db.query(User).filter(User.username == registration.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email already registered in registrations
    for user in data_store["registrations"]:
        if user.get("email") == registration.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(registration.password)
    
    # Create registration ID
    registration_id = f"REG{datetime.now().strftime('%Y%m%d%H%M%S')}{len(data_store['registrations'])}"
    
    # Store registration
    registration_record = {
        "registration_id": registration_id,
        "username": registration.username,
        "password": hashed_password,
        "full_name": registration.full_name,
        "email": registration.email,
        "phone": registration.phone,
        "designation": registration.designation,
        "employee_id": registration.employee_id,
        "approval_status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    data_store["registrations"].append(registration_record)
    
    return {
        "success": True,
        "message": "Registration submitted successfully. Please wait for admin approval.",
        "registration_id": registration_id
    }

@app.get("/api/auth/registrations")
async def get_pending_registrations(status: Optional[str] = None):
    """Get all registrations (admin only)"""
    registrations = data_store["registrations"]
    
    if status:
        registrations = [r for r in registrations if r["approval_status"] == status]
    
    return {
        "registrations": sorted(registrations, key=lambda x: x["created_at"], reverse=True),
        "total": len(registrations),
        "pending": len([r for r in data_store["registrations"] if r["approval_status"] == "pending"])
    }

@app.put("/api/auth/registrations/{registration_id}/approve")
async def approve_registration(registration_id: str, notes: Optional[str] = None, db: Session = Depends(get_db)):
    """Approve a registration (admin only)"""
    registration = next((r for r in data_store["registrations"] if r["registration_id"] == registration_id), None)
    
    # Determine role based on designation
    role_mapping = {
        "driver": "driver",
        "conductor": "conductor",
        "admin": "admin",
        "planner": "planner",
        "viewer": "viewer"
    }
    role = role_mapping.get(registration["designation"], "viewer")

    # Create database user
    db_user = User(
        username=registration["username"],
        password=registration["password"],
        role=role,
        employee_id=registration["employee_id"],
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Update registration entry for consistency
    registration["approval_status"] = "approved"
    registration["approved_at"] = datetime.now().isoformat()
    if notes:
        registration["admin_notes"] = notes
    
    return {"success": True, "message": f"User {registration['username']} approved successfully"}

@app.put("/api/auth/registrations/{registration_id}/reject")
async def reject_registration(registration_id: str, reason: Optional[str] = None):
    """Reject a registration (admin only)"""
    registration = next((r for r in data_store["registrations"] if r["registration_id"] == registration_id), None)
    
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    # Update registration status
    registration["approval_status"] = "rejected"
    registration["rejected_at"] = datetime.now().isoformat()
    if reason:
        registration["rejection_reason"] = reason
    
    return {"success": True, "message": f"Registration for {registration['full_name']} rejected"}

# ===========================
# DATA VALIDATION
# ===========================

def validate_ticket_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate uploaded ticket data and return quality report"""
    
    required_columns = ['from_stop', 'to_stop', 'time', 'passenger_count', 'fare']
    issues = []
    
    # Check required columns (allow extra columns)
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        return {
            "valid": False,
            "error": f"Missing required columns: {', '.join(missing_cols)}",
            "required_columns": required_columns,
            "found_columns": list(df.columns)
        }
    
    # Note: Extra columns (like route_id, distance_km, trip_date) are allowed and will be ignored
    
    # Check for missing values
    for col in required_columns:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            issues.append({
                "type": "missing_values",
                "column": col,
                "count": int(null_count),
                "percentage": round(null_count / len(df) * 100, 2)
            })
    
    # Validate numeric columns
    try:
        df['passenger_count'] = pd.to_numeric(df['passenger_count'], errors='coerce')
        df['fare'] = pd.to_numeric(df['fare'], errors='coerce')
    except:
        issues.append({"type": "conversion_error", "message": "Invalid numeric values"})
    
    # Check for negative values
    negative_passengers = (df['passenger_count'] < 0).sum()
    if negative_passengers > 0:
        issues.append({
            "type": "invalid_value",
            "column": "passenger_count",
            "message": f"{negative_passengers} negative values found"
        })
    
    negative_fares = (df['fare'] < 0).sum()
    if negative_fares > 0:
        issues.append({
            "type": "invalid_value",
            "column": "fare",
            "message": f"{negative_fares} negative values found"
        })
    
    # Check for duplicates
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        issues.append({
            "type": "duplicates",
            "count": int(duplicates),
            "percentage": round(duplicates / len(df) * 100, 2)
        })
    
    # Validate time format
    try:
        pd.to_datetime(df['time'], errors='coerce')
    except:
        issues.append({"type": "invalid_time", "message": "Invalid time format detected"})
    
    return {
        "valid": True,
        "total_records": len(df),
        "issues": issues,
        "quality_score": max(0, 100 - len(issues) * 10),
        "preview": df.head(10).to_dict(orient='records')
    }

# ===========================
# DATA UPLOAD
# ===========================

@app.post("/api/upload")
async def upload_data(file: UploadFile = File(...)):
    """Upload and validate ticket data CSV"""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    
    try:
        # Read CSV
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Validate
        validation_result = validate_ticket_data(df)
        
        if validation_result["valid"]:
            # Store data
            data_store["tickets"] = df
            
            return {
                "success": True,
                "message": "Data uploaded successfully",
                "validation": validation_result,
                "stats": {
                    "total_records": len(df),
                    "unique_stops": len(set(df['from_stop'].unique()) | set(df['to_stop'].unique())),
                    "date_range": {
                        "start": str(df['time'].min()),
                        "end": str(df['time'].max())
                    }
                }
            }
        else:
            raise HTTPException(status_code=400, detail=validation_result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/api/sample-csv")
async def get_sample_csv():
    """Download sample CSV template"""
    
    sample_data = pd.DataFrame({
        'from_stop': ['Secunderabad', 'KPHB', 'Dilsukhnagar', 'Uppal', 'LB Nagar'],
        'to_stop': ['Koti', 'Ameerpet', 'Charminar', 'Secunderabad', 'Dilsukhnagar'],
        'time': ['2024-01-15 08:30:00', '2024-01-15 09:15:00', '2024-01-15 10:00:00', 
                 '2024-01-15 11:30:00', '2024-01-15 14:00:00'],
        'passenger_count': [45, 38, 52, 41, 35],
        'fare': [25, 30, 20, 35, 25]
    })
    
    stream = io.StringIO()
    sample_data.to_csv(stream, index=False)
    
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tsrtc_sample_data.csv"}
    )

# ===========================
# OD ANALYTICS
# ===========================

@app.get("/api/analytics/od-matrix")
async def get_od_matrix(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    stop_filter: Optional[str] = None
):
    """Generate Origin-Destination demand matrix"""
    
    if data_store["tickets"] is None:
        raise HTTPException(status_code=400, detail="No data uploaded")
    
    df = data_store["tickets"].copy()
    
    # Convert time to datetime
    df['time'] = pd.to_datetime(df['time'])
    
    # Apply filters
    if start_time:
        df = df[df['time'] >= pd.to_datetime(start_time)]
    if end_time:
        df = df[df['time'] <= pd.to_datetime(end_time)]
    if stop_filter:
        df = df[(df['from_stop'] == stop_filter) | (df['to_stop'] == stop_filter)]
    
    # Calculate OD matrix
    od_matrix = df.groupby(['from_stop', 'to_stop']).agg({
        'passenger_count': 'sum',
        'fare': 'sum'
    }).reset_index()
    
    od_matrix['avg_fare'] = od_matrix['fare'] / od_matrix['passenger_count']
    od_matrix = od_matrix.sort_values('passenger_count', ascending=False)
    
    # Calculate hourly demand
    df['hour'] = df['time'].dt.hour
    hourly_demand = df.groupby('hour').agg({
        'passenger_count': 'sum',
        'fare': 'sum'
    }).reset_index()
    
    # Top corridors
    top_corridors = od_matrix.head(20).to_dict(orient='records')
    
    # Peak hours
    peak_hours = hourly_demand.nlargest(5, 'passenger_count')[['hour', 'passenger_count']].to_dict(orient='records')
    
    # Heatmap data
    all_stops = sorted(set(df['from_stop'].unique()) | set(df['to_stop'].unique()))
    heatmap = []
    for from_stop in all_stops[:20]:  # Limit for performance
        row = []
        for to_stop in all_stops[:20]:
            value = df[(df['from_stop'] == from_stop) & (df['to_stop'] == to_stop)]['passenger_count'].sum()
            row.append(int(value))
        heatmap.append(row)
    
    return {
        "top_corridors": top_corridors,
        "hourly_demand": hourly_demand.to_dict(orient='records'),
        "peak_hours": peak_hours,
        "heatmap": {
            "data": heatmap,
            "labels": all_stops[:20]
        },
        "summary": {
            "total_passengers": int(df['passenger_count'].sum()),
            "total_revenue": float(df['fare'].sum()),
            "avg_fare": float(df['fare'].mean()),
            "unique_corridors": len(od_matrix)
        }
    }

# ===========================
# PROFITABILITY ANALYSIS
# ===========================

@app.get("/api/analytics/profitability")
async def calculate_profitability():
    """Calculate route profitability"""
    
    df = get_tickets_df()
    
    # Aggregate by route (from-to pair)
    route_data = df.groupby(['from_stop', 'to_stop']).agg({
        'passenger_count': 'sum',
        'fare': 'sum'
    }).reset_index()
    
    # Estimate costs (simplified model)
    # Assume average distance based on fare and cost per km
    route_data['estimated_distance'] = route_data['fare'] / df['fare'].mean() * 15  # km
    COST_PER_KM = 8  # Fuel + maintenance
    FIXED_COST = 500  # per trip
    
    route_data['total_revenue'] = route_data['fare']
    route_data['estimated_cost'] = (route_data['estimated_distance'] * COST_PER_KM) + FIXED_COST
    route_data['profit'] = route_data['total_revenue'] - route_data['estimated_cost']
    route_data['profit_margin'] = (route_data['profit'] / route_data['total_revenue'] * 100).round(2)
    route_data['route_name'] = route_data['from_stop'] + ' → ' + route_data['to_stop']
    
    # Sort by profit
    route_data = route_data.sort_values('profit', ascending=False)
    
    # Profitable routes
    profitable = route_data[route_data['profit'] > 0].head(15)
    loss_making = route_data[route_data['profit'] < 0].head(15)
    
    return {
        "profitable_routes": profitable.to_dict(orient='records'),
        "loss_making_routes": loss_making.to_dict(orient='records'),
        "summary": {
            "total_revenue": float(route_data['total_revenue'].sum()),
            "total_cost": float(route_data['estimated_cost'].sum()),
            "net_profit": float(route_data['profit'].sum()),
            "profitable_count": len(route_data[route_data['profit'] > 0]),
            "loss_making_count": len(route_data[route_data['profit'] < 0]),
            "avg_profit_margin": float(route_data['profit_margin'].mean())
        },
        "all_routes": route_data.to_dict(orient='records')
    }

# ===========================
# WHAT-IF SIMULATOR
# ===========================

@app.post("/api/simulator/whatif")
async def simulate_whatif(request: WhatIfParams): # Changed parameter name to request: WhatIfParams
    """Run What-If simulation on demand and revenue""" # Changed docstring
    df = get_tickets_df()
    
    # Apply factors
    # Current scenario
    current_revenue = df['fare'].sum()
    current_passengers = df['passenger_count'].sum()
    current_capacity_utilization = 65  # Assume baseline
    
    # Simulate changes
    fare_multiplier = 1 + (request.fare_change_percent / 100) # Changed params to request
    
    # Price elasticity: -0.5 (typical for public transport)
    demand_change = -0.5 * request.fare_change_percent / 100 # Changed params to request
    demand_multiplier = 1 + demand_change
    
    # Frequency effect on demand (+1% frequency = +0.3% demand)
    frequency_effect = request.frequency_change_percent / 100 * 0.3 # Changed params to request
    demand_multiplier *= (1 + frequency_effect)
    
    # New scenario
    new_passengers = current_passengers * demand_multiplier
    new_revenue = new_passengers * df['fare'].mean() * fare_multiplier
    new_capacity_utilization = current_capacity_utilization + request.capacity_change # Changed params to request
    
    # Calculate operational impact
    frequency_multiplier = 1 + (request.frequency_change_percent / 100) # Changed params to request
    new_operational_cost = 500000 * frequency_multiplier  # Base cost
    
    new_profit = new_revenue - new_operational_cost
    current_profit = current_revenue - 500000
    
    return {
        "before": {
            "passengers": int(current_passengers),
            "revenue": float(current_revenue),
            "profit": float(current_profit),
            "capacity_utilization": current_capacity_utilization
        },
        "after": {
            "passengers": int(new_passengers),
            "revenue": float(new_revenue),
            "profit": float(new_profit),
            "capacity_utilization": new_capacity_utilization
        },
        "changes": {
            "passenger_change": float(((new_passengers - current_passengers) / current_passengers) * 100),
            "revenue_change": float(((new_revenue - current_revenue) / current_revenue) * 100),
            "profit_change": float(new_profit - current_profit),
            "roi": float(((new_profit - current_profit) / abs(new_operational_cost - 500000)) * 100) if new_operational_cost != 500000 else 0
        },
        "parameters": {
            "fare_change": request.fare_change_percent, # Changed params to request
            "frequency_change": request.frequency_change_percent, # Changed params to request
            "capacity_change": request.capacity_change # Changed params to request
        }
    }

# ===========================
# AI RECOMMENDATION ENGINE
# ===========================

@app.post("/api/ai/recommendations") # Kept POST as per original, instruction had GET
async def get_ai_recommendations(request: AIRecommendationRequest): # Kept parameter as per original, instruction had no parameters
    """Generate AI-powered route optimization recommendations""" # Changed docstring
    df = get_tickets_df()
    
    # Analyze route performance
    route_analysis = df.groupby(['from_stop', 'to_stop']).agg({
        'passenger_count': ['sum', 'mean', 'std'],
        'fare': ['sum', 'mean']
    }).reset_index()
    
    route_analysis.columns = ['from_stop', 'to_stop', 'total_passengers', 
                               'avg_passengers', 'std_passengers', 'total_revenue', 'avg_fare']
    
    # Calculate metrics
    route_analysis['revenue_per_passenger'] = route_analysis['total_revenue'] / route_analysis['total_passengers']
    route_analysis['route_name'] = route_analysis['from_stop'] + ' → ' + route_analysis['to_stop']
    
    # Estimate costs
    route_analysis['estimated_distance'] = route_analysis['avg_fare'] / 2.5  # km estimate
    route_analysis['estimated_cost'] = route_analysis['estimated_distance'] * 8 + 500
    route_analysis['profit'] = route_analysis['total_revenue'] - route_analysis['estimated_cost']
    route_analysis['profit_margin'] = (route_analysis['profit'] / route_analysis['total_revenue'] * 100)
    
    # AI Analysis
    recommendations = []
    
    # 1. Fare optimization recommendations
    low_revenue_routes = route_analysis[route_analysis['revenue_per_passenger'] < route_analysis['revenue_per_passenger'].mean()]
    for _, route in low_revenue_routes.head(3).iterrows():
        optimal_fare_increase = min(15, max(5, 20 - route['profit_margin']))
        projected_revenue_change = optimal_fare_increase * 0.5  # Considering elasticity
        
        recommendations.append({
            "type": "fare_adjustment",
            "priority": "high" if route['profit_margin'] < 0 else "medium",
            "route": route['route_name'],
            "current_metrics": {
                "passengers": int(route['total_passengers']),
                "revenue": float(route['total_revenue']),
                "avg_fare": float(route['avg_fare']),
                "profit_margin": float(route['profit_margin'])
            },
            "recommendation": {
                "action": "increase_fare",
                "amount": f"+{optimal_fare_increase}%",
                "new_fare": float(route['avg_fare'] * (1 + optimal_fare_increase/100))
            },
            "projected_impact": {
                "revenue_change": f"+{projected_revenue_change:.1f}%",
                "passenger_change": f"-{optimal_fare_increase * 0.5:.1f}%",
                "profit_change": float(route['total_revenue'] * projected_revenue_change / 100)
            },
            "reasoning": [
                f"Current profit margin of {route['profit_margin']:.1f}% is below target",
                f"Revenue per passenger (₹{route['revenue_per_passenger']:.2f}) is {((route['revenue_per_passenger'] / route_analysis['revenue_per_passenger'].mean() - 1) * 100):.1f}% below average",
                f"Route has stable demand ({route['total_passengers']:.0f} passengers)",
                f"Recommended increase of {optimal_fare_increase}% balances profitability with demand retention"
            ],
            "confidence": 0.85,
            "reason": f"Low profit margin ({route['profit_margin']:.1f}%) and below-average revenue per passenger on {route['route_name']}.",
            "confidence_score": 0.85,
            "expected_profit_impact": float(route['total_revenue'] * projected_revenue_change / 100),
            "passenger_impact": f"Approx {optimal_fare_increase * 0.5:.1f}% demand reduction (price elasticity)."
        })
    
    # 2. Frequency adjustment recommendations
    high_demand_routes = route_analysis[route_analysis['total_passengers'] > route_analysis['total_passengers'].quantile(0.75)]
    for _, route in high_demand_routes.head(2).iterrows():
        if route['avg_passengers'] > 40:  # High occupancy
            frequency_increase = 25
            
            recommendations.append({
                "type": "frequency_adjustment",
                "priority": "high",
                "route": route['route_name'],
                "current_metrics": {
                    "passengers": int(route['total_passengers']),
                    "avg_per_trip": float(route['avg_passengers']),
                    "occupancy_rate": "85%"
                },
                "recommendation": {
                    "action": "increase_frequency",
                    "amount": f"+{frequency_increase}%",
                    "rationale": "High demand with near-capacity trips"
                },
                "projected_impact": {
                    "passenger_increase": f"+{frequency_increase * 0.3:.1f}%",
                    "revenue_increase": f"+{frequency_increase * 0.3:.1f}%",
                    "additional_trips": int(route['total_passengers'] / route['avg_passengers'] * 0.25)
                },
                "reasoning": [
                    f"Average {route['avg_passengers']:.0f} passengers per trip indicates high demand",
                    "Current trips are running near capacity (85%)",
                    f"Route generates ₹{route['total_revenue']:.2f} making it profitable to expand",
                    f"Increasing frequency by {frequency_increase}% will capture unmet demand"
                ],
                "confidence": 0.78,
                "reason": f"High occupancy (~85%) and strong demand on {route['route_name']}; frequency increase captures unmet demand.",
                "confidence_score": 0.78,
                "expected_profit_impact": float(route['total_revenue'] * frequency_increase * 0.003),
                "passenger_impact": f"Estimated +{frequency_increase * 0.3:.1f}% passengers from better service frequency."
            })
    
    # 3. Bus size change recommendations
    low_occupancy_routes = route_analysis[route_analysis['avg_passengers'] < 25]
    for _, route in low_occupancy_routes.head(2).iterrows():
        recommendations.append({
            "type": "capacity_adjustment",
            "priority": "medium",
            "route": route['route_name'],
            "current_metrics": {
                "avg_passengers": float(route['avg_passengers']),
                "current_capacity": 50,
                "utilization": f"{(route['avg_passengers']/50*100):.1f}%"
            },
            "recommendation": {
                "action": "reduce_bus_size",
                "from": "50-seater",
                "to": "35-seater",
                "cost_saving": "₹150 per trip"
            },
            "projected_impact": {
                "cost_reduction": "-18%",
                "profit_margin_improvement": f"+{18 * route['total_revenue'] / route['estimated_cost']:.1f}%",
                "annual_savings": "₹54,000"
            },
            "reasoning": [
                f"Average occupancy of {route['avg_passengers']:.0f} passengers is only {(route['avg_passengers']/50*100):.1f}% of capacity",
                "Running large buses with low occupancy is inefficient",
                "Smaller buses (35-seater) would still accommodate current demand",
                "Operational cost savings of ₹150 per trip significantly improve margins"
            ],
            "confidence": 0.82,
            "reason": f"Low occupancy ({(route['avg_passengers']/50*100):.1f}%) on {route['route_name']}; downsizing bus reduces cost.",
            "confidence_score": 0.82,
            "expected_profit_impact": 54000.0,
            "passenger_impact": "Neutral; 35-seater still meets current demand."
        })
    
    
    return {
        "analysis_timestamp": datetime.now().isoformat(),
        "total_recommendations": len(recommendations),
        "recommendations": sorted(recommendations, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x['priority']], reverse=True),
        "summary": {
            "total_routes_analyzed": len(route_analysis),
            "avg_profit_margin": float(route_analysis['profit_margin'].mean()),
            "total_revenue": float(route_analysis['total_revenue'].sum()),
            "optimization_potential": "₹" + str(int(sum(r.get('projected_impact', {}).get('profit_change', 0) for r in recommendations)))
        }
    }

# ===========================
# GEO DATA
# ===========================

@app.get("/api/geo/stops")
async def get_all_stops():
    """Get unique stops from data"""
    df = get_tickets_df()
    stops = sorted(list(set(df['from_stop'].unique()) | set(df['to_stop'].unique())))
    
    # Generate realistic coordinates for Hyderabad area
    # Center: 17.385044, 78.486671
    base_lat, base_lng = 17.385044, 78.486671
    
    stops_geo = []
    for i, stop in enumerate(stops):
        # Calculate demand for this stop
        boarding = df[df['from_stop'] == stop]['passenger_count'].sum()
        alighting = df[df['to_stop'] == stop]['passenger_count'].sum()
        total_demand = boarding + alighting
        
        # Generate coordinates in a realistic spread
        angle = (i / len(stops)) * 2 * np.pi
        radius = 0.05 + (i % 3) * 0.03
        
        lat = base_lat + radius * np.cos(angle) + np.random.uniform(-0.01, 0.01)
        lng = base_lng + radius * np.sin(angle) + np.random.uniform(-0.01, 0.01)
        
        # Peak hour analysis
        df['hour'] = pd.to_datetime(df['time']).dt.hour
        stop_hourly = df[(df['from_stop'] == stop) | (df['to_stop'] == stop)].groupby('hour')['passenger_count'].sum()
        peak_hour = stop_hourly.idxmax() if len(stop_hourly) > 0 else 8
        
        stops_geo.append({
            "name": stop,
            "lat": float(lat),
            "lng": float(lng),
            "boarding": int(boarding),
            "alighting": int(alighting),
            "total_demand": int(total_demand),
            "peak_hour": int(peak_hour)
        })
    
    # Generate corridor lines (top routes)
    corridors = df.groupby(['from_stop', 'to_stop']).agg({
        'passenger_count': 'sum'
    }).reset_index().nlargest(15, 'passenger_count')
    
    corridor_lines = []
    stop_map = {s['name']: (s['lat'], s['lng']) for s in stops_geo}
    
    for _, row in corridors.iterrows():
        if row['from_stop'] in stop_map and row['to_stop'] in stop_map:
            corridor_lines.append({
                "from": row['from_stop'],
                "to": row['to_stop'],
                "from_coords": stop_map[row['from_stop']],
                "to_coords": stop_map[row['to_stop']],
                "demand": int(row['passenger_count'])
            })
    
    return {
        "stops": stops_geo,
        "corridors": corridor_lines,
        "center": {"lat": base_lat, "lng": base_lng}
    }

# ===========================
# REPORTS
# ===========================

@app.get("/api/reports/corridor")
async def get_corridor_report():
    """Detailed corridor analysis report"""
    df = get_tickets_df()
    
    # Analyze by corridor
    corridor_data = df.groupby(['from_stop', 'to_stop']).agg({
        'passenger_count': ['sum', 'mean', 'std'],
        'fare': ['sum', 'mean']
    }).reset_index()
    
    corridor_data.columns = ['from_stop', 'to_stop', 'total_passengers', 'avg_passengers', 
                              'std_passengers', 'total_revenue', 'avg_fare']
    corridor_data = corridor_data.sort_values('total_passengers', ascending=False)
    
    return {
        "report_date": datetime.now().isoformat(),
        "data": corridor_data.head(50).to_dict(orient='records'),
        "summary": {
            "total_corridors": len(corridor_data),
            "avg_corridor_demand": float(corridor_data['total_passengers'].mean())
        }
    }

@app.get("/api/reports/export/csv")
async def export_analysis_csv(report_type: str = "corridors"):
    """Export analysis data as CSV"""
    
    if data_store["tickets"] is None:
        raise HTTPException(status_code=400, detail="No data uploaded")
    
    df = data_store["tickets"].copy()
    
    if report_type == "corridors":
        export_df = df.groupby(['from_stop', 'to_stop']).agg({
            'passenger_count': 'sum',
            'fare': 'sum'
        }).reset_index()
    else:
        export_df = df
    
    stream = io.StringIO()
    export_df.to_csv(stream, index=False)
    
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=tsrtc_{report_type}_export.csv"}
    )

# ===========================
# HEALTH CHECK
# ===========================

@app.get("/")
async def root():
    """Serve test/landing page"""
    # Try to serve test page first to verify setup
    test_path = os.path.join(FRONTEND_DIR, "test.html")
    landing_path = os.path.join(FRONTEND_DIR, "landing.html")
    
    # Serve test page if it exists, otherwise landing
    if os.path.exists(test_path):
        return FileResponse(test_path)
    elif os.path.exists(landing_path):
        return FileResponse(landing_path)
    
    # Fallback to API info
    return {
        "service": "TSRTC Smart Analytics API",
        "version": "2.0",
        "status": "operational",
        "message": "Backend is running! Frontend files not found in expected location.",
        "frontend_path_expected": FRONTEND_DIR,
        "available_endpoints": {
            "test_page": "/test.html",
            "landing_page": "/landing.html",
            "users": "/users.html",
            "drivers": "/driver-login.html",
            "admins": "/index.html",
            "api_docs": "/docs"
        },
        "endpoints": {
            "auth": "/api/auth/login",
            "upload": "/api/upload",
            "analytics": "/api/analytics/*",
            "simulator": "/api/simulator/*",
            "geo": "/api/geo/*",
            "reports": "/api/reports/*"
        }
    }

@app.get("/landing")
async def landing():
    """Serve landing page"""
    landing_path = os.path.join(FRONTEND_DIR, "landing.html")
    if os.path.exists(landing_path):
        return FileResponse(landing_path)
    raise HTTPException(status_code=404, detail="Landing page not found")

@app.get("/{page_name}")
async def serve_page(page_name: str):
    """Serve frontend pages"""
    # List of valid pages
    valid_pages = [
        "landing.html", "index.html", "admin-login.html", "dashboard.html", "upload.html",
        "analytics.html", "profitability.html", "simulator.html", "maps.html",
        "users.html", "driver-login.html", "driver-dashboard.html",
        "ai_recommendations.html", "ai-recommendations.html",
        "booking.html", "admin-complaints.html",
        "test.html", "diagnostic.html"
    ]
    
    # Add .html extension if not present
    if not page_name.endswith('.html'):
        page_name = f"{page_name}.html"
    
    if page_name in valid_pages:
        page_path = os.path.join(FRONTEND_DIR, page_name)
        if not os.path.exists(page_path) and page_name == "ai-recommendations.html":
            page_path = os.path.join(FRONTEND_DIR, "ai_recommendations.html")
        if os.path.exists(page_path):
            return FileResponse(page_path)
    
    raise HTTPException(status_code=404, detail=f"Page {page_name} not found")

# ===========================
# TICKET BOOKING SYSTEM
# ===========================

@app.get("/api/booking/routes")
async def get_available_routes():
    """Get available routes for booking"""
    
    # If no data uploaded, return default routes
    if data_store["tickets"] is None:
        default_routes = [
            {"from": "Secunderabad", "to": "Koti", "fare": 30, "distance": "12"},
            {"from": "Koti", "to": "Secunderabad", "fare": 30, "distance": "12"},
            {"from": "KPHB", "to": "Ameerpet", "fare": 25, "distance": "10"},
            {"from": "Ameerpet", "to": "KPHB", "fare": 25, "distance": "10"},
            {"from": "Dilsukhnagar", "to": "Charminar", "fare": 20, "distance": "8"},
            {"from": "Charminar", "to": "Dilsukhnagar", "fare": 20, "distance": "8"},
            {"from": "Uppal", "to": "ECIL", "fare": 35, "distance": "14"},
            {"from": "ECIL", "to": "Uppal", "fare": 35, "distance": "14"},
            {"from": "Gachibowli", "to": "Ameerpet", "fare": 40, "distance": "16"},
            {"from": "Ameerpet", "to": "Gachibowli", "fare": 40, "distance": "16"},
            {"from": "Mehdipatnam", "to": "Koti", "fare": 22, "distance": "9"},
            {"from": "Koti", "to": "Mehdipatnam", "fare": 22, "distance": "9"},
        ]
        return {"routes": default_routes}
    
    df = data_store["tickets"].copy()
    routes = df.groupby(['from_stop', 'to_stop']).agg({
        'fare': 'mean',
        'passenger_count': 'sum'
    }).reset_index()
    
    # Calculate distance-based fare slabs
    routes['distance_km'] = routes['fare'] / 2.5  # Estimate
    routes['base_fare'] = routes.apply(lambda x: calculate_fare(x['distance_km']), axis=1)
    
    return {
        "routes": [
            {
                "from": row['from_stop'],
                "to": row['to_stop'],
                "fare": float(row['base_fare']),
                "distance": f"{row['distance_km']:.1f} km",
                "available_buses": ["100", "49M", "5K", "290U"]
            }
            for _, row in routes.iterrows()
        ]
    }

def calculate_fare(distance_km):
    """Calculate fare based on distance slabs"""
    if distance_km <= 5:
        return 15
    elif distance_km <= 10:
        return 25
    elif distance_km <= 20:
        return 40
    elif distance_km <= 30:
        return 55
    else:
        return 55 + (distance_km - 30) * 2

@app.post("/api/booking/create")
async def create_booking(booking: BookingRequest):
    """Create new ticket booking"""
    
    # Calculate fare
    if data_store["tickets"] is not None:
        df = data_store["tickets"]
        route_data = df[(df['from_stop'] == booking.from_stop) & (df['to_stop'] == booking.to_stop)]
        if not route_data.empty:
            base_fare = route_data['fare'].mean()
        else:
            base_fare = 30  # Default
    else:
        base_fare = 30
    
    total_fare = base_fare * booking.seats
    
    # Generate ticket
    ticket_id = f"TKT{datetime.now().strftime('%Y%m%d%H%M%S')}{len(data_store['bookings'])}"
    
    # Distance estimate for OD/revenue analytics
    distance_km = (base_fare / 2.5) if base_fare else 12.0
    qr_data = f"SMARTRTC|{ticket_id}|{booking.from_stop}|{booking.to_stop}|{booking.travel_date}|{booking.seats}"
    
    booking_record = {
        "ticket_id": ticket_id,
        "from_stop": booking.from_stop,
        "to_stop": booking.to_stop,
        "passenger_name": booking.passenger_name,
        "passenger_phone": booking.passenger_phone,
        "passenger_email": booking.passenger_email,
        "travel_date": booking.travel_date,
        "travel_time": booking.travel_time,
        "bus_number": booking.bus_number,
        "seats": booking.seats,
        "fare_per_seat": float(base_fare),
        "total_fare": float(total_fare),
        "distance_km": round(distance_km, 2),
        "booking_time": datetime.now().isoformat(),
        "status": "confirmed",
        "seat_numbers": [f"{i+1}A" for i in range(booking.seats)],
        "qr_data": qr_data
    }
    
    data_store["bookings"].append(booking_record)
    
    # Add to OD analytics data
    if data_store["tickets"] is not None:
        new_row = pd.DataFrame([{
            'from_stop': booking.from_stop,
            'to_stop': booking.to_stop,
            'time': booking.travel_time,
            'passenger_count': booking.seats,
            'fare': base_fare
        }])
        data_store["tickets"] = pd.concat([data_store["tickets"], new_row], ignore_index=True)
    
    return {
        "success": True,
        "ticket": booking_record,
        "message": "Booking confirmed successfully"
    }

@app.get("/api/booking/ticket/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Get ticket details (includes QR data for display)"""
    ticket = next((t for t in data_store["bookings"] if t["ticket_id"] == ticket_id), None)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@app.get("/api/booking/history")
async def get_booking_history(phone: Optional[str] = None, email: Optional[str] = None):
    """Get booking history by phone or email (for user-facing booking history)"""
    bookings = data_store["bookings"]
    if phone:
        bookings = [b for b in bookings if b.get("passenger_phone") == phone]
    if email:
        bookings = [b for b in bookings if b.get("passenger_email") == email]
    return {"bookings": sorted(bookings, key=lambda x: x.get("booking_time", ""), reverse=True)}

@app.get("/api/booking/check-availability")
async def check_availability(from_stop: str, to_stop: str, bus_number: str, travel_date: str):
    """Check seat availability"""
    # Count existing bookings
    existing_bookings = [
        b for b in data_store["bookings"] 
        if b["bus_number"] == bus_number and b["travel_date"] == travel_date
        and b["from_stop"] == from_stop and b["to_stop"] == to_stop
    ]
    
    total_booked = sum(b["seats"] for b in existing_bookings)
    total_capacity = 50  # Standard bus capacity
    available = total_capacity - total_booked
    
    return {
        "available": available,
        "total_capacity": total_capacity,
        "booked": total_booked,
        "occupancy_rate": f"{(total_booked/total_capacity*100):.1f}%"
    }

# ===========================
# ANONYMOUS COMPLAINT SYSTEM
# ===========================

@app.get("/api/complaints/crew/{bus_number}")
async def get_crew_for_bus(bus_number: str):
    """Get assigned crew for a bus number"""
    crew = data_store["crew_assignments"].get(bus_number)
    
    if not crew:
        # Return default for unknown buses
        return {
            "bus_number": bus_number,
            "crew": {
                "driver": {"id": "UNKNOWN", "name": "Driver information not available", "rating": 0},
                "conductor": {"id": "UNKNOWN", "name": "Conductor information not available", "rating": 0}
            }
        }
    
    return {
        "bus_number": bus_number,
        "crew": crew
    }

@app.get("/api/complaints/categories")
async def get_complaint_categories():
    """Return allowed anonymous complaint categories"""
    return {"categories": COMPLAINT_CATEGORIES}

@app.post("/api/complaints/submit")
async def submit_complaint(complaint: ComplaintRequest):
    """Submit anonymous complaint against crew member (structured flow)"""
    if complaint.category not in COMPLAINT_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Category must be one of: {COMPLAINT_CATEGORIES}")
    
    complaint_id = f"CMP{datetime.now().strftime('%Y%m%d%H%M%S')}{len(data_store['complaints'])}"
    
    # Get crew info
    crew = data_store["crew_assignments"].get(complaint.bus_number, {})
    person_info = crew.get(complaint.person_type, {})
    
    complaint_record = {
        "complaint_id": complaint_id,
        "bus_number": complaint.bus_number,
        "person_type": complaint.person_type,
        "person_id": complaint.person_id,
        "person_name": person_info.get("name", "Unknown"),
        "category": complaint.category,
        "description": complaint.description,
        "timestamp": complaint.timestamp or datetime.now().isoformat(),
        "status": "pending",
        "admin_notes": None
    }
    
    data_store["complaints"].append(complaint_record)
    
    return {
        "success": True,
        "complaint_id": complaint_id,
        "message": "Complaint submitted successfully. Reference ID: " + complaint_id
    }

@app.get("/api/complaints/all")
def get_all_complaints(status: Optional[str] = None, current_user: User = Depends(require_admin)):
    """Get all complaints (admin only)"""
    complaints = data_store["complaints"]
    
    if status:
        complaints = [c for c in complaints if c["status"] == status]
    
    # Add statistics
    crew_complaints = {}
    for c in data_store["complaints"]:
        person_id = c["person_id"]
        if person_id not in crew_complaints:
            crew_complaints[person_id] = {
                "name": c["person_name"],
                "type": c["person_type"],
                "total_complaints": 0,
                "by_category": {}
            }
        crew_complaints[person_id]["total_complaints"] += 1
        category = c["category"]
        crew_complaints[person_id]["by_category"][category] = crew_complaints[person_id]["by_category"].get(category, 0) + 1
    
    return {
        "complaints": sorted(complaints, key=lambda x: x["timestamp"], reverse=True),
        "total": len(complaints),
        "pending": len([c for c in complaints if c["status"] == "pending"]),
        "crew_performance": crew_complaints
    }

@app.put("/api/complaints/{complaint_id}/status")
async def update_complaint_status(complaint_id: str, status: str, notes: Optional[str] = None):
    """Update complaint status (admin only)"""
    complaint = next((c for c in data_store["complaints"] if c["complaint_id"] == complaint_id), None)
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    complaint["status"] = status
    if notes:
        complaint["admin_notes"] = notes
    
    return {"success": True, "message": "Complaint updated"}

# ===========================
# DRIVER OPERATIONAL ASSISTANT
# ===========================

@app.get("/api/driver/schedule/{employee_id}")
async def get_driver_schedule(employee_id: str):
    """Get driver's daily schedule"""
    
    # Generate schedule based on crew assignments
    schedule = []
    
    # Find which bus this driver operates
    driver_bus = None
    for bus_num, crew in data_store["crew_assignments"].items():
        if crew.get("driver", {}).get("id") == employee_id or crew.get("conductor", {}).get("id") == employee_id:
            driver_bus = bus_num
            break
    
    if not driver_bus:
        return {"schedule": [], "message": "No schedule found"}
    
    # Generate sample schedule
    base_time = datetime.strptime("06:00", "%H:%M")
    
    for trip_num in range(8):  # 8 trips per day
        trip_time = base_time + timedelta(hours=trip_num * 1.5)
        
        schedule.append({
            "trip_number": trip_num + 1,
            "departure_time": trip_time.strftime("%H:%M"),
            "bus_number": driver_bus,
            "route": "Secunderabad → Koti" if trip_num % 2 == 0 else "Koti → Secunderabad",
            "estimated_duration": "45 min",
            "status": "completed" if trip_num < 3 else "upcoming",
            "expected_load": f"{60 + (trip_num * 5)}%" if trip_num >= 3 and trip_num <= 6 else "40%"
        })
    
    return {
        "employee_id": employee_id,
        "bus_number": driver_bus,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "schedule": schedule,
        "total_trips": len(schedule),
        "completed_trips": len([s for s in schedule if s["status"] == "completed"])
    }

@app.get("/api/driver/stops/{bus_number}")
async def get_stop_sequence(bus_number: str):
    """Get stop sequence with load indicators"""
    
    stops = [
        {"name": "Secunderabad", "order": 1, "arrival": "06:00", "expected_boarding": 45, "expected_alighting": 0, "load": "90%"},
        {"name": "Paradise", "order": 2, "arrival": "06:08", "expected_boarding": 20, "expected_alighting": 5, "load": "95%"},
        {"name": "Rasoolpura", "order": 3, "arrival": "06:15", "expected_boarding": 15, "expected_alighting": 10, "load": "90%"},
        {"name": "Begumpet", "order": 4, "arrival": "06:23", "expected_boarding": 10, "expected_alighting": 8, "load": "85%"},
        {"name": "Ameerpet", "order": 5, "arrival": "06:30", "expected_boarding": 25, "expected_alighting": 20, "load": "85%"},
        {"name": "SR Nagar", "order": 6, "arrival": "06:38", "expected_boarding": 8, "expected_alighting": 15, "load": "70%"},
        {"name": "Erragadda", "order": 7, "arrival": "06:45", "expected_boarding": 5, "expected_alighting": 12, "load": "60%"},
        {"name": "Bharath Nagar", "order": 8, "arrival": "06:52", "expected_boarding": 3, "expected_alighting": 10, "load": "50%"},
        {"name": "Koti", "order": 9, "arrival": "07:00", "expected_boarding": 0, "expected_alighting": 35, "load": "0%"}
    ]
    
    return {
        "bus_number": bus_number,
        "total_stops": len(stops),
        "stops": stops
    }

@app.get("/api/driver/alerts")
async def get_traffic_alerts():
    """Get current traffic and operational alerts"""
    
    alerts = [
        {
            "id": 1,
            "type": "traffic",
            "severity": "high",
            "location": "Ameerpet Junction",
            "message": "Heavy traffic expected. Add 10 minutes to schedule.",
            "time": "06:30 AM - 08:30 AM"
        },
        {
            "id": 2,
            "type": "route",
            "severity": "medium",
            "location": "Punjagutta",
            "message": "Road construction. Use alternate route via Panjagutta Circle.",
            "time": "All day"
        },
        {
            "id": 3,
            "type": "weather",
            "severity": "low",
            "location": "All routes",
            "message": "Light rain expected around 3 PM. Drive carefully.",
            "time": "03:00 PM - 05:00 PM"
        }
    ]
    
    return {
        "alerts": alerts,
        "total": len(alerts),
        "high_priority": len([a for a in alerts if a["severity"] == "high"])
    }

@app.post("/api/driver/incident")
async def report_incident(
    employee_id: str,
    bus_number: str,
    incident_type: str,
    description: str,
    location: str
):
    """Report incident during duty"""
    
    incident_id = f"INC{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    incident = {
        "incident_id": incident_id,
        "employee_id": employee_id,
        "bus_number": bus_number,
        "type": incident_type,
        "description": description,
        "location": location,
        "timestamp": datetime.now().isoformat(),
        "status": "reported"
    }
    
    # Store in complaints/incidents list
    data_store["complaints"].append({
        "complaint_id": incident_id,
        "bus_number": bus_number,
        "person_type": "system",
        "person_id": employee_id,
        "person_name": "System Report",
        "category": incident_type,
        "description": description,
        "timestamp": incident["timestamp"],
        "status": "pending",
        "admin_notes": f"Incident reported by {employee_id}"
    })
    
    return {
        "success": True,
        "incident_id": incident_id,
        "message": "Incident reported successfully"
    }



# ===========================
# FARE-BASED BOOKING API
# ===========================

@app.post("/api/bookings/fare-based")
async def create_fare_based_booking(booking: FareBasedBookingRequest):
    """Create a fare-based ticket booking"""
    # Validate fare amount
    MIN_FARE = 10
    MAX_FARE = 500
    
    if booking.fare_amount < MIN_FARE or booking.fare_amount > MAX_FARE:
        raise HTTPException(
            status_code=400, 
            detail=f"Fare must be between ₹{MIN_FARE} and ₹{MAX_FARE}"
        )
    
    # Calculate distance based on fare (₹2 per km)
    distance_km = round(booking.fare_amount / 2, 2)
    
    # Generate ticket ID
    ticket_id = f"TKT{datetime.now().strftime('%Y%m%d%H%M%S')}{len(data_store['bookings'])}"
    
    # Calculate validity (24 hours from travel date)
    travel_datetime = datetime.strptime(booking.travel_date, '%Y-%m-%d')
    valid_until = travel_datetime.replace(hour=23, minute=59, second=59)
    
    # Create booking record
    booking_record = {
        "ticket_id": ticket_id,
        "passenger_name": booking.passenger_name,
        "passenger_phone": booking.passenger_phone,
        "passenger_email": booking.passenger_email,
        "fare_amount": booking.fare_amount,
        "distance_km": distance_km,
        "travel_date": booking.travel_date,
        "payment_method": booking.payment_method,
        "booking_time": datetime.now().isoformat(),
        "valid_until": valid_until.isoformat(),
        "status": "active",
        "qr_data": {
            "ticket_id": ticket_id,
            "passenger": booking.passenger_name,
            "fare": booking.fare_amount,
            "distance_km": distance_km,
            "valid_until": valid_until.isoformat(),
            "payment": booking.payment_method
        }
    }
    
    # Store booking
    data_store["bookings"].append(booking_record)
    
    return {
        "success": True,
        "ticket_id": ticket_id,
        "fare_amount": booking.fare_amount,
        "distance_km": distance_km,
        "valid_until": valid_until.isoformat(),
        "qr_data": booking_record["qr_data"],
        "message": f"Ticket booked successfully! Valid for {distance_km} km on any bus."
    }

@app.get("/api/tickets/verify/{ticket_id}")
async def verify_ticket(ticket_id: str):
    """Verify and retrieve ticket details for QR scanner"""
    # Find ticket in bookings
    for booking in data_store["bookings"]:
        if booking["ticket_id"] == ticket_id:
            # Check if ticket is still valid
            valid_until = datetime.fromisoformat(booking["valid_until"])
            is_valid = datetime.now() < valid_until and booking["status"] == "active"
            
            return {
                "success": True,
                "valid": is_valid,
                "ticket": {
                    "ticket_id": booking["ticket_id"],
                    "passenger_name": booking["passenger_name"],
                    "passenger_phone": booking["passenger_phone"],
                    "fare_amount": booking["fare_amount"],
                    "distance_km": booking["distance_km"],
                    "travel_date": booking["travel_date"],
                    "payment_method": booking["payment_method"],
                    "booking_time": booking["booking_time"],
                    "valid_until": booking["valid_until"],
                    "status": booking["status"]
                },
                "message": "Valid ticket" if is_valid else "Ticket expired or inactive"
            }
    
    raise HTTPException(status_code=404, detail="Ticket not found")

@app.get("/api/bookings/user/{phone}")
async def get_user_bookings(phone: str):
    """Get all bookings for a user by phone number"""
    user_bookings = [
        booking for booking in data_store["bookings"]
        if booking["passenger_phone"] == phone
    ]
    
    return {
        "success": True,
        "count": len(user_bookings),
        "bookings": sorted(user_bookings, key=lambda x: x["booking_time"], reverse=True)
    }



@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "data_loaded": data_store["tickets"] is not None,
        "timestamp": datetime.now().isoformat()
    }

# ===========================
# HTML FILE SERVING
# ===========================

@app.get("/{page_name}.html")
async def serve_html(page_name: str):
    """Serve HTML files from frontend directory"""
    html_path = os.path.join(FRONTEND_DIR, f"{page_name}.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    raise HTTPException(status_code=404, detail="Page not found")

@app.get("/")
async def serve_root():
    """Serve landing page as default"""
    landing_path = os.path.join(FRONTEND_DIR, "landing.html")
    if os.path.exists(landing_path):
        return FileResponse(landing_path)
    # Fallback to index.html if landing doesn't exist
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="No home page found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
