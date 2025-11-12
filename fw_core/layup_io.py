import json
from .model import Layup

def layup_to_dict(layup: Layup) -> dict:
    return {
        "name": layup.name,
        "geometry": vars(layup.geometry) if layup.geometry else None,
        "process": vars(layup.process) if layup.process else None,
        "layers": [
            {
                "angle": l.angle,
                "thickness": l.thickness,
                "material": {
                    "name": l.material.name,
                    "density": l.material.density,
                    "fiber_areal_weight": l.material.fiber_areal_weight,
                },
            }
            for l in layup.layers
        ],
    }

def save_layup_json(layup: Layup, path: str) -> None:
    data = layup_to_dict(layup)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
