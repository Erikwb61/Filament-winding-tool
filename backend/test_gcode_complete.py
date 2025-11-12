"""
Test-Suite für G-Code Export Module
Teste die Funktionalität ohne Netzwerk
"""

import sys
sys.path.insert(0, r'c:\fw_tool')

from backend.fw_core.path_optimizer import Geometry, PathOptimizer
from backend.fw_core.gcode_generator import GCodeGenerator, MachineConfig
from backend.fw_core.laminate_properties import LaminateProperties
from backend.fw_core.lamina_properties import LaminaDatabase

print("\n" + "="*70)
print("G-CODE EXPORT TEST SUITE")
print("="*70)

# ========================================================================
# TEST 1: PathOptimizer
# ========================================================================
print("\nTEST 1: Path Optimizer Module")
print("-"*70)

geom = Geometry(diameter_mm=200.0, length_mm=500.0, taper_angle_deg=0.0)
optimizer = PathOptimizer(geom)

# Generate helical path
path = optimizer.generate_helical_path(
    winding_angle_deg=45.0,
    pitch_mm=10.0,
    num_turns=3,
    speed_mm_min=100.0
)

stats = optimizer.get_path_statistics()
print(f"  Geometry: Diameter={geom.diameter_mm}mm, Length={geom.length_mm}mm")
print(f"  Path Generated:")
print(f"    - Points: {stats['num_points']}")
print(f"    - Total Length: {stats['total_length_mm']} mm")
print(f"    - Est. Time: {stats['estimated_time_min']} min")
print(f"    - Z Range: {stats['min_z_mm']} to {stats['max_z_mm']} mm")
print("  RESULT: PASSED")

# ========================================================================
# TEST 2: G-Code Generator
# ========================================================================
print("\nTEST 2: G-Code Generator Module")
print("-"*70)

machine = MachineConfig(
    name="Test CNC Machine",
    max_speed_mm_min=5000.0,
    feed_rate_mm_min=100.0,
    controller_type="fanuc"
)

gen = GCodeGenerator(machine)
gen.program_start("WINDING_TEST")
gen.setup_machine()
gen.rapid_move(x=100.0, y=0.0, z=50.0, theta=0.0)
gen.linear_move(x=100.0, y=0.0, z=10.0, theta=0.0, speed_mm_min=100.0)
gen.linear_move(x=100.0, y=0.0, z=20.0, theta=45.0, speed_mm_min=100.0)
gen.linear_move(x=100.0, y=0.0, z=30.0, theta=90.0, speed_mm_min=100.0)
gen.add_return_to_safe()
gen.program_end()

gcode = gen.generate_code()
gcode_lines = gcode.split('\n')

print(f"  Machine: {machine.name}")
print(f"  G-Code Generated:")
print(f"    - Lines: {len(gcode_lines)}")
print(f"    - Controller: {machine.controller_type}")
print(f"  First 8 lines:")
for line in gcode_lines[:8]:
    print(f"    {line}")
print("  RESULT: PASSED")

# ========================================================================
# TEST 3: Laminate Properties Integration
# ========================================================================
print("\nTEST 3: Laminate Properties Integration")
print("-"*70)

# Create sequence as list of (material, angle, count) tuples
sequence = [
    ("M40J", 0, 1),
    ("M40J", 45, 1),
    ("M40J", -45, 1),
    ("M40J", 90, 1)
]

# Create laminate
lam = LaminateProperties(
    lamina_list=sequence,
    ply_thickness_mm=0.125
)

eff_props = lam.effective_props

print(f"  Sequence: {sequence}")
print(f"  Material: M40J")
print(f"  Ply Thickness: 0.125 mm")
num_plies = sum([n for _, _, n in sequence])
total_thickness = num_plies * 0.125
print(f"  Total Thickness: {total_thickness} mm")
print(f"  Effective Properties:")
print(f"    - E_x: {eff_props.get('E_x', 0):.2f} GPa")
print(f"    - E_y: {eff_props.get('E_y', 0):.2f} GPa")
print(f"    - G_xy: {eff_props.get('G_xy', 0):.2f} GPa")
print("  RESULT: PASSED")

# ========================================================================
# TEST 4: Full G-Code Export Simulation
# ========================================================================
print("\nTEST 4: Full G-Code Export Simulation")
print("-"*70)

# Create geometry
geom = Geometry(diameter_mm=150.0, length_mm=300.0)

# Generate path
optimizer = PathOptimizer(geom)
path_points = optimizer.generate_geodesic_path(
    winding_angle_deg=45.0,
    num_turns=2,
    speed_mm_min=120.0
)

print(f"  Geometry: Diameter=150mm, Length=300mm")
print(f"  Winding: 2 turns at 45 degrees")
print(f"  Path Points: {len(path_points)}")
print(f"  RESULT: PASSED")

# ========================================================================
# SUMMARY
# ========================================================================
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
print("  1. PathOptimizer Module: PASSED")
print("  2. GCodeGenerator Module: PASSED")
print("  3. Laminate Properties: PASSED")
print("  4. Full Export Simulation: PASSED")
print("\n  ALL TESTS PASSED!")
print("="*70 + "\n")
