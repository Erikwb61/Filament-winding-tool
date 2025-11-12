from .model import Material, ProcessPreset

# Beispiel-Materialien (Werte sind nur Platzhalter!)
M40J = Material(name="M40J", density=1800, fiber_areal_weight=145)
IM7  = Material(name="IM7", density=1790, fiber_areal_weight=190)
MR70 = Material(name="MR70", density=1800, fiber_areal_weight=135)

# Beispiel-Prozess-Presets
TOWPREG = ProcessPreset(name="Towpreg", type="Towpreg", line_speed=0.1, efficiency=0.85)
NASS    = ProcessPreset(name="Nasswickeln", type="Nass", line_speed=0.08, efficiency=0.8)
AFP     = ProcessPreset(name="AFP", type="AFP", line_speed=0.2, efficiency=0.9)

MATERIALS = {
    "M40J": M40J,
    "IM7": IM7,
    "MR70": MR70,
}

PROCESSES = {
    "Towpreg": TOWPREG,
    "Nasswickeln": NASS,
    "AFP": AFP,
}
