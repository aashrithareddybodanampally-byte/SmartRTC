#!/usr/bin/env python3
"""
SmartRTC Sample Data Generator
Generates sample CSV and JSON data for tickets, passenger_logs, revenue, costs.
"""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(exist_ok=True)

STOPS = [
    "Secunderabad", "Paradise", "Rasoolpura", "Begumpet", "Ameerpet",
    "SR Nagar", "Erragadda", "Bharath Nagar", "Koti", "KPHB", "Dilsukhnagar",
    "Charminar", "Uppal", "LB Nagar", "Dilsukhnagar"
]

BUS_NUMBERS = ["100", "49M", "5K", "290U"]

def distance_km(from_s, to_s):
    i, j = STOPS.index(from_s) if from_s in STOPS else 0, STOPS.index(to_s) if to_s in STOPS else 0
    return round(abs(i - j) * 2.5 + random.uniform(1, 5), 2)

def fare_for_km(km):
    if km <= 5: return 15
    if km <= 10: return 25
    if km <= 20: return 40
    if km <= 30: return 55
    return 55 + (km - 30) * 2

def generate_ticket_data(rows=500):
    path = DATA_DIR / "sample_ticket_data.csv"
    start = datetime.now() - timedelta(days=30)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["from_stop", "to_stop", "time", "passenger_count", "fare"])
        for _ in range(rows):
            from_s = random.choice(STOPS)
            to_s = random.choice([s for s in STOPS if s != from_s])
            dt = start + timedelta(minutes=random.randint(0, 30*24*60))
            pax = random.randint(1, 10)
            km = distance_km(from_s, to_s)
            fare = fare_for_km(km) * pax
            w.writerow([from_s, to_s, dt.strftime("%Y-%m-%d %H:%M:%S"), pax, round(fare, 2)])
    print(f"Generated {path} with {rows} rows")

if __name__ == "__main__":
    generate_ticket_data(500)
