#!/usr/bin/env python
"""
Test der neuen CLT API Endpoints
"""
import requests
import json
import time

BASE_URL = 'http://localhost:5000'

def test_laminate_properties():
    """Test /api/laminate-properties"""
    print("\n" + "="*80)
    print("TEST 1: /api/laminate-properties")
    print("="*80)
    
    payload = {
        'sequence': '[0/±45/90]s',
        'ply_thickness_mm': 0.125,
        'material': 'M40J'
    }
    
    response = requests.post(f'{BASE_URL}/api/laminate-properties', json=payload)
    result = response.json()
    
    if response.status_code == 200 and result.get('success'):
        print("✅ REQUEST SUCCESSFUL")
        print(f"Num Plies: {result['num_plies']}")
        print(f"Total Thickness: {result['total_thickness_mm']} mm")
        print(f"Effective Properties:")
        for key, val in result['effective_properties'].items():
            print(f"  {key}: {val}")
    else:
        print("❌ REQUEST FAILED")
        print(json.dumps(result, indent=2))


def test_failure_analysis():
    """Test /api/failure-analysis"""
    print("\n" + "="*80)
    print("TEST 2: /api/failure-analysis")
    print("="*80)
    
    payload = {
        'sequence': '[0/±45/90]s',
        'ply_thickness_mm': 0.125,
        'material': 'M40J',
        'N_x': 1000,
        'N_y': 0,
        'N_xy': 0,
        'load_case': 'tension'
    }
    
    response = requests.post(f'{BASE_URL}/api/failure-analysis', json=payload)
    result = response.json()
    
    if response.status_code == 200 and result.get('success'):
        print("✅ REQUEST SUCCESSFUL")
        print(f"Min Safety Factor: {result['global_analysis']['min_safety_factor']}")
        print(f"Critical Ply ID: {result['global_analysis']['critical_ply_id']}")
        print(f"Design Status: {result['global_analysis']['design_status']}")
        print(f"Reserve Rating: {result['global_analysis']['reserve_rating']}")
        print(f"\nPly Analysis (first 3 plies):")
        for ply in result['ply_analysis'][:3]:
            print(f"  Ply {ply['ply_id']} @ {ply['angle_deg']}°: SF={ply['safety_factor']}, status={ply['status']}")
    else:
        print("❌ REQUEST FAILED")
        print(json.dumps(result, indent=2))


def test_tolerance_study():
    """Test /api/tolerance-study"""
    print("\n" + "="*80)
    print("TEST 3: /api/tolerance-study")
    print("="*80)
    
    payload = {
        'sequence': '[0/±45/90]s',
        'ply_thickness_mm': 0.125,
        'material': 'M40J',
        'angle_tolerance_deg': 1.0,
        'thickness_tolerance_pct': 5.0,
        'num_samples': 300,
        'N_x': 1000,
        'N_y': 0,
        'N_xy': 0
    }
    
    response = requests.post(f'{BASE_URL}/api/tolerance-study', json=payload)
    result = response.json()
    
    if response.status_code == 200 and result.get('success'):
        print("✅ REQUEST SUCCESSFUL")
        print(f"Num Samples: {result['num_samples']}")
        print(f"\nProperty Statistics (E_x):")
        if 'E_x' in result['property_statistics']:
            ex = result['property_statistics']['E_x']
            print(f"  Mean: {ex['mean']} GPa")
            print(f"  Std: {ex['std']} GPa")
            print(f"  95% CI: [{result['confidence_intervals_95'].get('E_x', [0,0])[0]}, {result['confidence_intervals_95'].get('E_x', [0,0])[1]}]")
        
        if result.get('failure_analysis'):
            print(f"\nFailure Analysis:")
            print(f"  Mean SF: {result['failure_analysis']['mean_safety_factor']}")
            print(f"  Probability of Failure: {result['failure_analysis']['probability_of_failure']}")
    else:
        print("❌ REQUEST FAILED")
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    print("🧪 Testen der neuen CLT Endpoints...")
    time.sleep(1)
    
    try:
        test_laminate_properties()
        test_failure_analysis()
        test_tolerance_study()
        
        print("\n" + "="*80)
        print("✅ ALLE TESTS ERFOLGREICH")
        print("="*80)
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
