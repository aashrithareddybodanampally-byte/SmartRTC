# Registration endpoints - to be added after the verify endpoint in main.py

# ===========================
# REGISTRATION ENDPOINTS
# ===========================

@app.post("/api/auth/register")
async def register_user(registration: Registration Request):
    """Submit new user registration"""
    # Check if username already exists
    if registration.username in data_store["users"]:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email already registered
    for user in data_store["registrations"]:
        if user.get("email") == registration.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if employee_id already registered
    for user in data_store["registrations"]:
        if user.get("employee_id") == registration.employee_id:
            raise HTTPException(status_code=400, detail="Employee ID already registered")
    
    # Hash password
    hashed_password = pwd_context.hash(registration.password)
    
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
async def approve_registration(registration_id: str, notes: Optional[str] = None):
    """Approve a registration (admin only)"""
    registration = next((r for r in data_store["registrations"] if r["registration_id"] == registration_id), None)
    
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    # Move to users
    # Determine role based on designation
    role_mapping = {
        "driver": "driver",
        "conductor": "conductor",
        "admin": "admin",
        "planner": "planner",
        "viewer": "viewer"
    }
    role = role_mapping.get(registration["designation"], "viewer")
    
    data_store["users"][registration["username"]] = {
        "password": registration["password"],
        "role": role,
        "full_name": registration["full_name"],
        "email": registration["email"],
        "phone": registration["phone"],
        "designation": registration["designation"],
        "employee_id": registration["employee_id"],
        "approval_status": "approved",
        "approved_at": datetime.now().isoformat()
    }
    
    # Update registration status
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
