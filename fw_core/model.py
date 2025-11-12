from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Material:
    name: str
    density: float          # kg/m³
    fiber_areal_weight: float  # g/m²
    e_modulus: Optional[float] = None
    notes: str = ""

@dataclass
class ProcessPreset:
    name: str
    type: str               # "Towpreg", "Nass", "AFP", ...
    line_speed: float       # m/s
    efficiency: float       # 0..1
    notes: str = ""

@dataclass
class Layer:
    angle: float            # Grad
    thickness: float        # m
    material: Material

@dataclass
class Geometry:
    d_bottom: float         # m
    d_top: float            # m
    height: float           # m
    winding_angle: float    # Grad
    tow_width: float        # m
    tow_count: int
    overlap: float          # 0..1

@dataclass
class Layup:
    name: str
    layers: List[Layer] = field(default_factory=list)
    geometry: Optional[Geometry] = None
    process: Optional[ProcessPreset] = None
