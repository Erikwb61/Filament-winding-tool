#!/usr/bin/env python3
"""Quick API Test"""
import requests
import json
import time

time.sleep(2)  # Warte auf Server

BASE_URL = 'http://localhost:5000'

print("\n=== TEST: /api/laminate-properties ===\n")

payload = {
    'sequence': '[0/±45/90]s',
    'ply_thickness_mm': 0.125,
    'material': 'M40J'
}

try:
    response = requests.post(f'{BASE_URL}/api/laminate-properties', json=payload, timeout=5)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"ERROR: {e}")
