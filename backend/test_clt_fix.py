#!/usr/bin/env python3
"""Test CLT Endpoints nach Fix"""
import requests
import json
import time

time.sleep(3)  # Wait for server

BASE_URL = 'http://localhost:5000'

print("\n=== TEST 1: /api/laminate-properties ===\n")

payload1 = {
    'sequence': '[0/±45/90]s',
    'ply_thickness_mm': 0.125,
    'material': 'M40J'
}

try:
    r = requests.post(f'{BASE_URL}/api/laminate-properties', json=payload1, timeout=5)
    print(f"Status: {r.status_code}")
    result = r.json()
    if result.get('success'):
        print("✅ CLT Laminate Properties SUCCESS!")
        props = result['effective_properties']
        print(f"  E_x: {props['E_x_GPa']} GPa")
        print(f"  E_y: {props['E_y_GPa']} GPa")
        print(f"  G_xy: {props['G_xy_GPa']} GPa")
    else:
        print(f"❌ ERROR: {result.get('error')}")
        print(f"Traceback: {result.get('traceback')[:500]}...")
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n=== TEST 2: /api/failure-analysis ===\n")

payload2 = {
    'sequence': '[0/±45/90]s',
    'ply_thickness_mm': 0.125,
    'material': 'M40J',
    'N_x': 1000,
    'N_y': 0,
    'N_xy': 0
}

try:
    r = requests.post(f'{BASE_URL}/api/failure-analysis', json=payload2, timeout=5)
    print(f"Status: {r.status_code}")
    result = r.json()
    if result.get('success'):
        print("✅ Failure Analysis SUCCESS!")
        ga = result['global_analysis']
        print(f"  Min SF: {ga['min_safety_factor']}")
        print(f"  Critical Ply: {ga['critical_ply_id']}")
        print(f"  Status: {ga['design_status']}")
    else:
        print(f"❌ ERROR: {result.get('error')}")
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n=== TEST 3: /api/tolerance-study ===\n")

payload3 = {
    'sequence': '[0/±45/90]s',
    'ply_thickness_mm': 0.125,
    'material': 'M40J',
    'num_samples': 200,  # Smaller for quick test
    'angle_tolerance_deg': 1.0,
    'thickness_tolerance_pct': 5.0
}

try:
    r = requests.post(f'{BASE_URL}/api/tolerance-study', json=payload3, timeout=10)
    print(f"Status: {r.status_code}")
    result = r.json()
    if result.get('success'):
        print("✅ Tolerance Study SUCCESS!")
        props = result['property_statistics']
        print(f"  E_x Mean: {props.get('E_x', {}).get('mean', '?')} GPa")
        print(f"  E_x CV: {props.get('E_x', {}).get('cv_percent', '?')}%")
        print(f"  Samples: {result['num_samples']}")
    else:
        print(f"❌ ERROR: {result.get('error')}")
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n✅ All tests completed!\n")
