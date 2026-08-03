# 🚀 TSRTC Smart Analytics Platform

**Enterprise-Grade Transport Data Analytics & Optimization System**

A production-ready web platform for analyzing bus ticket data, optimizing routes, and simulating strategic decisions for the Telangana State Road Transport Corporation (TSRTC).

---

## ✨ Features

### Core Modules

1. **📤 Data Upload & Validation**
   - CSV drag-and-drop interface
   - Real-time data quality analysis
   - Automatic error detection
   - Preview and validation reports

2. **📊 Origin-Destination (OD) Analytics**
   - Passenger demand matrix
   - Hourly demand patterns
   - Peak hour identification
   - Top corridor analysis
   - Interactive filtering

3. **💰 Route Profitability Engine**
   - Revenue vs cost analysis
   - Profit/loss tracking per route
   - Margin calculations
   - Route optimization recommendations

4. **🔬 What-If Simulator** *(Judges' WOW Feature)*
   - Interactive fare adjustment
   - Frequency modification
   - Capacity planning
   - Real-time impact analysis
   - Before/after comparisons
   - ROI calculations

5. **🗺️ Geographical Analytics**
   - Interactive map visualization
   - Stop demand intensity
   - Corridor flow lines
   - Click-to-explore interface

6. **🔐 Authentication System**
   - JWT-based security
   - Role-based access (Admin, Planner, Viewer)
   - Session persistence

7. **📄 Reports & Export**
   - CSV export functionality
   - Corridor analysis reports
   - Profit/loss summaries

---

## 🎨 Design System

**Aesthetic:** Mission Control × Modern Fintech

- **Dark Theme** with deep blues and electric accents
- **Glassmorphism** cards with backdrop blur
- **Animated Metrics** with smooth count-up effects
- **Premium Typography** (Rajdhani + Plus Jakarta Sans)
- **Responsive Design** for all screen sizes

---

## 🛠️ Tech Stack

### Backend
- **Python 3.8+** with FastAPI
- **Pandas & NumPy** for data processing
- **JWT** for authentication
- **Uvicorn** ASGI server

### Frontend
- **HTML5 / CSS3 / Vanilla JavaScript**
- **Chart.js** for data visualization
- **Leaflet** for interactive maps
- **Modular ES6** architecture

---

## 📋 Prerequisites

- Python 3.8 or higher
- pip package manager
- Modern web browser (Chrome, Firefox, Safari, Edge)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start Backend Server

```bash
cd backend
python main.py
```

The API will be available at: `http://localhost:8000`

### 3. Start Frontend

Open `frontend/index.html` in your browser, or use a simple HTTP server:

```bash
cd frontend
python -m http.server 8080
```

Then navigate to: `http://localhost:8080`

---

## 🔑 Demo Credentials

| Role    | Username  | Password     | Permissions           |
|---------|-----------|--------------|----------------------|
| Admin   | `admin`   | `admin123`   | Full access          |
| Planner | `planner` | `planner123` | Analytics & simulator|
| Viewer  | `viewer`  | `viewer123`  | Read-only access     |

---

## 📊 CSV Data Format

### Required Columns

```csv
from_stop,to_stop,time,passenger_count,fare
Secunderabad,Koti,2024-01-15 08:30:00,45,25
KPHB,Ameerpet,2024-01-15 09:15:00,38,30
```

### Field Specifications

- **from_stop**: Origin bus stop name (string)
- **to_stop**: Destination bus stop name (string)
- **time**: Journey timestamp (YYYY-MM-DD HH:MM:SS)
- **passenger_count**: Number of passengers (positive integer)
- **fare**: Ticket fare in INR (positive number)

### Download Sample

Click "📥 Download Sample CSV" in the Upload Data page to get a template file.

---

## 🎯 User Workflow

### First Time Setup

1. **Login** with demo credentials
2. **Upload CSV** data file
3. View **validation report**
4. Proceed to analytics

### Daily Operations

1. **Dashboard** - View key metrics
2. **OD Analytics** - Analyze passenger flow
3. **Profitability** - Identify profitable routes
4. **Simulator** - Test strategic changes
5. **Maps** - Explore geographical patterns

---

## 📁 Project Structure

```
tsrtc-platform/
├── backend/
│   ├── main.py              # FastAPI application
│   └── requirements.txt     # Python dependencies
│
└── frontend/
    ├── index.html           # Login page
    ├── dashboard.html       # Main dashboard
    ├── upload.html          # Data upload
    ├── analytics.html       # OD analytics
    ├── profitability.html   # Route profitability
    ├── simulator.html       # What-if simulator
    ├── maps.html           # Geo visualization
    │
    ├── css/
    │   └── styles.css      # Premium styling
    │
    └── js/
        └── app.js          # Core application logic
```

---

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/verify` - Verify token

### Data Management
- `POST /api/upload` - Upload CSV data
- `GET /api/sample-csv` - Download sample CSV

### Analytics
- `GET /api/analytics/od-matrix` - OD demand analysis
- `GET /api/analytics/profitability` - Route profitability
- `POST /api/simulator/whatif` - Run simulation

### Geo Data
- `GET /api/geo/stops` - Stop locations & corridors

### Reports
- `GET /api/reports/corridor` - Corridor report
- `GET /api/reports/export/csv` - Export as CSV

---

## 🎨 Key Features Showcase

### 1. Smart Data Validation
- Automatic header detection
- Missing value analysis
- Data type validation
- Duplicate detection
- Quality scoring

### 2. Interactive Visualizations
- Animated metric cards
- Real-time charts
- Heatmaps
- Time-series analysis
- Geographical plotting

### 3. What-If Simulator
- **Fare Adjustment**: -50% to +50%
- **Frequency Change**: -50% to +100%
- **Capacity Modification**: -30% to +30%
- **Impact Analysis**: Before/after comparison
- **ROI Calculation**: Investment returns

### 4. Geo Intelligence
- Interactive Leaflet maps
- Demand-based color coding
- Corridor flow visualization
- Click-to-explore stops
- Real-time filtering

---

## 🏆 Hackathon Highlights

### Production-Ready Features
✅ Real analytics algorithms (not hardcoded)  
✅ End-to-end data flow  
✅ Premium UI/UX design  
✅ Responsive layout  
✅ Error handling  
✅ Loading states  
✅ Toast notifications  

### Enterprise Grade
✅ JWT authentication  
✅ Role-based access  
✅ API documentation  
✅ Data validation  
✅ Export functionality  
✅ Scalable architecture  

### WOW Factor
✅ Interactive what-if simulator  
✅ Glassmorphism UI  
✅ Animated metrics  
✅ Live map visualization  
✅ Professional typography  
✅ Smooth transitions  

---

## 🔧 Configuration

### Backend Port
Edit `main.py` to change the port:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### API Base URL
Edit `frontend/js/app.js`:
```javascript
const API_BASE = 'http://localhost:8000';
```

---

## 📈 Performance Optimization

- **Lazy Loading**: Charts loaded on demand
- **Data Caching**: Reduced API calls
- **Debounced Filters**: Smooth user experience
- **Optimized Queries**: Fast data processing
- **Minified Assets**: Quick page loads

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt --break-system-packages
```

### CORS errors
- Ensure backend is running on port 8000
- Check browser console for errors
- Verify API_BASE URL in app.js

### No data showing
1. Upload CSV data first
2. Check validation report
3. Ensure data format matches requirements
4. Check browser console for errors

---

## 🚀 Production Deployment

### Backend
```bash
# Using gunicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend
- Deploy to any static hosting (Netlify, Vercel, GitHub Pages)
- Update API_BASE to production backend URL

---

## 📝 Future Enhancements

- [ ] Real-time data streaming
- [ ] Machine learning predictions
- [ ] Multi-depot support
- [ ] Mobile app
- [ ] Advanced reporting
- [ ] Email notifications
- [ ] PDF export
- [ ] Schedule optimization

---

## 👥 Team

Built for TSRTC Hackathon by the Analytics Team

---

## 📄 License

This is a hackathon demonstration project.

---

## 🙏 Acknowledgments

- TSRTC for the opportunity
- Chart.js for visualization library
- Leaflet for mapping solution
- FastAPI for the excellent framework

---

## 📞 Support

For issues or questions:
- Check documentation
- Review API responses
- Verify data format
- Check browser console

---

**Built with ❤️ for TSRTC**

*Making public transport smarter, one route at a time.*