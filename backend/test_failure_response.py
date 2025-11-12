import requests
import json

print("Testing Failure Analysis Response:")
payload = {
    'sequence': '[0/45/-45/90]s',
    'ply_thickness_mm': 0.125,
    'material': 'M40J',
    'N_x': 100000,
    'N_y': 0,
    'N_xy': 0
}
r = requests.post('http://localhost:5000/api/failure-analysis', json=payload)
print(f"Status: {r.status_code}")
result = r.json()
print("Response keys:", list(result.keys()))
if 'global_analysis' in result:
    print("Global Analysis keys:", list(result['global_analysis'].keys()))
    print(json.dumps(result['global_analysis'], indent=2))
if 'ply_analysis' in result:
    print(f"Ply Analysis: {len(result['ply_analysis'])} plies")
    if result['ply_analysis']:
        print("First ply:", result['ply_analysis'][0])
