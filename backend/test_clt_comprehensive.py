import requests
import json

print("=" * 60)
print("CLT API VALIDATION TESTS")
print("=" * 60)

base_url = "http://localhost:5000/api"

# Test 1: Laminate Properties
print("\n[TEST 1] Laminate Properties")
print("-" * 40)
payload = {
    'sequence': '[0/45/-45/90]s',
    'ply_thickness_mm': 0.125,
    'material': 'M40J'
}
r = requests.post(f"{base_url}/laminate-properties", json=payload)
if r.status_code == 200:
    result = r.json()
    if result.get('success'):
        props = result['effective_properties']
        print(f"✓ Status: {r.status_code}")
        print(f"  E_x: {props['E_x_GPa']} GPa")
        print(f"  E_y: {props['E_y_GPa']} GPa")
        print(f"  G_xy: {props['G_xy_GPa']} GPa")
        print(f"  Plies: {result['num_plies']}")
    else:
        print(f"✗ Error: {result.get('error')}")
else:
    print(f"✗ HTTP {r.status_code}: {r.text[:200]}")

# Test 2: Failure Analysis
print("\n[TEST 2] Failure Analysis")
print("-" * 40)
payload = {
    'sequence': '[0/45/-45/90]s',
    'ply_thickness_mm': 0.125,
    'material': 'M40J',
    'N_x': 100000,  # N/m
    'N_y': 0,
    'N_xy': 0
}
r = requests.post(f"{base_url}/failure-analysis", json=payload)
if r.status_code == 200:
    result = r.json()
    if result.get('success'):
        print(f"✓ Status: {r.status_code}")
        print(f"  Min SF: {result.get('min_safety_factor', 'N/A')}")
        print(f"  Critical Ply: {result.get('critical_ply_index', 'N/A')}")
        print(f"  Status: {result.get('status', 'N/A')}")
    else:
        print(f"✗ Error: {result.get('error')}")
else:
    print(f"✗ HTTP {r.status_code}: {r.text[:200]}")

# Test 3: Tolerance Study
print("\n[TEST 3] Tolerance Study (Monte-Carlo)")
print("-" * 40)
payload = {
    'sequence': '[0/45/-45/90]s',
    'ply_thickness_mm': 0.125,
    'material': 'M40J',
    'n_samples': 50,  # Reduced for speed
    'E_variation': 0.05  # 5% variation
}
r = requests.post(f"{base_url}/tolerance-study", json=payload)
if r.status_code == 200:
    result = r.json()
    if result.get('success'):
        print(f"✓ Status: {r.status_code}")
        stats = result.get('statistics', {})
        print(f"  E_x Mean: {stats.get('E_x_mean', 'N/A')} GPa")
        print(f"  E_x Std: {stats.get('E_x_std', 'N/A')} GPa")
        print(f"  E_y Mean: {stats.get('E_y_mean', 'N/A')} GPa")
        print(f"  E_y Std: {stats.get('E_y_std', 'N/A')} GPa")
        print(f"  Samples: {result.get('num_samples', 'N/A')}")
    else:
        print(f"✗ Error: {result.get('error')}")
else:
    print(f"✗ HTTP {r.status_code}: {r.text[:200]}")

print("\n" + "=" * 60)
print("TESTS COMPLETE")
print("=" * 60)
