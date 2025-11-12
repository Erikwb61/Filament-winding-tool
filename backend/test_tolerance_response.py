import requests
import json

print("Testing Tolerance Study Response:")
payload = {
    'sequence': '[0/45/-45/90]s',
    'ply_thickness_mm': 0.125,
    'material': 'M40J',
    'num_samples': 100,
    'N_x': 100000
}
r = requests.post('http://localhost:5000/api/tolerance-study', json=payload)
print(f"Status: {r.status_code}")
result = r.json()
print("Response keys:", list(result.keys()))
print(json.dumps(result, indent=2))
