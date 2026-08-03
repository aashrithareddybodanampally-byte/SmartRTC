#!/usr/bin/env python3
"""
Fix numpy serialization issues in simple_main.py
"""

import re

def fix_numpy_issues():
    # Read the current simple_main.py
    with open('simple_main.py', 'r') as f:
        content = f.read()
    
    # Add numpy to Python conversion function
    numpy_fix = """
def convert_numpy_types(obj):
    \"\"\"Convert numpy types to native Python types for JSON serialization\"\"\"
    if hasattr(obj, 'item'):
        return obj.item()
    elif hasattr(obj, 'tolist'):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

"""
    
    # Insert the conversion function after imports
    content = content.replace('from collections import defaultdict', 'from collections import defaultdict' + numpy_fix)
    
    # Fix the profitability endpoint
    profitability_fix = '''@app.get("/api/analytics/profitability")
async def get_profitability():
    \"\"\"Get route profitability analysis\"\"\"
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
        raise HTTPException(status_code=500, detail=str(e))'''
    
    # Replace the profitability endpoint
    profitability_pattern = r'@app\.get\("/api/analytics/profitability"\).*?raise HTTPException\(status_code=500, detail=str\(e\)\)'
    content = re.sub(profitability_pattern, profitability_fix, content, flags=re.DOTALL)
    
    # Fix the simulator endpoint
    simulator_fix = '''@app.post("/api/simulator/whatif")
async def run_simulation(params: dict):
    \"\"\"Run what-if simulation\"\"\"
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
        raise HTTPException(status_code=500, detail=str(e))'''
    
    # Replace the simulator endpoint
    simulator_pattern = r'@app\.post\("/api/simulator/whatif"\).*?raise HTTPException\(status_code=500, detail=str\(e\)\)'
    content = re.sub(simulator_pattern, simulator_fix, content, flags=re.DOTALL)
    
    # Write the fixed content
    with open('simple_main.py', 'w') as f:
        f.write(content)
    
    print("Fixed numpy serialization issues")

if __name__ == "__main__":
    fix_numpy_issues()
