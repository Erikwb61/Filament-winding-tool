import math
from .model import Geometry, Layup

def mean_circumference(geo: Geometry) -> float:
    r_bottom = geo.d_bottom / 2
    r_top = geo.d_top / 2
    r_mean = 0.5 * (r_bottom + r_top)
    return 2 * math.pi * r_mean

def path_length_one_pass(geo: Geometry) -> float:
    alpha = math.radians(geo.winding_angle)
    return geo.height / math.cos(alpha)

def passes_per_layer(geo: Geometry) -> float:
    effective_bandwidth = geo.tow_width * geo.tow_count * (1.0 - geo.overlap)
    circumference = mean_circumference(geo)
    return circumference / effective_bandwidth

def layup_summary(layup: Layup) -> dict:
    if layup.geometry is None:
        raise ValueError("Geometrie nicht gesetzt")
    geo = layup.geometry

    path_len = path_length_one_pass(geo)
    passes = passes_per_layer(geo)
    total_passes = passes * len(layup.layers)

    speed = layup.process.line_speed if layup.process else 0.1
    time_sec = (path_len * total_passes) / speed

    circumference = mean_circumference(geo)
    area = circumference * geo.height
    mass = 0.0
    for layer in layup.layers:
        areal = layer.material.fiber_areal_weight / 1000.0  # g/m² → kg/m²
        mass += areal * area

    return {
        "umfang_m": circumference,
        "pfadlaenge_m": path_len,
        "durchlaeufe": total_passes,
        "zeit_s": time_sec,
        "masse_kg": mass,
    }
