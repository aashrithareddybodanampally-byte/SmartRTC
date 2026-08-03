# 🚀 QUICK START GUIDE

Get TSRTC Analytics Platform running in 3 minutes!

## For Linux/Mac:

```bash
# 1. Navigate to the project
cd tsrtc-platform

# 2. Run the startup script
./start.sh
```

## For Windows:

```bash
# 1. Navigate to the project
cd tsrtc-platform

# 2. Run the startup script
start.bat
```

## Manual Setup:

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Start Backend
```bash
cd backend
python main.py
```

Backend will start on: http://localhost:8000

### Step 3: Open Frontend

**Option A:** Direct File Access
- Simply open `frontend/index.html` in your browser

**Option B:** HTTP Server (Recommended)
```bash
cd frontend
python -m http.server 8080
```
Then open: http://localhost:8080

## First Login:

Use these credentials:
- **Username:** admin
- **Password:** admin123

## Getting Started:

1. **Login** with admin credentials
2. **Upload Sample Data:**
   - Click "Upload Data" in navigation
   - Click "Download Sample CSV" 
   - Upload the downloaded file (or use `data/sample_ticket_data.csv`)
3. **Explore Features:**
   - Dashboard - Overview metrics
   - OD Analytics - Demand analysis
   - Profitability - Route profits/losses
   - Simulator - What-if scenarios
   - Maps - Geographical view

## Troubleshooting:

### Backend won't start?
```bash
pip install --upgrade pip
pip install -r requirements.txt --break-system-packages
```

### Can't access frontend?
- Make sure backend is running on port 8000
- Check if API_BASE in `frontend/js/app.js` is correct
- Try using the HTTP server method

### No data showing?
- Upload CSV data first
- Check validation report
- Verify CSV format matches requirements

## Need Help?

Check the full README.md for detailed documentation.

---

**Built for TSRTC Hackathon 🏆**