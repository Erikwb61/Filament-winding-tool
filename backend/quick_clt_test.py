import requests
import json

payload = {
    'sequence': '[0/±45/90]s',
    'ply_thickness_mm': 0.125,
    'material': 'M40J'
}

r = requests.post('http://localhost:5000/api/laminate-properties', json=payload)
print(f'Status: {r.status_code}')
result = r.json()

if result.get('success'):
    print('✅ CLT Laminate Properties - SUCCESS!')
    props = result['effective_properties']
    print(f'  E_x = {props["E_x_GPa"]} GPa')
    print(f'  E_y = {props["E_y_GPa"]} GPa')
    print(f'  G_xy = {props["G_xy_GPa"]} GPa')
    print(f'  Plies = {result["num_plies"]}')
else:
    print(f'❌ ERROR: {result.get("error")}')
    if result.get('traceback'):
        print(result['traceback'][:500])
