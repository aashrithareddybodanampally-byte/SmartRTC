"""
TSRTC Smart Analytics Platform - Simplified Backend API
Temporary fix for bcrypt issues
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import json
from collections import defaultdict
def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if hasattr(obj, 'item'):
        return obj.item()
    elif hasattr(obj, 'tolist'):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj


import os

# Initialize FastAPI
app = FastAPI(title="TSRTC Analytics API", version="2.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = "tsrtc-hackathon-secret-key-2024"
ALGORITHM = "HS256"

# Simple authentication (plain text for demo)
def hash_password(password: str):
    return password  # Plain text for demo

def verify_password(plain_password, hashed_password):
    return plain_password == hashed_password

# In-memory data storage (for demo)
data_store = {
    "tickets": None,
    "bookings": [],
    "complaints": [],
    "crew_assignments": {},
    "registrations": [],
    "users": {
        "admin": {"password": "admin123", "role": "admin"},
        "planner": {"password": "planner123", "role": "planner"},
        "viewer": {"password": "viewer123", "role": "viewer"}
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

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

# Authentication endpoints
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    
    # Check in-memory users for demo accounts
    if request.username in data_store["users"]:
        user_data = data_store["users"][request.username]
        if verify_password(request.password, user_data["password"]):
            # Create simple token (in production, use proper JWT)
            access_token = f"simple_token_{request.username}_{datetime.now().timestamp()}"
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "username": request.username,
                    "role": user_data["role"]
                }
            }
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/auth/verify")
async def verify_token():
    """Simple token verification for demo"""
    return {"valid": True, "user": {"username": "admin", "role": "admin"}}

# Data upload endpoint
@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload and process CSV data"""
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Validate required columns
        required_columns = ['from_stop', 'to_stop', 'time', 'passenger_count', 'fare']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Store the data
        data_store["tickets"] = df
        
        return {
            "message": "File uploaded successfully",
            "rows": len(df),
            "columns": list(df.columns),
            "preview": df.head().to_dict('records')
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.get("/api/sample-csv")
async def download_sample_csv():
    """Download sample CSV file"""
    sample_data = """from_stop,to_stop,time,passenger_count,fare
Secunderabad,Koti,2024-01-15 08:30:00,45,25
KPHB,Ameerpet,2024-01-15 09:15:00,38,30
Banjara Hills,Secunderabad,2024-01-15 10:00:00,52,35
Hitech City,Kukatpally,2024-01-15 11:30:00,41,28
Dilsukhnagar,Begumpet,2024-01-15 12:45:00,37,22"""
    
    return StreamingResponse(
        io.StringIO(sample_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_tickets.csv"}
    )

# Analytics endpoints
@app.get("/api/analytics/od-matrix")
async def get_od_matrix():
    """Get origin-destination demand matrix"""
    try:
        df = get_tickets_df()
        
        # Group by origin-destination
        od_data = df.groupby(['from_stop', 'to_stop']).agg({
            'passenger_count': 'sum',
            'fare': 'sum'
        }).reset_index()
        
        # Get top routes
        top_routes = od_data.nlargest(10, 'passenger_count')
        
        return {
            "od_matrix": od_data.to_dict('records'),
            "top_routes": top_routes.to_dict('records'),
            "total_routes": len(od_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/profitability")
async def get_profitability():
    """Get route profitability analysis"""
    try:
        df = get_tickets_df()
        
        # Calculate profitability per route
        route_data = df.groupby(['from_stop', 'to_stop']).agg({
            'fare': 'sum',
            'passenger_count': 'sum'
        }).reset_index()
        
        # Assume cost per passenger (simplified)
        route_data['cost'] = route_data['passenger_count'] * 15  # Assume 15 INR per passenger cost
        route_data['profit'] = route_data['fare'] - route_data['cost']
        route_data['margin'] = (route_data['profit'] / route_data['fare'] * 100).round(2)
        
        # Sort by profit
        route_data = route_data.sort_values('profit', ascending=False)
        
        # Convert to dict and fix numpy types
        routes_dict = route_data.to_dict('records')
        routes_dict = convert_numpy_types(routes_dict)
        
        total_revenue = float(route_data['fare'].sum())
        total_cost = float(route_data['cost'].sum())
        total_profit = float(route_data['profit'].sum())
        
        return {
            "routes": routes_dict,
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "total_profit": total_profit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulator/whatif")
async def run_simulation(params: dict):
    """Run what-if simulation"""
    try:
        df = get_tickets_df()
        
        # Get simulation parameters
        fare_change = params.get('fare_change', 0)
        frequency_change = params.get('frequency_change', 0)
        capacity_change = params.get('capacity_change', 0)
        
        # Apply changes (simplified simulation)
        original_revenue = float(df['fare'].sum())
        original_passengers = float(df['passenger_count'].sum())
        
        # Calculate new values (simplified elasticity model)
        fare_multiplier = 1 + (fare_change / 100)
        demand_elasticity = -0.5  # Simplified elasticity
        
        new_fare = df['fare'] * fare_multiplier
        demand_multiplier = 1 + (demand_elasticity * fare_change / 100)
        new_passengers = df['passenger_count'] * demand_multiplier * (1 + frequency_change / 100)
        
        new_revenue = float((new_fare * new_passengers).sum())
        
        return {
            "original": {
                "revenue": original_revenue,
                "passengers": original_passengers
            },
            "simulated": {
                "revenue": new_revenue,
                "passengers": float(new_passengers.sum())
            },
            "impact": {
                "revenue_change": new_revenue - original_revenue,
                "revenue_change_percent": round(((new_revenue - original_revenue) / original_revenue * 100), 2),
                "passenger_change": float(new_passengers.sum()) - original_passengers,
                "passenger_change_percent": round(((float(new_passengers.sum()) - original_passengers) / original_passengers * 100), 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/geo/stops")
async def get_geo_data():
    """Get geographical data for stops"""
    # Sample geo data (in production, this would come from a real geocoding service)
    stops_data = [
        {"name": "Secunderabad", "lat": 17.4458, "lon": 78.4966, "demand": 1200},
        {"name": "Koti", "lat": 17.3761, "lon": 78.4933, "demand": 980},
        {"name": "KPHB", "lat": 17.4948, "lon": 78.3996, "demand": 850},
        {"name": "Ameerpet", "lat": 17.4375, "lon": 78.4483, "demand": 1100},
        {"name": "Banjara Hills", "lat": 17.4135, "lon": 78.4555, "demand": 920},
        {"name": "Hitech City", "lat": 17.4483, "lon": 78.3806, "demand": 780},
        {"name": "Dilsukhnagar", "lat": 17.3686, "lon": 78.5243, "demand": 890},
        {"name": "Begumpet", "lat": 17.4417, "lon": 78.4794, "demand": 950}
    ]
    
    return {"stops": stops_data}

@app.get("/api/reports/corridor")
async def get_corridor_report():
    """Get corridor analysis report"""
    try:
        df = get_tickets_df()
        
        # Simple corridor analysis
        corridor_data = df.groupby('from_stop').agg({
            'passenger_count': 'sum',
            'fare': 'sum'
        }).reset_index()
        
        corridor_data = corridor_data.sort_values('passenger_count', ascending=False)
        
        return {
            "corridors": corridor_data.to_dict('records'),
            "total_corridors": len(corridor_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/export/csv")
async def export_csv():
    """Export data as CSV"""
    try:
        df = get_tickets_df()
        
        return StreamingResponse(
            io.StringIO(df.to_csv(index=False)),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=exported_tickets.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Mount static files (frontend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
