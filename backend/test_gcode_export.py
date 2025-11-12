"""
Test G-Code Export API
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_gcode_sample():
    """Test Sample G-Code Endpoint"""
    print("\n" + "="*70)
    print("TEST 1: Sample G-Code (GET /api/export-gcode/sample)")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/export-gcode/sample")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Sample G-Code generated successfully")
        print(f"  Lines of code: {len(data['gcode'].split(chr(10)))}")
        print("\nFirst 20 lines of G-Code:")
        print("-" * 70)
        lines = data['gcode'].split('\n')[:20]
        for line in lines:
            print(line)
        print("-" * 70)
        return True
    else:
        print(f"✗ Error: {response.text}")
        return False


def test_gcode_export():
    """Test Full G-Code Export"""
    print("\n" + "="*70)
    print("TEST 2: Full G-Code Export (POST /api/export-gcode)")
    print("="*70)
    
    payload = {
        "sequence": "[0/±45/90]s",
        "material": "M40J",
        "ply_thickness_mm": 0.125,
        "diameter_mm": 200.0,
        "length_mm": 500.0,
        "taper_angle_deg": 0.0,
        "winding_angle_deg": 45.0,
        "pitch_mm": 10.0,
        "num_turns": 5,
        "machine_type": "4-axis",
        "controller_type": "fanuc",
        "feed_rate_mm_min": 100.0
    }
    
    print(f"\nRequest Payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/export-gcode",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ G-Code export successful")
        print(f"\n  Filename: {data['filename']}")
        print(f"  Machine: {data['machine_config']['name']}")
        print(f"  Type: {data['machine_config']['type']}")
        print(f"  Controller: {data['machine_config']['controller']}")
        
        print(f"\n  Path Statistics:")
        stats = data['path_statistics']
        print(f"    - Points: {stats['num_points']}")
        print(f"    - Total Length: {stats['total_length_mm']} mm")
        print(f"    - Estimated Time: {stats['estimated_time_min']} min")
        print(f"    - Z Range: {stats['min_z_mm']} to {stats['max_z_mm']} mm")
        
        print(f"\n  Laminate Properties:")
        lam = data['laminate_properties']
        print(f"    - Sequence: {lam['sequence']}")
        print(f"    - Material: {lam['material']}")
        print(f"    - Plies: {lam['num_plies']}")
        print(f"    - Thickness: {lam['total_thickness_mm']} mm")
        print(f"    - E_x: {lam['E_x_GPa']} GPa")
        print(f"    - E_y: {lam['E_y_GPa']} GPa")
        
        if data['warnings']:
            print(f"\n  Warnings: {data['warnings']}")
        
        print(f"\nFirst 30 lines of G-Code:")
        print("-" * 70)
        lines = data['gcode'].split('\n')[:30]
        for line in lines:
            print(line)
        print("-" * 70)
        
        return True
    else:
        print(f"✗ Error: {response.text}")
        return False


def test_gcode_different_angles():
    """Test mit verschiedenen Wickelwinkeln"""
    print("\n" + "="*70)
    print("TEST 3: Different Winding Angles")
    print("="*70)
    
    angles = [0.0, 45.0, 90.0]
    
    for angle in angles:
        payload = {
            "sequence": "[0/±45/90]s",
            "material": "M40J",
            "ply_thickness_mm": 0.125,
            "diameter_mm": 150.0,
            "length_mm": 300.0,
            "winding_angle_deg": angle,
            "pitch_mm": 5.0,
            "num_turns": 3,
            "feed_rate_mm_min": 120.0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/export-gcode",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            stats = data['path_statistics']
            print(f"\n✓ Angle {angle}°:")
            print(f"  - Points: {stats['num_points']}")
            print(f"  - Total Length: {stats['total_length_mm']} mm")
            print(f"  - Time: {stats['estimated_time_min']} min")
        else:
            print(f"\n✗ Angle {angle}°: Error {response.status_code}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("G-CODE EXPORT API TEST SUITE")
    print("="*70)
    
    results = []
    
    # Test 1: Sample
    results.append(("Sample G-Code", test_gcode_sample()))
    
    # Test 2: Full Export
    results.append(("Full G-Code Export", test_gcode_export()))
    
    # Test 3: Different Angles
    test_gcode_different_angles()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    passed_count = sum(1 for _, p in results if p)
    print(f"\n{passed_count}/{len(results)} tests passed")
